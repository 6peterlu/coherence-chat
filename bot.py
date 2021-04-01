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
import pytz

import logging
from constants import ABSENT_MSG, BOUNDARY_MSG, CONFIRMATION_MSG, DAILY_MSG, ERROR_MSG, FOLLOWUP_MSG, NO_DOSE_MSG, REMINDER_TOO_CLOSE_MSG, REMINDER_TOO_LATE_MSG, SKIP_MSG, TAKE_MSG, UNKNOWN_MSG

# allow no reminders to be set within 10 mins of boundary
BUFFER_TIME_MINS = 10
USER_TIMEZONE = "US/Pacific"

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

class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dose_id = db.Column(db.Integer)
    send_time = db.Column(db.DateTime, nullable=False)
    reminder_type = db.Column(db.String(10), nullable=False)  # using string for readability

    def __repr__(self):
        return f"<Reminder {id}>"
    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

# initialize tables
db.create_all()  # are there bad effects from running this every time? edit: I guess not

# twilio objects
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)


# initialize scheduler
scheduler = APScheduler()
# if you don't wanna use a config, you can set options here:
# scheduler.api_enabled = True
# interval example
# misfire grace time: the length of time a job can be late before it's cancelled
# @scheduler.task('interval', id='do_job_1', seconds=3, misfire_grace_time=900)
def job1():
    print('Job 1 executed')

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
    alarm_starttime = datetime.now().replace(hour=start_hour, minute=start_minute, second=0, microsecond=0)
    alarm_endtime = datetime.now().replace(hour=end_hour, minute=end_minute, second=0, microsecond=0)
    if alarm_starttime < datetime.now():
        alarm_starttime += timedelta(days=1)
        alarm_endtime += timedelta(days=1)
    # protect end time > start time invariant across am/pm
    if alarm_endtime < alarm_starttime:
        alarm_endtime += timedelta(days=1)
    scheduler.add_job(f"{new_dose_record.id}-initial", send_intro_text,
        trigger="interval",
        start_date=alarm_starttime,
        days=1,
        args=[phone_number, alarm_starttime, alarm_endtime, new_dose_record.id]
    )

    return jsonify()

@app.route("/dose", methods=["DELETE"])
def delete_dose():
    print("deleting dose")
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Dose.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

@app.route("/reminder", methods=["DELETE"])
def delete_reminder():
    print("deleting reminder")
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
        "reminders": [reminder.as_dict() for reminder in all_reminders]
    })

@app.route('/bot', methods=['POST'])
def bot():
    print("received incoming POST")
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
        latest_dose_record = list(filter(lambda d: d.id == latest_dose_id, doses))[0]
        if exists_remaining_reminder_job(latest_dose_id, ["boundary"]):
            if incoming_msg in ["1", "2", "3"]:
                message_delays = {
                        "1": timedelta(minutes=10),
                        "2": timedelta(minutes=30),
                        "3": timedelta(hours=1)
                    }
                remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                boundary_job = scheduler.get_job(f"{latest_dose_id}-boundary")
                dose_end_time = boundary_job.next_run_time.replace(tzinfo=None)  # make naive
                print(dose_end_time)
                next_alarm_time = datetime.now() + message_delays[incoming_msg]  # timezone unaware?
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
                        from_='+12813771848',
                        to=incoming_phone_number
                    )
                    scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                        args=[incoming_phone_number, latest_dose_id, dose_end_time],
                        trigger="date",
                        run_date=next_alarm_time
                    )
                else:
                    client.messages.create(
                        body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                        from_='+12813771848',
                        to=incoming_phone_number
                    )
            elif incoming_msg in ["t", "s"]:
                message_copy = {
                    "t": TAKE_MSG,
                    "s": SKIP_MSG
                }
                client.messages.create(
                    body=message_copy[incoming_msg],
                    from_='+12813771848',
                    to=incoming_phone_number
                )
                remove_jobs_helper(latest_dose_id, ["absent", "followup", "boundary"])
            else:
                client.messages.create(
                    body=ERROR_MSG,
                    from_='+12813771848',
                    to=incoming_phone_number
                )
        else:
            client.messages.create(
                body=NO_DOSE_MSG,
                from_='+12813771848',
                to=incoming_phone_number
            )
    else:
        client.messages.create(
            body=UNKNOWN_MSG,
            from_='+12813771848',
            to=incoming_phone_number
        )
    return jsonify()
scheduler.init_app(app)
scheduler.start()

def maybe_schedule_absent(phone_number, dose_id, end_date):
    # schedule absent text in an hour or ten mins before boundary
    desired_absent_reminder = min(datetime.now() + timedelta(hours=1), end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > datetime.now():
        scheduler.add_job(f"{dose_id}-absent", send_absent_text,
            args=[phone_number, dose_id],
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

def send_followup_text(phone_number, dose_id, end_date):
    client.messages.create(
        body=FOLLOWUP_MSG,
        from_='+12813771848',
        to=phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="followup")
    db.session.add(reminder_record)
    db.session.commit()
    # remove absent jobs, if exist
    remove_jobs_helper(dose_id, ["absent", "followup"])
    maybe_schedule_absent(phone_number, dose_id, end_date)

def send_absent_text(phone_number, dose_id):
    client.messages.create(
        body=ABSENT_MSG,
        from_='+12813771848',
        to=phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="absent")
    db.session.add(reminder_record)
    db.session.commit()

def send_boundary_text(phone_number, dose_id):
    if exists_remaining_reminder_job(dose_id, ["followup"]):
        # if there's a later followup, don't send the boundary text
        return
    client.messages.create(
        body=BOUNDARY_MSG,
        from_='+12813771848',
        to=phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="boundary")
    db.session.add(reminder_record)
    db.session.commit()

def send_intro_text(phone_number, start_date, end_date, dose_id):
    client.messages.create(
        body=DAILY_MSG.substitute(time=start_date.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
        from_='+12813771848',
        to=phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=datetime.now(), reminder_type="initial")
    db.session.add(reminder_record)
    db.session.commit()
    maybe_schedule_absent(phone_number, dose_id, end_date)
    scheduler.add_job(f"{dose_id}-boundary", send_boundary_text,
        args=[phone_number, dose_id],
        trigger="date",
        run_date=end_date
    )

if __name__ == '__main__':
    app.run(host='0.0.0.0')