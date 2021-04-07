from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
# import Flask-APScheduler
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os
# from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from datetime import datetime, timedelta
from pytz import timezone, utc as pytzutc
import parsedatetime
import random
import string

# fuzzy nlp handling
import spacy

nlp = spacy.load("en_core_web_sm")

TOKENS_TO_RECOGNIZE = [
    "dinner",
    "breakfast",
    "lunch",
    "bathroom",
    "reading",
    "eating",
    "out",
    "call",
    "on a call",
    "meeting",
    "walking",
    "going for a walk",
    "busy",
    "thanks",
    "help",
    "ok",
    "great",
    "no problem",
    "hello",
    "confused",
    "run",
    "running",
    "sleeping",
    "out to dinner",
    "out to lunch",
    "out to breakfast",
    "out to brunch",
    "brunch",
    "later",
    "golf",
    "tennis",
    "swimming",
    "basketball",
    "watching tv"
]

# load on server start
SPACY_EMBED_MAP = {token: nlp(token) for token in TOKENS_TO_RECOGNIZE}

import logging
from constants import (
    ABSENT_MSG,
    BOUNDARY_MSG,
    CLINICAL_BOUNDARY_MSG,
    CONFIRMATION_MSG,
    INITIAL_MSGS,
    ERROR_MSG,
    FOLLOWUP_MSGS,
    MANUAL_TEXT_NEEDED_MSG,
    NO_DOSE_MSG,
    REMINDER_TOO_CLOSE_MSG,
    REMINDER_TOO_LATE_MSG,
    SKIP_MSG,
    TAKE_MSG,
    UNKNOWN_MSG,
    ACTION_MENU
)

# allow no reminders to be set within 10 mins of boundary
BUFFER_TIME_MINS = 10
USER_TIMEZONE = "US/Pacific"
TWILIO_PHONE_NUMBERS = {
    "local": "2813771848",
    "production": "2673824152"
}

# numbers for which the person should NOT take it after the dose period.
CLINICAL_BOUNDARY_PHONE_NUMBERS = ["8587761377"]

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

# parse datetime calendar object
cal = parsedatetime.Calendar()

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
        alarm_starttime = get_time_now().replace(hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0)
        if alarm_starttime < get_time_now():
            alarm_starttime += timedelta(days=1)
        return alarm_starttime
    @property
    def next_end_date(self):
        alarm_endtime = get_time_now().replace(hour=self.end_hour, minute=self.end_minute, second=0, microsecond=0)
        if alarm_endtime < get_time_now():
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
       return_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       return_dict["send_time"] = self.send_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
       return return_dict

class Online(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    online = db.Column(db.Boolean)
    def __repr__(self):
        return f"<Online {id}>"

class Concept(db.Model):
    name = db.Column(db.String, primary_key=True)  # must be unique
    time_range_start = db.Column(db.Integer)  # in minutes
    time_range_end = db.Column(db.Integer)  # in minutes

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    phone_number = db.Column(db.String(13), nullable=False)
    description = db.Column(db.String)

    def as_dict(self):
       return_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       return_dict["event_time"] = self.event_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
       return return_dict

class ManualTakeover(db.Model):
    phone_number = db.Column(db.String(13), primary_key=True)


# initialize tables
db.create_all()  # are there bad effects from running this every time? edit: I guess not

# twilio objects
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# initialize scheduler
scheduler = APScheduler()
scheduler.init_app(app)
scheduler.start()

# not calling this with false anywhere
def get_time_now(tzaware=True):
    return datetime.now(pytzutc) if tzaware else datetime.utcnow()

# message helpers
def get_followup_message():
    return random.choice(FOLLOWUP_MSGS)

def get_initial_message():
    return random.choice(INITIAL_MSGS)  # returns a template

def get_take_message():
    datestring = get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%b %d, %I:%M %p')
    return TAKE_MSG.substitute(time=datestring)


def log_event(event_type, phone_number, event_time=None, description=None):
    if event_time is None:
        event_time = get_time_now()  # done at runtime for accurate timing
    new_event = Event(event_type=event_type, phone_number=phone_number, event_time=event_time, description=description)
    db.session.add(new_event)
    db.session.commit()

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
    id_to_delete = int(incoming_data["id"])
    remove_jobs_helper(id_to_delete, ["boundary", "initial", "followup", "absent"])
    Dose.query.filter_by(id=id_to_delete).delete()
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
    all_reminders = Reminder.query.order_by(Reminder.send_time.desc()).all()
    all_takeover = ManualTakeover.query.all()
    # all_concepts = Concept.query.all()
    return jsonify({
        "doses": [dose.as_dict() for dose in all_doses],
        "reminders": [reminder.as_dict() for reminder in all_reminders],
        # "concepts": [concept.as_dict() for concept in all_concepts],
        "onlineStatus": get_online_status(),
        "manualTakeover": [mt.phone_number for mt in all_takeover]
    })

@app.route("/events", methods=["GET"])
def get_events_for_number():
    query_phone_number = request.args.get("phoneNumber")
    query_days = int(request.args.get("days"))
    earliest_date = get_time_now() - timedelta(days=query_days)
    matching_events = Event.query.filter(
            Event.event_time > earliest_date, Event.phone_number == f"+11{query_phone_number}"
        ).order_by(Event.event_time.desc()).all()
    return jsonify({
        "events": [event.as_dict() for event in matching_events]
    })

@app.route("/events", methods=["DELETE"])
def delete_event():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Event.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

@app.route("/events", methods=["POST"])
def post_event():
    incoming_data = request.json
    phone_number = f"+11{incoming_data['phoneNumber']}"
    event_type = incoming_data["eventType"]
    log_event(event_type=event_type, phone_number=phone_number)
    return jsonify()

@app.route("/messages", methods=["GET"])
def get_messages_for_number():
    # only get messages in the past week.
    query_phone_number = request.args.get("phoneNumber")
    query_days = int(request.args.get("days"))
    date_limit = get_time_now() - timedelta(days=query_days)
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
            "date_sent": message.date_sent.astimezone(timezone(USER_TIMEZONE)).strftime("%b %d, %I:%M%p")
        }
        for message in combined_list
    ]
    return jsonify(json_blob)

@app.route("/online", methods=["POST"])
def online_toggle():
    online_status = get_online_status()
    if online_status:  # is online, we need to clear manual takeover on going offline
        ManualTakeover.query.delete()
    online_record = Online.query.get(1)
    online_record.online = not online_status
    db.session.commit()
    return jsonify()

def activity_detection(message_str):
    # not deferring for now because that actually seems worse
    # if the string contains any numbers or timestrings, defer to the datetime parser
    # time_strings = ["hr", "min", "hour", "minute", "mins"]
    # if any(map(str.isdigit, message_str)) or any(map(lambda x: x in message_str, time_strings)):
    #     return None
    computing_prefix = "Computing ideal reminder time...done."
    time_delay = timedelta(minutes=random.randint(30,60))
    direct_time_mapped_strings = {
        "brunch": (time_delay, f"{computing_prefix} Have a great brunch! We'll check in later."),
        "out to brunch": (time_delay, f"{computing_prefix} Have a great brunch! We'll check in later."),
        "dinner": (time_delay, f"{computing_prefix} Have a great dinner! We'll check in later."),
        "out to dinner": (time_delay, f"{computing_prefix} Have a great dinner! We'll check in later."),
        "lunch": (time_delay, f"{computing_prefix} Have a great lunch! We'll check in later."),
        "out to lunch": (time_delay, f"{computing_prefix} Have a great lunch! We'll check in later."),
        "breakfast": (time_delay, f"{computing_prefix} Have a great breakfast! We'll check in later."),
        "out to breakfast": (time_delay, f"{computing_prefix} Have a great breakfast! We'll check in later."),
        "walking": (time_delay, f"{computing_prefix} Enjoy your walk! We'll check in later."),
        "going for a walk": (time_delay, f"{computing_prefix} Enjoy your walk! We'll check in later."),
        "eating": (time_delay, f"{computing_prefix} Enjoy your meal! We'll check in later."),
        "meeting": (time_delay, f"{computing_prefix} Have a productive meeting! We'll check in later."),
        "call": (time_delay, f"{computing_prefix} Have a great call! We'll check in later."),
        "on a call": (time_delay, f"{computing_prefix} Have a great call! We'll check in later."),
        "out": (time_delay, f"{computing_prefix} No problem, we'll check in later."),
        "busy": (time_delay, f"{computing_prefix} No problem, we'll check in later."),
        "later": (time_delay, f"{computing_prefix} No problem, we'll check in later."),
        "bathroom": (time_delay, f"{computing_prefix} No problem, we'll check in in a bit."),
        "reading": (time_delay, f"{computing_prefix} Enjoy your book, we'll check in later."),
        "run": (time_delay, f"{computing_prefix} Have a great run! We'll see you later."),
        "running": (time_delay, f"{computing_prefix} Have a great run! We'll see you later."),
        "sleeping": (time_delay, f"{computing_prefix} Sleep well! We'll see you later."),
        "golf": (time_delay, f"{computing_prefix} Have fun out there! We'll see you later."),
        "tennis": (time_delay, f"{computing_prefix} Have fun out there! We'll see you later."),
        "swimming": (time_delay, f"{computing_prefix} Have fun out there! We'll see you later."),
        "basketball": (time_delay, f"{computing_prefix} Have fun out there! We'll see you later."),
        "watching tv": (time_delay, f"{computing_prefix} Have fun, we'll check in later."),
    }
    best_match_score = 0.0
    best_match_concept = None
    for concept in direct_time_mapped_strings:
        match_score = nlp(message_str).similarity(SPACY_EMBED_MAP[concept])
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_concept = concept
    if best_match_score > 0.75:
        return direct_time_mapped_strings[best_match_concept]
    return None

def canned_responses(message_str):
    hardcoded_responses = {
        "x": "Thanks for reporting. We've noted the error and are working on it."
    }
    if message_str in hardcoded_responses:
        return hardcoded_responses[message_str]
    responses = {
        "thanks": "No problem, glad to help.",
        "help": UNKNOWN_MSG,
        "confused": UNKNOWN_MSG,
        "ok": "👍",
        "great": "👍",
        "no problem": "👍",
        "hello": "Hello! 👋"
    }
    best_match_score = 0.0
    best_match_concept = None
    for concept in responses:
        match_score = nlp(message_str).similarity(SPACY_EMBED_MAP[concept])
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_concept = concept
    if best_match_score > 0.7:
        return responses[best_match_concept]
    return None


def should_force_manual(phone_number):  # phone number format: +13604508655
    all_takeover = ManualTakeover.query.all()
    takeover_numbers = [mt.phone_number for mt in all_takeover]
    return f"+1{phone_number[1:]}" in takeover_numbers

def extract_integer(message):
    try:
        return int(message)
    except ValueError:
        return None

def incoming_message_processing(incoming_msg):
    processed_msg = incoming_msg.lower().strip()
    processed_msg = processed_msg.translate(str.maketrans("", "", string.punctuation))
    processed_msg_tokens = processed_msg.split()
    take_list = list(filter(lambda x: x == "t", processed_msg_tokens))
    skip_list = list(filter(lambda x: x == "s", processed_msg_tokens))
    everything_else = list(filter(lambda x: x != "t" and x != "s", processed_msg_tokens))
    final_message_list = []
    if len(take_list) > 0:
        final_message_list.append("t")
    elif len(skip_list) > 0:
        final_message_list.append("s")
    final_message_list.append(" ".join(everything_else))
    return final_message_list

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg_list = incoming_message_processing(request.values.get('Body', ''))
    incoming_phone_number = request.values.get('From', None)
    for incoming_msg in incoming_msg_list:
        # attempt to parse time from incoming msg
        datetime_data, parse_status = cal.parseDT(incoming_msg, tzinfo=pytzutc)  # this doesn't actually work, asking in this github issue https://github.com/bear/parsedatetime/issues/259
        if not any(char.isdigit() for char in incoming_msg):
            parse_status = 0  # force parse to be zero if the string was pure concept.
        activity_detection_time = activity_detection(incoming_msg)
        canned_response = canned_responses(incoming_msg)
        extracted_integer = extract_integer(incoming_msg)
        # canned response
        if not should_force_manual(incoming_phone_number) and (
                incoming_msg in ['1', '2', '3', 't', 's']
                or parse_status != 0
                or activity_detection_time is not None
                or extracted_integer is not None
            ):
            doses = Dose.query.filter_by(phone_number=f"+1{incoming_phone_number[1:]}").all()  # +113604508655
            dose_ids = [dose.id for dose in doses]
            latest_reminder_record = Reminder.query \
                .filter(Reminder.dose_id.in_(dose_ids)) \
                .order_by(Reminder.send_time.desc()) \
                .first()
            latest_dose_id = None if latest_reminder_record is None else latest_reminder_record.dose_id
            if exists_remaining_reminder_job(latest_dose_id, ["boundary"]):
                if incoming_msg in ["1", "2", "3"] \
                    or parse_status != 0 \
                    or activity_detection_time is not None \
                    or extracted_integer is not None:
                    obscure_confirmation = False
                    message_delays = {
                            "1": timedelta(minutes=10),
                            "2": timedelta(minutes=30),
                            "3": timedelta(hours=1)
                        }
                    remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                    dose_end_time = get_current_end_date(latest_dose_id)
                    if incoming_msg in ["1", "2", "3"]:
                        log_event("requested_time_delay", incoming_phone_number, description=f"{message_delays[incoming_msg]}")
                        next_alarm_time = get_time_now() + message_delays[incoming_msg]
                    elif extracted_integer is not None:
                        log_event("requested_time_delay", incoming_phone_number, description=f"{timedelta(minutes=extracted_integer)}")
                        next_alarm_time = get_time_now() + timedelta(minutes=extracted_integer)
                    elif activity_detection_time is not None:
                        next_alarm_time = get_time_now() + activity_detection_time[0]
                        obscure_confirmation = True
                        log_event("activity", f"+1{incoming_phone_number[1:]}", description=incoming_msg)
                    else:
                        next_alarm_time = datetime_data
                        if os.environ['FLASK_ENV'] == "local":  # HACK: required to get this to work on local
                            pacific_time = timezone(USER_TIMEZONE)
                            next_alarm_time = pacific_time.localize(datetime_data.replace(tzinfo=None))
                    too_close = False
                    if next_alarm_time > dose_end_time - timedelta(minutes=10):
                        next_alarm_time = dose_end_time - timedelta(minutes=10)
                        too_close = True
                    if next_alarm_time > get_time_now():
                        log_event("reminder_delay", f"+1{incoming_phone_number[1:]}", description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                        if obscure_confirmation:
                            client.messages.create(
                                body= activity_detection_time[1],
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:
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
                        if obscure_confirmation:
                            client.messages.create(
                                body= activity_detection_time[1],
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                elif incoming_msg in ["t", "s"]:
                    message_copy = {
                        "t": get_take_message(),
                        "s": SKIP_MSG
                    }
                    if incoming_msg == "t":
                        log_event("take", f"+1{incoming_phone_number[1:]}")
                    if incoming_msg == "s":
                        log_event("skip", f"+1{incoming_phone_number[1:]}")
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
                log_event("out_of_range", incoming_phone_number, description=incoming_msg)
                client.messages.create(
                    body=NO_DOSE_MSG,
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=incoming_phone_number
                )
        elif not should_force_manual(incoming_phone_number) and (canned_response is not None):
            log_event("conversational", f"+1{incoming_phone_number[1:]}", description=incoming_msg)
            client.messages.create(
                body=canned_response,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
        else:
            log_event("not_interpretable", f"+1{incoming_phone_number[1:]}", description=incoming_msg)
            text_fallback(incoming_phone_number)
    return jsonify()

def text_fallback(phone_number):
    if get_online_status():
        # if we're online, don't send the unknown text and let us respond.
        client.messages.create(
            body=MANUAL_TEXT_NEEDED_MSG.substitute(number=phone_number),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to="+13604508655"  # admin phone #
        )
    else:
        client.messages.create(
            body=UNKNOWN_MSG,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=phone_number
        )

@app.route("/manual", methods=["POST"])
def manual_send():
    incoming_data = request.json
    dose_id = int(incoming_data["doseId"])
    reminder_type = incoming_data["reminderType"]
    if reminder_type == "absent":
        send_absent_text(dose_id)
    elif reminder_type == "followup":
        send_followup_text(dose_id)
    elif reminder_type == "initial":
        send_intro_text(dose_id)
    return jsonify()

@app.route("/manual/takeover", methods=["POST"])
def manual_takeover():
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    takeover_record = ManualTakeover.query.get(f"+11{target_phone_number}")
    if takeover_record is None:
        new_takeover_record = ManualTakeover(phone_number=f"+11{target_phone_number}")
        db.session.add(new_takeover_record)
        db.session.commit()
    return jsonify()

@app.route("/manual/takeover", methods=["DELETE"])
def end_manual_takeover():
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    takeover_record = ManualTakeover.query.get(f"+11{target_phone_number}")
    if takeover_record is not None:
        db.session.delete(takeover_record)
        db.session.commit()
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
    log_event("manual_text", f"+11{target_phone_number}", description=text)
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
    if end_date is not None:  # if it's none, there's no boundary set up
        desired_absent_reminder = min(get_time_now() + timedelta(minutes=random.randint(45,75)), end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > get_time_now():
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
    current_end_date = scheduled_job.next_run_time
    return current_end_date

def send_followup_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=get_followup_message(),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="followup")
    db.session.add(reminder_record)
    db.session.commit()
    # remove absent jobs, if exist
    remove_jobs_helper(dose_id, ["absent", "followup"])
    maybe_schedule_absent(dose_id)
    log_event("followup", dose_obj.phone_number)

def send_absent_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=ABSENT_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="absent")
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_id, ["absent", "followup"])
    log_event("absent", dose_obj.phone_number)  # need this bc the function is cached during scheduling
    maybe_schedule_absent(dose_id)

def send_boundary_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=CLINICAL_BOUNDARY_MSG.substitute(time=get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%I:%M')) if dose_obj.phone_number[3:] in CLINICAL_BOUNDARY_PHONE_NUMBERS else BOUNDARY_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="boundary")
    db.session.add(reminder_record)
    db.session.commit()
    # this shouldn't be needed, but followups sent manually leave absent artifacts
    remove_jobs_helper(dose_id, ["absent", "followup"])
    log_event("boundary", dose_obj.phone_number)

def send_intro_text(dose_id, manual=False):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=f"{get_initial_message().substitute(time=get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%I:%M'))}{ACTION_MENU}",
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="initial")
    db.session.add(reminder_record)
    db.session.commit()
    scheduler.add_job(f"{dose_id}-boundary", send_boundary_text,
        args=[dose_id],
        trigger="date",
        run_date=dose_obj.next_end_date if manual else dose_obj.next_end_date - timedelta(days=1)  # HACK, assumes this executes after start_date
    )
    maybe_schedule_absent(dose_id)
    log_event("initial", dose_obj.phone_number)


if __name__ == '__main__':
    app.run(host='0.0.0.0')