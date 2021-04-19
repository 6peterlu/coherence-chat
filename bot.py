from flask import Flask, request, jsonify, send_from_directory
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
# import Flask-APScheduler
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os
# from twilio.twiml.messaging_response import MessagingResponse
from twilio.rest import Client
from datetime import datetime, timedelta
from functools import wraps
from pytz import timezone, utc as pytzutc
import parsedatetime
import random
import string
from itertools import chain, groupby

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)

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
    "meeting",
    "walking",
    "walk",
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
    "brunch",
    "later",
    "golf",
    "tennis",
    "swimming",
    "basketball",
    "shower",
    "working",
    "tv",
    "yes"
]

ALL_EVENTS = [
    "paused",
    "resumed",
    "user_reported_error",
    "requested_time_delay",
    "activity",
    "reminder_delay",
    "take",
    "skip",
    "out_of_range",
    "conversational",
    "not_interpretable",
    "manual_text",
    "followup",
    "absent",
    "boundary",
    "initial"
]

# load on server start
SPACY_EMBED_MAP = {token: nlp(token) for token in TOKENS_TO_RECOGNIZE}

import logging
from constants import (
    ABSENT_MSGS,
    ACTION_OUT_OF_RANGE_MSG,
    BOUNDARY_MSG,
    CLINICAL_BOUNDARY_MSG,
    CONFIRMATION_MSG,
    FUTURE_MESSAGE_SUFFIXES,
    INITIAL_MSGS,
    ERROR_MSG,
    FOLLOWUP_MSGS,
    INITIAL_SUFFIXES,
    MANUAL_TEXT_NEEDED_MSG,
    PAUSE_MESSAGE,
    REMINDER_OUT_OF_RANGE_MSG,
    REMINDER_TOO_CLOSE_MSG,
    REMINDER_TOO_LATE_MSG,
    SECRET_CODE_MESSAGE,
    SKIP_MSG,
    TAKE_MSG,
    TAKE_MSG_EXCITED,
    THANKS_MESSAGES,
    TIME_OF_DAY_PREFIX_MAP,
    UNKNOWN_MSG,
    ACTION_MENU,
    USER_ERROR_REPORT,
    USER_ERROR_RESPONSE,
    WELCOME_BACK_MESSAGES
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


PATIENT_DOSE_MAP = { "+113604508655": {"morning": [153, 154], "afternoon": [114, 152]}} if os.environ["FLASK_ENV"] == "local" else {
    "+113604508655": {"morning": [85]},
    "+113609042210": {"afternoon": [25], "evening": [15]},
    "+113609049085": {"evening": [16]},
    "+114152142478": {"morning": [26, 82]},
    "+116502690598": {"evening": [27]},
    "+118587761377": {"morning": [29]},
    "+113607738908": {"morning": [68, 87], "evening": [69, 81]},
    "+115038871884": {"morning": [70], "afternoon": [71]},
    "+113605214193": {"morning": [72], "evening": [74]},
    "+113605131225": {"morning": [75], "afternoon": [76], "evening": [77]},
    "+113606064445": {"afternoon": [78, 88]},
    "+113609010956": {"evening": [86]}
}

PATIENT_NAME_MAP = { "+113604508655": "Peter" } if os.environ["FLASK_ENV"] == "local" else {
    "+113604508655": "Peter",
    "+113606064445": "Cheryl",
    "+113609042210": "Steven",
    "+113609049085": "Tao",
    "+114152142478": "Miki",
    "+116502690598": "Caroline",
    "+118587761377": "Hadara",
    "+113607738908": "Karrie",
    "+115038871884": "Charles",
    "+113605214193": "Leann",
    "+113605131225": "Jeanette",
    "+113609010956": "Andie"
}

SECRET_CODES = { "+113604508655": 123456 } if os.environ["FLASK_ENV"] == "local" else {
    "+113604508655": 123456,
    "+113606064445": 110971,
    "+113609042210": 902157,
    "+113609049085": 311373,
    "+114152142478": 332274,
    "+116502690598": 320533,
    "+118587761377": 548544,
    "+113607738908": 577505,
    "+115038871884": 474580,
    "+113605214193": 402913,
    "+113605131225": 846939,
    "+113609010956": 299543
}

ACTIVITY_BUCKET_SIZE_MINUTES = 10

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
    SEND_FILE_MAX_AGE_DEFAULT = 0

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
    active = db.Column(db.Boolean)

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

    def within_dosing_period(self, time=None):
        time_to_compare = get_time_now() if time is None else time
        # boundary condition
        return self.next_end_date - timedelta(days=1) > time_to_compare and self.next_start_date - timedelta(days=1) < time_to_compare

    def already_recorded(self):
        matching_events = Event.query.filter(
            Event.description == str(self.id),
            Event.event_type.in_(["take", "skip"]),
            Event.event_time > self.next_start_date - timedelta(days=1),
            Event.event_time < self.next_end_date - timedelta(days=1)
        ).all()
        if len(matching_events) > 0:
            return True
        return False


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

    @property
    def aware_event_time(self):
        return self.event_time.replace(tzinfo=datetime.now().astimezone().tzinfo)

# list of users that have all messages manually responded to
class ManualTakeover(db.Model):
    phone_number = db.Column(db.String(13), primary_key=True)

# list of users that have paused the reminder service
class PausedService(db.Model):
    phone_number = db.Column(db.String(13), primary_key=True)


# initialize tables
db.create_all()  # are there bad effects from running this every time? edit: I guess not

# twilio objects
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# initialize scheduler
scheduler = APScheduler()

# not calling this with false anywhere
def get_time_now(tzaware=True):
    return datetime.now(pytzutc) if tzaware else datetime.utcnow()

# message helpers
def get_followup_message():
    return random.choice(FOLLOWUP_MSGS)

def get_initial_message(dose_id, time_string, welcome_back=False):
    current_time_of_day = None
    for phone_number in PATIENT_DOSE_MAP:
        for time_of_day in PATIENT_DOSE_MAP[phone_number]:
            if dose_id in PATIENT_DOSE_MAP[phone_number][time_of_day]:
                current_time_of_day = time_of_day
    if welcome_back:
        return f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"
    random_choice = random.random()
    if random_choice < 0.8 or current_time_of_day is None:
        return random.choice(INITIAL_MSGS).substitute(time=time_string)
    else:
        return f"{random.choice(TIME_OF_DAY_PREFIX_MAP[current_time_of_day])} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"

def get_take_message(excited):
    datestring = get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%b %d, %I:%M %p')
    return TAKE_MSG_EXCITED.substitute(time=datestring) if excited else TAKE_MSG.substitute(time=datestring)

def get_absent_message():
    return random.choice(ABSENT_MSGS)

def get_thanks_message():
    return random.choice(THANKS_MESSAGES)


def log_event(event_type, phone_number, event_time=None, description=None):
    if event_time is None:
        event_time = get_time_now()  # done at runtime for accurate timing
    new_event = Event(event_type=event_type, phone_number=phone_number, event_time=event_time, description=description)
    db.session.add(new_event)
    db.session.commit()


def auth_required_get(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.args.get("pw") != "couchsurfing":
            return jsonify(), 401
        else:
            return f(*args, **kwargs)
    return decorated_function

def auth_required_post_delete(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if request.json.get("pw") != "couchsurfing":
            return jsonify(), 401
        else:
            return f(*args, **kwargs)
    return decorated_function


# makes sure our clients refresh their pages on update
@app.after_request
def add_header(resp):
    resp.headers["Cache-Control"] = "no-cache, no-store, must-revalidate"
    resp.headers["Pragma"] = "no-cache"
    resp.headers["Expires"] = "0"
    return resp

@app.route("/", methods=["GET"])
def patient_page():
    return app.send_static_file('index.html')

@app.route("/css/<path:path>", methods=["GET"])
def serve_css(path):
    return send_from_directory('css', path)

@app.route("/svg/<path:path>", methods=["GET"])
def serve_svg(path):
    return send_from_directory('svg', path)


def round_date(dt, delta=ACTIVITY_BUCKET_SIZE_MINUTES, round_up=False):
    if round_up:
        return dt + (datetime.min - dt) % timedelta(minutes=delta)
    else:  # round down
        return dt - (dt - datetime.min) % timedelta(minutes=delta)



# NOTE: Not currently used.
def generate_activity_analytics(user_events):
    day_stripped_events = [event.event_time.replace(day=1, month=1, year=1, microsecond=0) for event in user_events]
    groups = []
    keys = []
    for k, g in groupby(day_stripped_events, round_date):
        keys.append(k)
        groups.append(list(g))
    collected_data = dict(zip(keys, groups))
    num_buckets = keys[len(keys) - 1] - keys[0]
    activity_data = {}
    for time_increment in range(int(num_buckets.seconds / (ACTIVITY_BUCKET_SIZE_MINUTES * 60))):
        bucket_id = keys[0] + timedelta(minutes = time_increment * 15)
        if bucket_id in collected_data:
            activity_data[bucket_id.isoformat()] = len(collected_data[bucket_id])
        else:
            activity_data[bucket_id.isoformat()] = 0
    if not activity_data:
        return {}
    largest_count = max(activity_data.values())
    for bucket in activity_data:
        activity_data[bucket] /= largest_count
    return activity_data


# takes user behavior events to the beginning of time
def generate_behavior_learning_scores(user_behavior_events, active_doses):
    # end time is end of yesterday.
    end_time = get_time_now().astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    user_behavior_events_until_today = list(filter(lambda event: event.aware_event_time < end_time, user_behavior_events))
    if len(user_behavior_events_until_today) == 0:
        return {}
    behavior_scores_by_day = {}
    # starts at earliest day
    current_day_bucket = user_behavior_events_until_today[0].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    lastest_day = user_behavior_events_until_today[len(user_behavior_events_until_today) - 1].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    while current_day_bucket <= lastest_day:
        print("bucket")
        current_day_events = list(filter(lambda event: event.aware_event_time < current_day_bucket + timedelta(days=1) and event.aware_event_time > current_day_bucket, user_behavior_events_until_today))
        current_day_take_skip = list(filter(lambda event: event.event_type in ["take", "skip"], current_day_events))
        unique_time_buckets = []
        print(current_day_events)
        for k, _ in groupby([event.event_time for event in current_day_events], round_date):
            unique_time_buckets.append(k)
        behavior_score_for_day = len(current_day_take_skip) * 3 / len(active_doses) + len(unique_time_buckets) * 2 / len (active_doses) - 3
        behavior_scores_by_day[current_day_bucket] = behavior_score_for_day
        current_day_bucket += timedelta(days=1)
    score_sum = 0
    starting_buffer = len(behavior_scores_by_day) - 7  # combine all data before last 7 days
    output_scores = {}
    for day in behavior_scores_by_day:
        score_sum += behavior_scores_by_day[day]
        if starting_buffer == 0:
            output_scores[day] = score_sum
        else:
            starting_buffer -= 1
    print(output_scores)
    return "hello"


@app.route("/patientData", methods=["GET"])
def patient_data():
    recovered_cookie = request.cookies.get("phoneNumber")
    if recovered_cookie is None:
        return jsonify()  # empty response if no cookie
    phone_number = f"+11{recovered_cookie}"
    if phone_number not in PATIENT_DOSE_MAP:
        response = jsonify({"error": "The secret code was incorrect. Please double-check that you've entered it correctly."})
        response.set_cookie("phoneNumber", "", expires=0)
        return response
    patient_dose_times = PATIENT_DOSE_MAP[phone_number]
    relevant_dose_ids = list(chain.from_iterable(patient_dose_times.values()))
    relevant_dose_ids_as_str = [str(x) for x in relevant_dose_ids]
    relevant_doses = Dose.query.filter(Dose.id.in_(relevant_dose_ids), Dose.active.is_(True)).all()
    take_record_events = [
        "take",
        "skip",
        "boundary"
    ]
    user_driven_events = [
        "take",
        "skip",
        "paused",
        "resumed",
        "user_reported_error",
        "out_of_range",
        "not_interpretable",
        "requested_time_delay",
        "activity"
    ]
    combined_list = list(set(take_record_events) | set(user_driven_events))
    # rules
    # ignore: reminder_delay
    # reminders from us: followup, absent, boundary, initial, manual_text
    # best user activity: take, skip
    # moderate user activity: paused, resumed, user_reported_error, out_of_range, not_interpretable
    # worst user activity: requested_time_delay, activity
    relevant_events = Event.query.filter(Event.event_type.in_(combined_list), Event.phone_number == phone_number).all()
    dose_history_events = list(filter(lambda event: event.event_type in take_record_events and event.description in relevant_dose_ids_as_str, relevant_events))
    user_behavior_events = list(filter(lambda event: event.event_type in user_driven_events, relevant_events))
    for event in user_behavior_events:
        print(event.event_type)
    # NOTE: add back in later (but maybe post-react world)
    # activity_analytics = generate_activity_analytics(user_behavior_events)
    event_data_by_time = {}
    for time in patient_dose_times:
        event_data_by_time[time] = {"events": []}
        dose_ids = patient_dose_times[time]
        for event in dose_history_events:
            if int(event.description) in dose_ids:
                event_data_by_time[time]["events"].append(event.as_dict())
        for dose in relevant_doses:
            if dose.id in dose_ids:
                event_data_by_time[time]["dose"] = dose.as_dict()
                break
    dose_to_take_now = False
    for dose in relevant_doses:
        if dose.within_dosing_period() and not dose.already_recorded():
            dose_to_take_now = True
            break
    paused_service = PausedService.query.get(phone_number)
    behavior_learning_scores = generate_behavior_learning_scores(user_behavior_events, relevant_doses)
    return jsonify({
        "phoneNumber": recovered_cookie,
        "eventData": event_data_by_time,
        "patientName": PATIENT_NAME_MAP[phone_number],
        "takeNow": dose_to_take_now,
        "pausedService": bool(paused_service),
        "behaviorLearningScores": behavior_learning_scores
    })

@app.route("/pauseService", methods=["POST"])
def pause_service():
    recovered_cookie = request.cookies.get("phoneNumber")
    if recovered_cookie is None:
        return jsonify(), 401  # empty response if no cookie
    formatted_phone_number = f"+11{recovered_cookie}"
    relevant_doses = Dose.query.filter(Dose.phone_number == formatted_phone_number, Dose.active.is_(True)).all()
    relevant_doses = sorted(relevant_doses, key=lambda dose: dose.next_start_date)
    paused_service = PausedService.query.get(formatted_phone_number)
    if paused_service is None:
        paused_service = PausedService(phone_number=formatted_phone_number)
        db.session.add(paused_service)
        for dose in relevant_doses:
            remove_jobs_helper(dose.id, ["initial", "absent", "boundary", "followup"])
        # send pause message
        client.messages.create(
            body=PAUSE_MESSAGE,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=formatted_phone_number
        )
        log_event("paused", formatted_phone_number)
    else:
        db.session.delete(paused_service)
        for idx, dose in enumerate(relevant_doses):
            if idx == 0:
                resume_dose(dose, next_dose=True)
            else:
                resume_dose(dose)
        log_event("resumed", formatted_phone_number)
    db.session.commit()
    return jsonify()


def resume_dose(dose_obj, next_dose=False):
    if dose_obj.within_dosing_period() and not dose_obj.already_recorded():
        # send initial reminder text immediately
        send_intro_text(dose_obj.id, welcome_back=True)
    elif next_dose:
        # send welcome message immediately, but no reminder
        client.messages.create(
            body=f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(FUTURE_MESSAGE_SUFFIXES).substitute(time=dose_obj.next_start_date.astimezone(timezone(USER_TIMEZONE)).strftime('%I:%M %p'))}",
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=dose_obj.phone_number
        )
    # set up recurring job
    scheduler.add_job(f"{dose_obj.id}-initial", send_intro_text,
        trigger="interval",
        start_date=dose_obj.next_start_date,
        days=1,
        args=[dose_obj.id],
        misfire_grace_time=5*60
    )


@app.route("/login", methods=["POST"])
def save_phone_number():
    secret_code = request.json["code"]
    phone_number = request.json["phoneNumber"]
    numeric_filter = filter(str.isdigit, phone_number)
    phone_number = "".join(numeric_filter)
    if len(phone_number) == 11 and phone_number[0] == "1":
        phone_number = phone_number[1:]
    phone_number_formatted = f"+11{phone_number}"
    if secret_code == str(SECRET_CODES[phone_number_formatted]):
        out = jsonify()
        out.set_cookie("phoneNumber", phone_number)
        log_event("successful_login", phone_number_formatted)
        return out
    log_event("failed_login", phone_number_formatted)
    return jsonify(), 401

@app.route("/login/requestCode", methods=["POST"])
def request_secret_code():
    phone_number = request.json["phoneNumber"]
    numeric_filter = filter(str.isdigit, phone_number)
    phone_number = "".join(numeric_filter)
    if len(phone_number) == 11 and phone_number[0] == "1":
        phone_number = phone_number[1:]
    phone_number_formatted = f"+11{phone_number}"
    if phone_number_formatted in SECRET_CODES:
        client.messages.create(
            body=SECRET_CODE_MESSAGE.substitute(code=SECRET_CODES[phone_number_formatted]),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=phone_number_formatted
        )
        return jsonify()
    return jsonify(), 401

@app.route("/logout", methods=["GET"])
def logout():
    out = jsonify()
    out.set_cookie("phoneNumber", "", expires=0)
    return out


@app.route("/admin", methods=["GET"])
def admin_page():
    return app.send_static_file('admin.html')

# add a dose
@app.route("/dose", methods=["POST"])
@auth_required_post_delete
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
        medication_name=medication_name,
        active=True
    )
    db.session.add(new_dose_record)
    db.session.commit()
    pause_record = PausedService.query.get(phone_number)
    # only add job if service is not paused
    if pause_record is None:
        scheduler.add_job(f"{new_dose_record.id}-initial", send_intro_text,
            trigger="interval",
            start_date=new_dose_record.next_start_date,
            days=1,
            args=[new_dose_record.id],
            misfire_grace_time=5*60
        )
    return jsonify()

@app.route("/dose/editName", methods=["POST"])
@auth_required_post_delete
def edit_dose_name():
    incoming_data = request.json
    new_name = incoming_data["doseName"]
    dose_id = int(incoming_data["doseId"])
    dose_to_modify = Dose.query.get(dose_id)
    dose_to_modify.medication_name = new_name
    db.session.commit()
    return jsonify()

@app.route("/dose/toggleActivate", methods=["POST"])
@auth_required_post_delete
def toggle_dose_activate():
    incoming_data = request.json
    dose_id = incoming_data["doseId"]
    relevant_dose = Dose.query.get(dose_id)
    relevant_dose.active = not relevant_dose.active
    db.session.commit()
    if relevant_dose.active:
        scheduler.add_job(f"{relevant_dose.id}-initial", send_intro_text,
            trigger="interval",
            start_date=relevant_dose.next_start_date,
            days=1,
            args=[relevant_dose.id],
            misfire_grace_time=5*60
        )
    else:
        remove_jobs_helper(relevant_dose.id, ["boundary", "initial", "followup", "absent"])
    return jsonify()

@app.route("/dose", methods=["DELETE"])
@auth_required_post_delete
def delete_dose():
    incoming_data = request.json
    id_to_delete = int(incoming_data["id"])
    remove_jobs_helper(id_to_delete, ["boundary", "initial", "followup", "absent"])
    Dose.query.filter_by(id=id_to_delete).delete()
    db.session.commit()
    return jsonify()

@app.route("/reminder", methods=["DELETE"])
@auth_required_post_delete
def delete_reminder():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Reminder.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

# TODO: take phone number as arg, and only grab data for that number
@app.route("/everything", methods=["GET"])
@auth_required_get
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
@auth_required_get
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
@auth_required_post_delete
def delete_event():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Event.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

@app.route("/events", methods=["POST"])
@auth_required_post_delete
def post_event():
    incoming_data = request.json
    phone_number = f"+11{incoming_data['phoneNumber']}"
    event_type = incoming_data["eventType"]
    dose_id = incoming_data["doseId"]
    event_time_raw = incoming_data["eventTime"]
    if not event_time_raw:
        log_event(event_type=event_type, phone_number=phone_number, description=dose_id)
    else:
        event_time_obj = datetime.strptime(event_time_raw, "%Y-%m-%dT%H:%M")
        if os.environ["FLASK_ENV"] != "local":
            event_time_obj += timedelta(hours=7)  # HACK to transform to UTC
        log_event(event_type=event_type, phone_number=phone_number, description=dose_id, event_time=event_time_obj)
    return jsonify()

@app.route("/messages", methods=["GET"])
@auth_required_get
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
@auth_required_post_delete
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
    time_delay_long = timedelta(minutes=random.randint(30,60))
    time_delay_short = timedelta(minutes=random.randint(10,30))
    direct_time_mapped_strings = {
        "brunch": (time_delay_long, f"{computing_prefix} Have a great brunch! We'll check in later."),
        "dinner": (time_delay_long, f"{computing_prefix} Have a great dinner! We'll check in later."),
        "lunch": (time_delay_long, f"{computing_prefix} Have a great lunch! We'll check in later."),
        "breakfast": (time_delay_long, f"{computing_prefix} Have a great breakfast! We'll check in later."),
        "walking": (time_delay_short, f"{computing_prefix} Enjoy your walk! We'll check in later."),
        "walk": (time_delay_short, f"{computing_prefix} Enjoy your walk! We'll check in later."),
        "eating": (time_delay_long, f"{computing_prefix} Enjoy your meal! We'll check in later."),
        "meeting": (time_delay_long, f"{computing_prefix} Have a productive meeting! We'll check in later."),
        "call": (time_delay_long, f"{computing_prefix} Have a great call! We'll check in later."),
        "out": (time_delay_long, f"{computing_prefix} No problem, we'll check in later."),
        "busy": (time_delay_long, f"{computing_prefix} No problem, we'll check in later."),
        "later": (time_delay_long, f"{computing_prefix} No problem, we'll check in later."),
        "bathroom": (time_delay_short, f"{computing_prefix} No problem, we'll check in in a bit."),
        "reading": (time_delay_long, f"{computing_prefix} Enjoy your book, we'll check in later."),
        "run": (time_delay_short, f"{computing_prefix} Have a great run! We'll see you later."),
        "running": (time_delay_short, f"{computing_prefix} Have a great run! We'll see you later."),
        "sleeping": (time_delay_long, f"{computing_prefix} Sleep well! We'll see you later."),
        "golf": (time_delay_long, f"{computing_prefix} Have fun out there! We'll see you later."),
        "tennis": (time_delay_long, f"{computing_prefix} Have fun out there! We'll see you later."),
        "swimming": (time_delay_long, f"{computing_prefix} Have fun out there! We'll see you later."),
        "basketball": (time_delay_short, f"{computing_prefix} Have fun out there! We'll see you later."),
        "tv": (time_delay_long, f"{computing_prefix} Have fun, we'll check in later."),
        "shower": (time_delay_short, f"{computing_prefix} Have a good shower, we'll check in later."),
        "working": (time_delay_long, f"{computing_prefix} No problem, we'll check in later."),
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
    # use this code block for any hardcoded canned responses we need
    # hardcoded_responses = {
    #     "x": "Thanks for reporting. We've noted the error and are working on it."
    # }
    # if message_str in hardcoded_responses:
    #     return hardcoded_responses[message_str]
    responses = {
        "thanks": get_thanks_message(),
        "help": UNKNOWN_MSG,
        "confused": UNKNOWN_MSG,
        "ok": "👍",
        "great": "👍",
        "no problem": "👍",
        "hello": "Hello! 👋",
        "yes": "Great, you use 'T' to mark your medication as taken."
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

# this function returns a list of tokens which get processed in order through chat pipeline
# note that there's no guarantee of text sending order
def incoming_message_processing(incoming_msg):
    processed_msg = incoming_msg.lower().strip()
    excited = "!" in processed_msg
    processed_msg = processed_msg.translate(str.maketrans("", "", string.punctuation))
    processed_msg = processed_msg.replace("[", "").replace("]", "")
    processed_msg_tokens = processed_msg.split()
    take_list = list(filter(lambda x: x == "t" or x == "taken", processed_msg_tokens))
    skip_list = list(filter(lambda x: x == "s", processed_msg_tokens))
    error_list = list(filter(lambda x: x == "x", processed_msg_tokens))
    thanks_list = list(filter(lambda x: x == "thanks" or x == "thank", processed_msg_tokens))
    filler_words = ["taking", "going", "to", "a", "for", "on", "still"]
    everything_else = list(filter(lambda x: x != "t" and x != "s" and x != "taken" and x not in filler_words, processed_msg_tokens))
    final_message_list = []
    if len(error_list) > 0:
        return ["x"]  # no more message processing
    if len(take_list) > 0:
        final_message_list.append("t")
    elif len(skip_list) > 0:
        final_message_list.append("s")
    if len(thanks_list) > 0:
        final_message_list.append("thanks")
    elif len(everything_else) > 0:
        coalesce_words = ["dinner", "breakfast", "lunch", "brunch", "sleeping", "bathroom", "shower", "tv"]
        intersection = list(filter(lambda x: x in coalesce_words, everything_else))
        if len(intersection) > 0:
            final_message_list.append(intersection[0])  # just append matched concept if any
        else:
            final_message_list.append(" ".join(everything_else))
    return final_message_list, excited

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg_list, excited = incoming_message_processing(request.values.get('Body', ''))
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
                incoming_msg in ['1', '2', '3', 't', 's', 'x']
                or parse_status != 0
                or activity_detection_time is not None
                or extracted_integer is not None
            ):
            # handle error report
            if incoming_msg == 'x':
                client.messages.create(
                    body=USER_ERROR_REPORT.substitute(phone_number=incoming_phone_number),
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to="+13604508655"
                )
                client.messages.create(
                    body=USER_ERROR_RESPONSE,
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=incoming_phone_number
                )
                log_event("user_reported_error", f"+1{incoming_phone_number[1:]}")
                return jsonify()
            doses = Dose.query.filter_by(phone_number=f"+1{incoming_phone_number[1:]}").all()  # +113604508655
            dose_ids = [dose.id for dose in doses]
            latest_reminder_record = Reminder.query \
                .filter(Reminder.dose_id.in_(dose_ids)) \
                .order_by(Reminder.send_time.desc()) \
                .first()
            latest_dose_id = None if latest_reminder_record is None else latest_reminder_record.dose_id
            matching_dose_list = list(filter(lambda dose: dose.id == latest_dose_id, doses))
            latest_dose = matching_dose_list[0] if len(matching_dose_list) > 0 else None
            if latest_dose is not None and latest_dose.within_dosing_period():
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
                        log_event("requested_time_delay", f"+1{incoming_phone_number[1:]}", description=f"{message_delays[incoming_msg]}")
                        next_alarm_time = get_time_now() + message_delays[incoming_msg]
                    elif extracted_integer is not None:
                        log_event("requested_time_delay", f"+1{incoming_phone_number[1:]}", description=f"{timedelta(minutes=extracted_integer)}")
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
                            run_date=next_alarm_time,
                            misfire_grace_time=5*60
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
                        "t": get_take_message(excited),
                        "s": SKIP_MSG
                    }
                    if incoming_msg == "t":
                        log_event("take", f"+1{incoming_phone_number[1:]}", description=latest_dose_id)
                    if incoming_msg == "s":
                        log_event("skip", f"+1{incoming_phone_number[1:]}", description=latest_dose_id)
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
                log_event("out_of_range", f"+1{incoming_phone_number[1:]}", description=incoming_msg)
                client.messages.create(
                    body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
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
@auth_required_post_delete
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
@auth_required_post_delete
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
@auth_required_post_delete
def end_manual_takeover():
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    takeover_record = ManualTakeover.query.get(f"+11{target_phone_number}")
    if takeover_record is not None:
        db.session.delete(takeover_record)
        db.session.commit()
    return jsonify()


@app.route("/manual/text", methods=["POST"])
@auth_required_post_delete
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
            run_date=desired_absent_reminder,
            misfire_grace_time=5*60
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
    log_event("followup", dose_obj.phone_number, description=dose_id)

def send_absent_text(dose_id):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=get_absent_message(),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="absent")
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_id, ["absent", "followup"])
    log_event("absent", dose_obj.phone_number, description=dose_id)
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
    log_event("boundary", dose_obj.phone_number, description=dose_id)

def send_intro_text(dose_id, manual=False, welcome_back=False):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=f"{get_initial_message(dose_id, get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%I:%M'), welcome_back)}{ACTION_MENU}",
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=dose_obj.phone_number
    )
    reminder_record = Reminder(dose_id=dose_id, send_time=get_time_now(), reminder_type="initial")
    db.session.add(reminder_record)
    db.session.commit()
    scheduler.add_job(f"{dose_id}-boundary", send_boundary_text,
        args=[dose_id],
        trigger="date",
        run_date=dose_obj.next_end_date if manual else dose_obj.next_end_date - timedelta(days=1),  # HACK, assumes this executes after start_date
        misfire_grace_time=5*60
    )
    maybe_schedule_absent(dose_id)
    log_event("initial", dose_obj.phone_number, description=dose_id)

def scheduler_error_alert(event):
    with scheduler.app.app_context():
        client.messages.create(
            body=f"Scheduler reports job missed for event ID {event.job_id}.",
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to="+13604508655"
        )
scheduler.add_listener(scheduler_error_alert, EVENT_JOB_MISSED | EVENT_JOB_ERROR)
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0')