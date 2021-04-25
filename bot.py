from flask import Flask, request, jsonify, send_from_directory
from sqlalchemy.sql.expression import false
from flask_cors import CORS
from flask_sqlalchemy import SQLAlchemy
# import Flask-APScheduler
from flask_apscheduler import APScheduler
from apscheduler.jobstores.sqlalchemy import SQLAlchemyJobStore
import os
from twilio.rest import Client
from datetime import datetime, timedelta
from functools import wraps
from pytz import timezone, utc as pytzutc
import parsedatetime
import random
from itertools import chain, groupby
from werkzeug.middleware.proxy_fix import ProxyFix
from models import (
    Dose,
    Reminder,
    Online,
    ManualTakeover,
    Event,
    PausedService,
    # new data models
    User,
    EventLog,
    DoseWindow,
    Medication,
    # new data schemas
    UserSchema,
    DoseWindowSchema,
    MedicationSchema,
    EventLogSchema
)

from models import db
from nlp import segment_message

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
    "yes",
    "phone"
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
    ALREADY_RECORDED,
    BOUNDARY_MSG,
    CLINICAL_BOUNDARY_MSG,
    CONFIRMATION_MSG,
    FUTURE_MESSAGE_SUFFIXES,
    INITIAL_MSGS,
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


PATIENT_DOSE_MAP = { "+113604508655": {"morning": [153, 154, 173], "afternoon": [114, 152]}} if os.environ["FLASK_ENV"] == "local" else {
    "+113604508655": {"morning": [85]},
    "+113609042210": {"afternoon": [25], "evening": [15]},
    "+113609049085": {"evening": [16]},
    "+114152142478": {"morning": [26, 82, 92]},
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

IP_BLACKLIST = ["73.93.153.54", "73.15.102.35", "73.93.154.210"]

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
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)

# sqlalchemy db
db.app = app
db.init_app(app)

# parse datetime calendar object
cal = parsedatetime.Calendar()


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

def get_initial_message(dose_id, time_string, welcome_back=False, phone_number=None):
    current_time_of_day = None
    for phone_number in PATIENT_DOSE_MAP:
        for time_of_day in PATIENT_DOSE_MAP[phone_number]:
            if dose_id in PATIENT_DOSE_MAP[phone_number][time_of_day]:
                current_time_of_day = time_of_day
    if welcome_back:
        return f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"
    random_choice = random.random()
    if random_choice < 0.8 or current_time_of_day is None or phone_number == "+114152142478":  # blacklist miki
        return random.choice(INITIAL_MSGS).substitute(time=time_string)
    else:
        return f"{random.choice(TIME_OF_DAY_PREFIX_MAP[current_time_of_day])} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"

def get_take_message(excited, input_time=None):
    datestring = get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%b %d, %I:%M %p') if input_time is None else input_time.strftime('%b %d, %I:%M %p')
    return TAKE_MSG_EXCITED.substitute(time=datestring) if excited else TAKE_MSG.substitute(time=datestring)

def get_take_message_new(excited, user_obj, input_time=None):
    datestring = get_time_now().astimezone(timezone(user_obj.timezone)).strftime('%b %d, %I:%M %p') if input_time is None else input_time.strftime('%b %d, %I:%M %p')
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

def log_event_new(event_type, user_id, dose_window_id, medication_id=None, event_time=None, description=None):
    if event_time is None:
        event_time = get_time_now()  # done at runtime for accurate timing
    new_event = EventLog(
        event_type=event_type,
        user_id=user_id,
        dose_window_id=dose_window_id,
        medication_id=medication_id,
        event_time=event_time,
        description=description
    )
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
# def generate_activity_analytics(user_events):
#     day_stripped_events = [event.event_time.replace(day=1, month=1, year=1, microsecond=0) for event in user_events]
#     groups = []
#     keys = []
#     for k, g in groupby(day_stripped_events, round_date):
#         keys.append(k)
#         groups.append(list(g))
#     collected_data = dict(zip(keys, groups))
#     num_buckets = keys[len(keys) - 1] - keys[0]
#     activity_data = {}
#     for time_increment in range(int(num_buckets.seconds / (ACTIVITY_BUCKET_SIZE_MINUTES * 60))):
#         bucket_id = keys[0] + timedelta(minutes = time_increment * 15)
#         if bucket_id in collected_data:
#             activity_data[bucket_id.isoformat()] = len(collected_data[bucket_id])
#         else:
#             activity_data[bucket_id.isoformat()] = 0
#     if not activity_data:
#         return {}
#     largest_count = max(activity_data.values())
#     for bucket in activity_data:
#         activity_data[bucket] /= largest_count
#     return activity_data


# TODO: rewrite this
# takes user behavior events to the beginning of time
def generate_behavior_learning_scores(user_behavior_events, active_doses):
    # end time is end of yesterday.
    end_time = get_time_now().astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    user_behavior_events_until_today = list(filter(lambda event: event.aware_event_time < end_time, user_behavior_events))
    if len(user_behavior_events_until_today) == 0 or len(active_doses) == 0:
        return {}
    behavior_scores_by_day = {}
    # starts at earliest day
    current_day_bucket = user_behavior_events_until_today[0].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    # latest_day = user_behavior_events_until_today[len(user_behavior_events_until_today) - 1].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    while current_day_bucket < end_time:
        current_day_events = list(filter(lambda event: event.aware_event_time < current_day_bucket + timedelta(days=1) and event.aware_event_time > current_day_bucket, user_behavior_events_until_today))
        current_day_take_skip = list(filter(lambda event: event.event_type in ["take", "skip"], current_day_events))
        unique_time_buckets = []
        for k, _ in groupby([event.event_time for event in current_day_events], round_date):
            unique_time_buckets.append(k)
        behavior_score_for_day = len(current_day_take_skip) * 3 / len(active_doses) + len(unique_time_buckets) * 2 / len (active_doses) - 3
        behavior_scores_by_day[current_day_bucket] = behavior_score_for_day
        current_day_bucket += timedelta(days=1)
    score_sum = 0
    starting_buffer = len(behavior_scores_by_day) - 7  # combine all data before last 7 days
    output_scores = []
    for day in behavior_scores_by_day:
        score_sum += behavior_scores_by_day[day]
        if score_sum < 0:
            score_sum = 0
        elif score_sum > 100:
            score_sum = 100
        if starting_buffer <= 0:
            output_scores.append((day.strftime('%a'), int(score_sum)))
        else:
            starting_buffer -= 1
    return output_scores


# TODO: rewrite
@app.route("/patientData", methods=["GET"])
def patient_data():
    recovered_cookie = request.cookies.get("phoneNumber")
    if recovered_cookie is None:
        return jsonify()  # empty response if no cookie
    phone_number = f"+11{recovered_cookie}"
    # blacklist my IPs to reduce data pollution
    # my IP might be changing, not sure.
    if request.remote_addr not in IP_BLACKLIST:
        log_event("patient_portal_load", phone_number, description=request.remote_addr)
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
    relevant_events = Event.query.filter(Event.event_type.in_(combined_list), Event.phone_number == phone_number).order_by(Event.event_time.asc()).all()
    dose_history_events = list(filter(lambda event: event.event_type in take_record_events and event.description in relevant_dose_ids_as_str, relevant_events))
    user_behavior_events = list(filter(lambda event: event.event_type in user_driven_events, relevant_events))
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


# TODO: rewrite
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

# TODO: rewrite
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


# TODO: rewrite
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
        if request.remote_addr not in IP_BLACKLIST:
            log_event("successful_login", phone_number_formatted, description=request.remote_addr)
        return out
    log_event("failed_login", phone_number_formatted)
    return jsonify(), 401

# TODO: rewrite
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

# TODO: rewrite
@app.route("/logout", methods=["GET"])
def logout():
    out = jsonify()
    out.set_cookie("phoneNumber", "", expires=0)
    return out

@app.route("/admin", methods=["GET"])
def admin_page():
    return app.send_static_file('admin.html')

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
@app.route("/dose", methods=["DELETE"])
@auth_required_post_delete
def delete_dose():
    incoming_data = request.json
    id_to_delete = int(incoming_data["id"])
    remove_jobs_helper(id_to_delete, ["boundary", "initial", "followup", "absent"])
    Dose.query.filter_by(id=id_to_delete).delete()
    db.session.commit()
    return jsonify()

# TODO: rewrite
@app.route("/reminder", methods=["DELETE"])
@auth_required_post_delete
def delete_reminder():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Reminder.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
@app.route("/events", methods=["DELETE"])
@auth_required_post_delete
def delete_event():
    incoming_data = request.json
    id_to_delete = incoming_data["id"]
    Event.query.filter_by(id=int(id_to_delete)).delete()
    db.session.commit()
    return jsonify()

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
def should_force_manual(phone_number):  # phone number format: +13604508655
    all_takeover = ManualTakeover.query.all()
    takeover_numbers = [mt.phone_number for mt in all_takeover]
    return f"+1{phone_number[1:]}" in takeover_numbers

def extract_integer(message):
    try:
        return int(message)
    except ValueError:
        return None

def convert_to_user_local_time(user_obj, dt):
    user_tz = timezone(user_obj.timezone)
    return user_tz.localize(dt.replace(tzinfo=None))

@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg_list = segment_message(request.values.get('Body', ''))
    incoming_phone_number = request.values.get('From', None)
    formatted_incoming_phone_number = f"+1{incoming_phone_number[1:]}"
    if "NEW_DATA_MODEL" in os.environ:
        standardized_incoming_phone_number = incoming_phone_number[2:]
        associated_users = User.query.filter(User.phone_number == standardized_incoming_phone_number).all()
        associated_user = None if len(associated_users) == 0 else associated_users[0]
        # the phone number is not in our system. we could consider sending a signup link
        if associated_user is None:
            log_event_new("unexpected_phone_number", None, None, None, description=standardized_incoming_phone_number)
            return jsonify(), 401
        overlapping_dose_windows = list(filter(lambda dw: dw.within_dosing_period(), associated_user.dose_windows))
        dose_window = None if len(overlapping_dose_windows) == 0 else overlapping_dose_windows[0]
        # we weren't able to parse any part of the message
        if len(incoming_msg_list) == 0:
            log_event_new("not_interpretable", associated_user.id, None if dose_window is None else dose_window.id, description=request.values.get('Body', ''))
            text_fallback(incoming_phone_number)
        for incoming_msg in incoming_msg_list:
            if associated_user.manual_takeover:
                log_event_new("manually_silenced", associated_user.id, None if dose_window is None else dose_window.id, description=incoming_msg["raw"])
                text_fallback(incoming_phone_number)
            else:
                if incoming_msg["type"] == "take":
                    if dose_window is not None:
                        associated_doses = dose_window.medications
                        doses_not_recorded = list(filter(
                            lambda dose: not dose.is_recorded_for_today(dose_window, associated_user),
                            associated_doses
                        ))
                        if len(doses_not_recorded) == 0: # all doses already recorded.
                            for dose in associated_doses:
                                log_event_new("attempted_rerecord", associated_user.id, dose_window.id, dose.id, description=incoming_msg["raw"])
                            client.messages.create(
                                body=ALREADY_RECORDED,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:
                            # all doses not recorded, we record now
                            excited = incoming_msg["modifiers"]["emotion"] == "excited"
                            input_time = incoming_msg.get("payload")
                            outgoing_copy = get_take_message(excited, input_time=input_time)
                            for dose in associated_doses:
                                log_event_new("take", associated_user.id, dose_window.id, dose.id, description=dose.id, event_time=input_time)
                            # text patient confirmation
                            client.messages.create(
                                body=outgoing_copy,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", associated_user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                elif incoming_msg["type"] == "skip":
                    if dose_window is not None:
                        associated_doses = dose_window.medications
                        doses_not_recorded = list(filter(
                            lambda dose: not dose.is_recorded_for_today(dose_window, associated_user),
                            associated_doses
                        ))
                        if len(doses_not_recorded) == 0: # all doses already recorded.
                            for dose in associated_doses:
                                log_event_new("attempted_rerecord", associated_user.id, dose_window.id, dose.id, description=incoming_msg["raw"])
                            client.messages.create(
                                body=ALREADY_RECORDED,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:
                            # all doses not recorded, we record now
                            input_time = incoming_msg.get("payload")
                            for dose in associated_doses:
                                log_event_new("skip", associated_user.id, dose_window.id, dose.id, description=dose.id, event_time=input_time)
                            # text patient confirmation
                            client.messages.create(
                                body=SKIP_MSG,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", associated_user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                elif incoming_msg["type"] == "special":  # TODO: start here
                    if incoming_msg["payload"] == "x":
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
                        log_event_new("user_reported_error", associated_user.id, None if dose_window is None else dose_window.id, None)
                    elif incoming_msg["payload"] in ["1", "2", "3"]:
                        if dose_window is not None:
                            associated_doses = dose_window.medications
                            message_delays = {
                                "1": timedelta(minutes=10),
                                "2": timedelta(minutes=30),
                                "3": timedelta(hours=1)
                            }
                            log_event_new("requested_time_delay", associated_user.id, dose_window.id, None, description=f"{message_delays[incoming_msg['payload']]}")
                            next_alarm_time = get_time_now() + message_delays[incoming_msg["payload"]]
                            too_close = False
                            dose_end_time = dose_window.next_end_date - timedelta(days=1)
                            if next_alarm_time > dose_end_time - timedelta(minutes=10):
                                next_alarm_time = dose_end_time - timedelta(minutes=10)
                                too_close = True
                            if next_alarm_time > get_time_now():
                                log_event_new("reminder_delay", associated_user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(associated_user.timezone))}")
                                client.messages.create(
                                    body=REMINDER_TOO_CLOSE_MSG.substitute(
                                        time=dose_end_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M"),
                                        reminder_time=next_alarm_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                    ),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                                remove_jobs_helper(dose_window.id, ["followup", "absent"])
                                scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                    args=[dose_window, associated_user],
                                    trigger="date",
                                    run_date=next_alarm_time,
                                    misfire_grace_time=5*60
                                )
                            else:
                                client.messages.create(
                                    body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M")),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                        else:
                            log_event_new("out_of_range", associated_user.id, None, None, description=incoming_msg["raw"])
                            client.messages.create(
                                body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                if incoming_msg["type"] == "delay_minutes":
                    if dose_window is not None:
                        minute_delay = incoming_msg["payload"]
                        log_event_new("requested_time_delay", associated_user.id, dose_window.id, None, description=f"{timedelta(minutes=minute_delay)}")
                        next_alarm_time = get_time_now() + timedelta(minutes=minute_delay)
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", associated_user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(associated_user.timezone))}")
                            client.messages.create(
                                body=REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"])
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window, associated_user],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(associated_user.timezone)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", associated_user.id, dose_window.id, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "requested_alarm_time":
                    if dose_window is not None:
                        next_alarm_time = convert_to_user_local_time(associated_user, incoming_msg["payload"])
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", associated_user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body=REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"])
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window, associated_user],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", associated_user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "activity":
                    if dose_window is not None:
                        log_event_new("activity", associated_user.id, dose_window.id, None, description=incoming_msg["raw"])
                        next_alarm_time = get_time_now() + (timedelta(minutes=random.randint(10, 30)) if incoming_msg["payload"]["type"] == "short" else timedelta(minutes=random.randint(30, 60)))
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", associated_user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body=incoming_msg["payload"]["response"],
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"])
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window, associated_user],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", associated_user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "thanks":
                    log_event_new("conversational", associated_user.id, None, None, description=incoming_msg["raw"])
                    client.messages.create(
                        body=get_thanks_message(),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
    else:
        # we weren't able to parse any part of the message
        if len(incoming_msg_list) == 0:
            log_event("not_interpretable", formatted_incoming_phone_number, description=request.values.get('Body', ''))
            text_fallback(incoming_phone_number)
        # grab all relevant dose info for the incoming text
        doses = Dose.query.filter_by(phone_number=formatted_incoming_phone_number).all()  # +113604508655
        dose_ids = [dose.id for dose in doses]
        latest_reminder_record = Reminder.query \
            .filter(Reminder.dose_id.in_(dose_ids)) \
            .order_by(Reminder.send_time.desc()) \
            .first()
        latest_dose_id = None if latest_reminder_record is None else latest_reminder_record.dose_id
        matching_dose_list = list(filter(lambda dose: dose.id == latest_dose_id, doses))
        latest_dose = matching_dose_list[0] if len(matching_dose_list) > 0 else None
        for incoming_msg in incoming_msg_list:
            # if manually taken over, silence all automated outgoing responses and notify admin
            if should_force_manual(incoming_phone_number):
                log_event("manually_silenced", formatted_incoming_phone_number, description=incoming_msg["raw"])
                text_fallback(incoming_phone_number)
            else:
                if incoming_msg["type"] == "take":
                    if latest_dose is not None and latest_dose.within_dosing_period():
                        excited = incoming_msg["modifiers"]["emotion"] == "excited"
                        input_time = incoming_msg.get("payload")
                        # input_time = datetime.strptime(incoming_msg.get("payload"), "%Y-%m-%d %H:%M:%S-")
                        outgoing_copy = get_take_message(excited, input_time=input_time)
                        log_event("take", formatted_incoming_phone_number, description=latest_dose_id, event_time=input_time)
                        # text patient confirmation
                        client.messages.create(
                            body=outgoing_copy,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                        # remove future reminders
                        remove_jobs_helper(latest_dose_id, ["absent", "followup", "boundary"])
                    else:
                        log_event("out_of_range", formatted_incoming_phone_number, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                elif incoming_msg["type"] == "skip":
                    if latest_dose is not None and latest_dose.within_dosing_period():
                        log_event("skip", formatted_incoming_phone_number, description=latest_dose_id)
                        client.messages.create(
                            body=SKIP_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                        remove_jobs_helper(latest_dose_id, ["absent", "followup", "boundary"])
                    else:
                        log_event("out_of_range", formatted_incoming_phone_number, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                elif incoming_msg["type"] == "special":
                    if incoming_msg["payload"] == "x":
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
                        log_event("user_reported_error", formatted_incoming_phone_number)
                    if incoming_msg["payload"] in ["1", "2", "3"]:
                        if latest_dose is not None and latest_dose.within_dosing_period():
                            message_delays = {
                                "1": timedelta(minutes=10),
                                "2": timedelta(minutes=30),
                                "3": timedelta(hours=1)
                            }
                            dose_end_time = get_current_end_date(latest_dose_id)
                            log_event("requested_time_delay", formatted_incoming_phone_number, description=f"{message_delays[incoming_msg['payload']]}")
                            next_alarm_time = get_time_now() + message_delays[incoming_msg["payload"]]
                            # TODO: remove repeated code block
                            too_close = False
                            if next_alarm_time > dose_end_time - timedelta(minutes=10):
                                next_alarm_time = dose_end_time - timedelta(minutes=10)
                                too_close = True
                            if next_alarm_time > get_time_now():
                                log_event("reminder_delay", formatted_incoming_phone_number, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                                client.messages.create(
                                    body=REMINDER_TOO_CLOSE_MSG.substitute(
                                        time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                                        reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                    ),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                                remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                                scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                                    args=[latest_dose_id],
                                    trigger="date",
                                    run_date=next_alarm_time,
                                    misfire_grace_time=5*60
                                )
                            else:
                                client.messages.create(
                                    body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                        else:
                            log_event("out_of_range", f"+1{incoming_phone_number[1:]}", description=incoming_msg["raw"])
                            client.messages.create(
                                body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                if incoming_msg["type"] == "delay_minutes":
                    if latest_dose is not None and latest_dose.within_dosing_period():
                        dose_end_time = get_current_end_date(latest_dose_id)
                        minute_delay = incoming_msg["payload"]
                        log_event("requested_time_delay", formatted_incoming_phone_number, description=f"{timedelta(minutes=minute_delay)}")
                        next_alarm_time = get_time_now() + timedelta(minutes=minute_delay)
                        # TODO: remove repeated code block
                        too_close = False
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event("reminder_delay", formatted_incoming_phone_number, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body= REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                            scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                                args=[latest_dose_id],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event("out_of_range", f"+1{incoming_phone_number[1:]}", description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "requested_alarm_time":
                    if latest_dose is not None and latest_dose.within_dosing_period():
                        dose_end_time = get_current_end_date(latest_dose_id)
                        next_alarm_time = incoming_msg["payload"]
                        # TODO: remove repeated code block
                        too_close = False
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event("reminder_delay", formatted_incoming_phone_number, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body= REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                            scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                                args=[latest_dose_id],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event("out_of_range", f"+1{incoming_phone_number[1:]}", description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "activity":
                    log_event("activity", formatted_incoming_phone_number, description=incoming_msg["raw"])
                    if latest_dose is not None and latest_dose.within_dosing_period():
                        dose_end_time = get_current_end_date(latest_dose_id)
                        next_alarm_time = get_time_now() + (timedelta(minutes=random.randint(10, 30)) if incoming_msg["payload"]["type"] == "short" else timedelta(minutes=random.randint(30, 60)))
                        # TODO: remove repeated code block
                        too_close = False
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event("reminder_delay", formatted_incoming_phone_number, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body=incoming_msg["payload"]["response"],
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(latest_dose_id, ["followup", "absent"])
                            scheduler.add_job(f"{latest_dose_id}-followup", send_followup_text,
                                args=[latest_dose_id],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event("out_of_range", formatted_incoming_phone_number)
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "thanks":
                    log_event("conversational", formatted_incoming_phone_number, description=latest_dose_id)
                    client.messages.create(
                        body=get_thanks_message(),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
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

# TODO: rewrite
@app.route("/manual", methods=["POST"])
@auth_required_post_delete
def manual_send():
    incoming_data = request.json
    dose_id = int(incoming_data["doseId"])
    reminder_type = incoming_data["reminderType"]
    manual_time = incoming_data["manualTime"]
    if not manual_time:
        if reminder_type == "absent":
            send_absent_text(dose_id)
        elif reminder_type == "followup":
            send_followup_text(dose_id)
        elif reminder_type == "initial":
            send_intro_text(dose_id)
    else:
        event_time_obj = datetime.strptime(manual_time, "%Y-%m-%dT%H:%M")
        if os.environ["FLASK_ENV"] != "local":
            event_time_obj += timedelta(hours=7)  # HACK to transform to UTC
        if reminder_type == "absent":
            scheduler.add_job(f"{dose_id}-absent", send_absent_text,
                args=[dose_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
        elif reminder_type == "followup":
            scheduler.add_job(f"{dose_id}-followup", send_followup_text,
                args=[dose_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
        elif reminder_type == "initial":
            scheduler.add_job(f"{dose_id}-initial", send_intro_text,
                args=[dose_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
    return jsonify()

# TODO: rewrite
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

# TODO: rewrite
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

# TODO: rewrite
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

# NEW
def maybe_schedule_absent_new(dose_window_obj):
    end_date = dose_window_obj.id.next_end_date - timedelta(days=1)
    desired_absent_reminder = min(get_time_now() + timedelta(minutes=random.randint(45,75)), end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > get_time_now():
        scheduler.add_job(f"{dose_window_obj.id}-absent", send_absent_text,
            args=[dose_window_obj.id],
            trigger="date",
            run_date=desired_absent_reminder,
            misfire_grace_time=5*60
        )

def remove_jobs_helper(dose_id, jobs_list):
    for job in jobs_list:
        job_id = f"{dose_id}-{job}-new" if "NEW_DATA_MODEL" in os.environ else f"{dose_id}-{job}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)


def exists_remaining_reminder_job(dose_id, job_list):
    for job in job_list:
        if scheduler.get_job(f"{dose_id}-{job}"):
            return True
    return False

# TODO: deprecate
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

# NEW
def send_followup_text_new(dose_window_obj, user_obj):
    client.messages.create(
        body=get_followup_message(),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{user_obj.phone_number}"
    )
    reminder_record = EventLog(
        event_type="followup",
        user_id=user_obj.id,
        dose_window_id=dose_window_obj.id,
        medication_id=None,
        event_time=get_time_now()
    )
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"])
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("followup", user_obj.id, dose_window_obj.id, medication_id=None)

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

# NEW
def send_absent_text_new(dose_window_obj, user_obj):
    client.messages.create(
        body=get_absent_message(),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{user_obj.phone_number}"
    )
    reminder_record = EventLog(
        event_type="absent",
        user_id=user_obj.id,
        dose_window_id=dose_window_obj.id,
        medication_id=None,
        event_time=get_time_now()
    )
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"])
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("absent", user_obj.id, dose_window_obj.id, medication_id=None)

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

# NEW
def send_boundary_text_new(dose_window_obj, user_obj):
    client.messages.create(
        body=CLINICAL_BOUNDARY_MSG.substitute(time=get_time_now().astimezone(timezone(user_obj.timezone)).strftime('%I:%M')) if user_obj.phone_number in CLINICAL_BOUNDARY_PHONE_NUMBERS else BOUNDARY_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{user_obj.phone_number}"
    )
    reminder_record = EventLog(
        event_type="boundary",
        user_id=user_obj.id,
        dose_window_id=dose_window_obj.id,
        medication_id=None,
        event_time=get_time_now()
    )
    db.session.add(reminder_record)
    db.session.commit()
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"])
    log_event_new("boundary", user_obj.id, dose_window_obj.id, medication_id=None)

def send_intro_text(dose_id, manual=False, welcome_back=False):
    dose_obj = Dose.query.get(dose_id)
    client.messages.create(
        body=f"{get_initial_message(dose_id, get_time_now().astimezone(timezone(USER_TIMEZONE)).strftime('%I:%M'), welcome_back, dose_obj.phone_number)}{ACTION_MENU}",
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

# NEW
def send_intro_text_new(dose_window_obj, user_obj, manual=False, welcome_back=False):
    client.messages.create(
        body=f"{get_initial_message(dose_window_obj.id, get_time_now().astimezone(timezone(user_obj.timezone)).strftime('%I:%M'), welcome_back, user_obj.phone_number)}{ACTION_MENU}",
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{user_obj.phone_number}"
    )
    reminder_record = EventLog(
        event_type="initial",
        user_id=user_obj.id,
        dose_window_id=dose_window_obj.id,
        medication_id=None,
        event_time=get_time_now()
    )
    db.session.add(reminder_record)
    db.session.commit()
    scheduler.add_job(f"{dose_window_obj.id}-boundary", send_boundary_text_new,
        args=[dose_window_obj, user_obj],
        trigger="date",
        run_date=dose_window_obj.next_end_date if manual else dose_window_obj.next_end_date - timedelta(days=1),  # HACK, assumes this executes after start_date
        misfire_grace_time=5*60
    )
    maybe_schedule_absent_new(dose_window_obj)

def scheduler_error_alert(event):
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=f"Scheduler reports job missed for event ID {event.job_id}.",
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to="+13604508655"
        )

# user methods
@app.route("/user/create", methods=["POST"])
@auth_required_post_delete
def create_user():
    incoming_data = request.json
    new_user = User(
        phone_number=incoming_data["phoneNumber"],
        name=incoming_data["name"],
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify()

@app.route("/user/everything", methods=["GET"])
@auth_required_get
def get_all_data_for_user():
    user = User.query.get(int(request.args.get("userId")))
    if user is None:
        return jsonify(), 400
    user_schema = UserSchema()
    return jsonify(user_schema.dump(user))

@app.route("/user/togglePause", methods=["POST"])
@auth_required_post_delete
def pause_user():
    incoming_data = request.json
    user = User.query.get(incoming_data["userId"])
    if user is None:
        return jsonify(), 400
    user.paused = not user.paused
    db.session.commit()
    return jsonify()


@app.route("/user/manualTakeover", methods=["POST"])
@auth_required_post_delete
def toggle_manual_takeover_user():
    incoming_data = request.json
    user = User.query.get(incoming_data["userId"])
    if user is None:
        return jsonify(), 400
    user.manual_takeover = not user.manual_takeover
    db.session.commit()
    return jsonify()

# dose window methods
@app.route("/doseWindow/create", methods=["POST"])
@auth_required_post_delete
def create_dose_window():
    incoming_data = request.json
    create_for_all_days = "createForAllDays" in request.json
    if create_for_all_days:
        for i in range(7):
            new_dose_window = DoseWindow(
                i,
                int(incoming_data["startHour"]),
                int(incoming_data["startMinute"]),
                int(incoming_data["endHour"]),
                int(incoming_data["endMinute"]),
                int(incoming_data["userId"])
            )
            db.session.add(new_dose_window)
    else:
        new_dose_window = DoseWindow(
            int(incoming_data["dayOfWeek"]),
            int(incoming_data["startHour"]),
            int(incoming_data["startMinute"]),
            int(incoming_data["endHour"]),
            int(incoming_data["endMinute"]),
            int(incoming_data["userId"])
        )
        db.session.add(new_dose_window)
    db.session.commit()
    return jsonify()

@app.route("/doseWindow/update", methods=["POST"])
@auth_required_post_delete
def update_dose_window():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    dose_window = DoseWindow.query.get(dose_window_id)
    if dose_window is None:
        return jsonify(), 400
    dose_window.start_hour = int(incoming_data["startHour"])
    dose_window.start_minute = int(incoming_data["startMinute"])
    dose_window.end_hour = int(incoming_data["endHour"])
    dose_window.end_minute = int(incoming_data["endMinute"])
    db.session.commit()

@app.route("/doseWindow/addMedication", methods=["POST"])
@auth_required_post_delete
def associate_medication_with_dose_window_route():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    medication_id = int(incoming_data["medicationId"])
    dose_window = DoseWindow.query.get(dose_window_id)
    medication = Medication.query.get(medication_id)
    if dose_window is None or medication is None:
        return jsonify(), 400
    dose_window.medications.append(medication)
    db.session.commit()
    return jsonify()

@app.route("/doseWindow/removeMedication", methods=["POST"])
@auth_required_post_delete
def disassociate_medication_with_dose_window_route():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    medication_id = int(incoming_data["medicationId"])
    dose_window = DoseWindow.query.get(dose_window_id)
    medication = Medication.query.get(medication_id)
    if dose_window is None or medication is None:
        return jsonify(), 400
    dose_window.medications.append(medication)
    db.session.commit()
    return jsonify()

# medication methods
@app.route("/medication/create", methods=["POST"])
@auth_required_post_delete
def create_medication():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    dose_window = DoseWindow.query.get(dose_window_id)
    if dose_window is None:
        return jsonify(), 400
    new_medication = Medication(
        int(incoming_data["userId"]),
        incoming_data["medicationName"],
        incoming_data.get("instructions"),
        dose_windows=[dose_window]  # initialize with a dose window
    )
    db.session.add(new_medication)
    db.session.commit()
    return jsonify()

@app.route("/medication/update", methods=["POST"])
@auth_required_post_delete
def update_medication():
    incoming_data = request.json
    medication_id = int(incoming_data["medicationId"])
    medication = Medication.query.get(medication_id)
    if medication is None:
        return jsonify(), 400
    medication.name = incoming_data["medicationName"]
    medication.instructions = incoming_data["medicationInstructions"]
    db.session.commit()
    return jsonify()


PHONE_NUMBERS_TO_PORT = [
    "3604508655"
]


# TODO: testing
def port_legacy_data(phone_numbers_to_port, names, patient_dose_map):
    for phone_number in phone_numbers_to_port:
        # initialize users to paused for now to protect scheduler DB
        user_obj = User(phone_number, names[f"+11{phone_number}"], paused=True)
        db.session.add(user_obj)
        db.session.flush()  # populate user_id
        formatted_phone_number = f"+11{phone_number}"
        doses = Dose.query.filter(Dose.phone_number == formatted_phone_number).all()
        events_for_user = Event.query.filter(Event.phone_number == formatted_phone_number).all()
        for dose in doses:
            dose_id_equivalency_list = []
            for _, equivalency_list in patient_dose_map[formatted_phone_number].items():
                if dose.id in equivalency_list:
                    dose_id_equivalency_list = equivalency_list
            dose_id_equivalency_list_str = [str(x) for x in dose_id_equivalency_list]
            medication_names = dose.medication_name.split(", ")
            dose_window_obj = DoseWindow(
                dose.start_hour,
                dose.start_minute,
                dose.end_hour,
                dose.end_minute,
                user_obj.id
            )
            db.session.add(dose_window_obj)
            db.session.flush()
            medication_obj_list = []
            for medication_name in medication_names:
                medication_obj = Medication(
                    user_obj.id, medication_name,
                    dose_windows=[dose_window_obj]
                )
                db.session.add(medication_obj)
                medication_obj_list.append(medication_obj)
            db.session.flush()
            events_for_dose = filter(
                lambda event: event.description in dose_id_equivalency_list_str,
                events_for_user
            )
            for event in events_for_dose:
                for medication in medication_obj_list:
                    corresponding_event = EventLog(
                        event.event_type,
                        user_obj.id,
                        dose_window_obj.id,
                        medication.id,
                        event.event_time,
                        description=None
                    )
                    db.session.add(corresponding_event)
        non_dose_associated_events = filter(
            lambda event: event.description not in dose_id_equivalency_list_str,
            events_for_user
        )
        for event in non_dose_associated_events:
            corresponding_event = EventLog(
                event.event_type,
                user_obj.id,
                None,
                None,
                event.event_time,
                description=event.description
            )
            db.session.add(corresponding_event)
    db.session.commit()


scheduler.add_listener(scheduler_error_alert, EVENT_JOB_MISSED | EVENT_JOB_ERROR)
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0')