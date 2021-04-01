from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
# import Flask-APScheduler
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os
# import requests
# from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from datetime import datetime, timedelta
from pytz import timezone

import logging
from constants import ABSENT_MSG, BOUNDARY_MSG, CONFIRMATION_MSG, DAILY_MSG, ERROR_MSG, FOLLOWUP_MSG, MANUAL_TEXT_NEEDED_MSG, NO_DOSE_MSG, REMINDER_TOO_CLOSE_MSG, REMINDER_TOO_LATE_MSG, SKIP_MSG, TAKE_MSG, UNKNOWN_MSG

# allow no reminders to be set within 10 mins of boundary
BUFFER_TIME_MINS = 10
USER_TIMEZONE = "US/Pacific"
TWILIO_PHONE_NUMBERS = {
    "local": "2813771848",
    "production": "2673824152"
}

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

# set configuration values
class Config(object):
    SCHEDULER_API_ENABLED = True
    SCHEDULER_JOBSTORES = {
        'default': SQLAlchemyJobStore(
            url=os.environ['SQLALCHEMY_DATABASE_URI'],
            tablename='apscheduler_jobs'
        )
    }
    SQLALCHEMY_DATABASE_URI = os.environ['SQLALCHEMY_DATABASE_URI']
    SQLALCHEMY_TRACK_MODIFICATIONS = False

# create app
app = Flask(__name__)
app.config.from_object(Config())
CORS(app)

# sqlalchemy db
db = SQLAlchemy(app)

# sqlalchemy models & deserializers
class Dose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    start_minute = db.Column(db.Integer, nullable=False)
    end_minute = db.Column(db.Integer, nullable=False)
    patient_name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(13), nullable=False)  # +11234567890
    medication_name = db.Column(db.String(80), nullable=True)

    # TODO: extend this repr to include all fields
    def __repr__(self):
        return '<Dose %r>' % self.patient_name

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

    @property
    def next_start_date(self):
        alarm_starttime = datetime.now().replace(hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0)
        if alarm_starttime < datetime.now():
            alarm_starttime += timedelta(days=1)
        return alarm_starttime
    @property
    def next_end_date(self):
        alarm_endtime = datetime.now().replace(hour=self.end_hour, minute=self.end_minute, second=0, microsecond=0)
        if alarm_endtime < datetime.now():
            alarm_endtime += timedelta(days=1)
        if alarm_endtime < self.next_start_date:
            alarm_endtime += timedelta(days=1)
        return alarm_endtime

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dose_id = db.Column(db.Integer)
    send_time = db.Column(db.DateTime, nullable=False)
    reminder_type = db.Column(db.String(10), nullable=False)  # using string for readability

    def __repr__(self):
        return f"<Reminder {id}>"
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Online(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    online = db.Column(db.Boolean)
    def __repr__(self):
        return f"<Online {id} online={online}>"

# initialize tables
db.create_all()  # are there bad effects from running this every time? edit: I guess not

# twilio objects
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# initialize scheduler
scheduler = APScheduler()

# add a dose
@app.route("/dose", methods=["POST"])
def add_dose():
    incoming_data = request.json
    start_hour = incoming_data["startHour"]
    start_minute = incoming_data["startMinute"]
    end_hour = incoming_data["endHour"]
    end_minute = incoming_data["endMinute"]
    raw_phone_number = incoming_data["phoneNumber"]
    phone_number = f"+1{raw_phone_number}"
    patient_name = incoming_data["patientName"]
    medication_name = incoming_data.get("medicationName", None)
    new_dose_record = Dose(
        start_hour=start_hour,
        start_minute=start_minute,
        end_hour=end_hour,
        end_minute=end_minute,
        phone_number=phone_number,
        patient_name=patient_name,
        medication_name=medication_name
    )
    db.session.add(new_dose_record)
    db.session.commit()
    scheduler.add_job(f"{new_dose_record.id}-initial", send_intro_text,
        trigger="interval",
        start_date=new_dose_record.next_start_date,
        days=1,
        args=[new_dose_record.id]
    )

    return jsonify()

@app.route("/dose", methods=["DELETE"])
def delete_dose():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Dose.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

@app.route("/reminder", methods=["DELETE"])
def delete_reminder():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Reminder.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

@app.route("/everything", methods=["GET"])
def get_everything():
    all_doses = Dose.query.all()
    all_reminders = Reminder.query.all()
    return jsonify({
        "doses": [dose.as_dict() for dose in all_doses],
        "reminders": [reminder.as_dict() for reminder in all_reminders],
        "onlineStatus": get_online_status()
    })

@app.route("/messages", methods=["GET"])
def get_messages_for_number():
    # only get messages in the past week.
    query_phone_number = request.args.get("phoneNumber")
    date_limit = datetime.now() - timedelta(days=3)
    truncated_date_limit = date_limit.replace(hour=0, minute=0, second=0, microsecond=0, tzinfo=None)
    sent_messages_list = client.messages.list(
        date_sent_after=truncated_date_limit,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+1{query_phone_number}"
    )
    received_messages_list = client.messages.list(
        date_sent_after=truncated_date_limit,
        to=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        from_=f"+1{query_phone_number}"
    )
    combined_list = sorted(sent_messages_list + received_messages_list, key= lambda msg: msg.date_sent, reverse=True)
    json_blob = [
        {
            "sender": "us" if message.from_ == f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}" else "them",
            "body": message.body,
            "date_sent": message.date_sent.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
        }
        for message in combined_list
    ]
    return jsonify(json_blob)

@app.route("/online", methods=["POST"])
def online_toggle():
    online_status = get_online_status()
    online_record = Online.query.get(1)
    online_record.online = not online_status
    db.session.commit()
    return jsonify()

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg = request.values.get('Body', '').lower()
    incoming_phone_number = request.values.get('From', None)
    if incoming_msg in ['1', '2', '3', 't', 's']:
        doses = Dose.query.filter_by(phone_number=f"+1{incoming_phone_number[1:]}").all()
        dose_ids = [dose.id for dose in doses]
        latest_reminder_record = Reminder.query \
            .filter(Reminder.dose_id.in_(dose_ids)) \
            .order_by(Reminder.send_time.desc()) \
            .first()
        latest_dose_id = latest_reminder_record.dose_id
        if exists_remaining_reminder_job(latest_dose_id, ["boundary"]):
            if incoming_msg in ["1", "2", "3"]:
                message_delays = {
                        "1": timedelta(minutes=10),
                        "2": timedelta(minutes=30),
                        "3": timedelta(hours=1)
                    }
                remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                dose_end_time = get_current_end_date(latest_dose_id)
                next_alarm_time = datetime.now() + message_delays[incoming_msg]
                too_close = False
                if next_alarm_time > dose_end_time - timedelta(minutes=1):
                    next_alarm_time = dose_end_time - timedelta(minutes=1)
                    too_close = True
                if next_alarm_time > datetime.now():
                    client.messages.create(
                        body= REMINDER_TOO_CLOSE_MSG.substitute(
                            time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                            reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                        ),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
                    scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                        args=[latest_dose_id],
                        trigger="date",
                        run_date=next_alarm_time
                    )
                else:
                    client.messages.create(
                        body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
            elif incoming_msg in ["t", "s"]:
                message_copy = {
                    "t": TAKE_MSG,
                    "s": SKIP_MSG
                }
                client.messages.create(
                    body=message_copy[incoming_msg],
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=incoming_phone_number
                )
                remove_jobs_helper(latest_dose_id, ["absent", "followup", "boundary"])
            else:
                client.messages.create(
                    body=ERROR_MSG,
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=incoming_phone_number
                )
        else:
            client.messages.create(
                body=NO_DOSE_MSG,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
    else:
        if get_online_status():
            # if we're online, don't send the unknown text and let us respond.
            client.messages.create(
                body=MANUAL_TEXT_NEEDED_MSG.substitute(number=incoming_phone_number),
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to="+13604508655"  # admin phone #
            )
        else:
            client.messages.create(
                body=UNKNOWN_MSG,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
    return jsonify()
scheduler.init_app(app)
scheduler.start()


@app.route("/manual", methods=["POST"])
def manual_send():
    incoming_data = request.json
    dose_id = int(incoming_data["doseId"])
    reminder_type = incoming_data["reminderType"]
    if reminder_type == "absent":
        send_absent_text(dose_id)
    elif reminder_type == "followup":
        send_followup_text(dose_id)
    return jsonify()

@app.route("/manual/text", methods=["POST"])
def manual_send_text():
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    text = incoming_data["text"]
    client.messages.create(
        body=text,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+1{target_phone_number}"
    )
    return jsonify()

def get_online_status():
    online_record = Online.query.filter_by(id=1).one_or_none()
    if online_record is None:
        online_record = Online(online=False)
        db.session.add(online_record)
        db.session.commit()
    return online_record.online

def maybe_schedule_absent(dose_id):
    end_date = get_current_end_date(dose_id)
    # schedule absent text in an hour or ten mins before boundary
    desired_absent_reminder = datetime.now() + timedelta(hours=1)
    if end_date is not None:  # if it's none, there's no boundary set up
        desired_absent_reminder = min(datetime.now() + timedelta(hours=1), end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > datetime.now():
        scheduler.add_job(f"{dose_id}-absent", send_absent_text,
            args=[dose_id],
            trigger="date",
            run_date=desired_absent_reminder
        )

def remove_jobs_helper(dose_id, jobs_list):
    for job in jobs_list:
        if scheduler.get_job(f"{dose_id}-{job}"):
            scheduler.remove_job(f"{dose_id}-{job}")

def exists_remaining_reminder_job(dose_id, job_list):
    for job in job_list:
        if scheduler.get_job(f"{dose_id}-{job}"):
            return True
    return False

def get_current_end_date(dose_id):
    scheduled_job = scheduler.get_job(f"{dose_id}-boundary")
    if scheduled_job is None:
        return None
    current_end_date = scheduled_job.next_run_time.replace(tzinfo=None)
    return current_end_date

def send_followup_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=FOLLOWUP_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="followup")
    db.session.add(reminder_record)
    db.session.commit()
    # remove absent jobs, if exist
    remove_jobs_helper(dose_id, ["absent", "followup"])
    maybe_schedule_absent(dose_id)

def send_absent_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=ABSENT_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="absent")
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_id, ["absent", "followup"])

def send_boundary_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=BOUNDARY_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="boundary")
    db.session.add(reminder_record)
    db.session.commit()
    # this shouldn't be needed, but followups sent manually leave absent artifacts
    remove_jobs_helper(dose_id, ["absent", "followup"])

def send_intro_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=DAILY_MSG.substitute(time=dose_obj.next_start_date.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="initial")
    db.session.add(reminder_record)
    db.session.commit()
    maybe_schedule_absent(dose_id)
    scheduler.add_job(f"{dose_id}-boundary", send_boundary_text,
        args=[dose_id],
        trigger="date",
        run_date=dose_obj.next_end_date - timedelta(days=1)  # HACK, assumes this executes after start_date
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0')