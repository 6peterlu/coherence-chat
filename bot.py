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
    Online,
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
    REQUEST_WEBSITE,
    SECRET_CODE_MESSAGE,
    SKIP_MSG,
    SUGGEST_DOSE_WINDOW_CHANGE,
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


PATIENT_DOSE_MAP = {
    "+113604508655": {"morning": [85]},
    "+113609042210": {"afternoon": [25], "evening": [15]},
    "+113609049085": {"evening": [16]},
    "+114152142478": {"morning": [26, 82, 92]},
    "+116502690598": {"evening": [27]},
    "+118587761377": {"morning": [29]},
    "+113607738908": {"morning": [68, 87], "evening": [69, 81]},
    "+115038871884": {"morning": [70], "afternoon": [71]},
    "+113605214193": {"morning": [72], "evening": [74, 103]},
    "+113605131225": {"morning": [75], "afternoon": [76], "evening": [77]},
    "+113606064445": {"afternoon": [78, 88]},
    "+113609010956": {"evening": [86]}
}

PATIENT_NAME_MAP = {
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

SECRET_CODES = {
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
# maybe we don't run this?
# db.create_all()  # are there bad effects from running this every time? edit: I guess not

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

def get_take_message_new(excited, user_obj, input_time=None):
    datestring = get_time_now().astimezone(timezone(user_obj.timezone)).strftime('%b %d, %I:%M %p') if input_time is None else input_time.strftime('%b %d, %I:%M %p')
    return TAKE_MSG_EXCITED.substitute(time=datestring) if excited else TAKE_MSG.substitute(time=datestring)

def get_absent_message():
    return random.choice(ABSENT_MSGS)

def get_thanks_message():
    return random.choice(THANKS_MESSAGES)


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


def generate_behavior_learning_scores_new(user_behavior_events, user):
    # end time is end of yesterday.
    end_time = get_time_now().astimezone(timezone(user.timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    user_behavior_events_until_today = list(filter(lambda event: event.aware_event_time < end_time, user_behavior_events))
    if len(user_behavior_events_until_today) == 0 or len(user.doses) == 0:
        return {}
    behavior_scores_by_day = {}
    # starts at earliest day
    current_day_bucket = user_behavior_events_until_today[0].aware_event_time.astimezone(timezone(user.timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
    # latest_day = user_behavior_events_until_today[len(user_behavior_events_until_today) - 1].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
    while current_day_bucket < end_time:
        current_day_events = list(filter(lambda event: event.aware_event_time < current_day_bucket + timedelta(days=1) and event.aware_event_time > current_day_bucket, user_behavior_events_until_today))
        current_day_take_skip = list(filter(lambda event: event.event_type in ["take", "skip"], current_day_events))
        unique_time_buckets = []
        for k, _ in groupby([event.event_time for event in current_day_events], round_date):
            unique_time_buckets.append(k)
        behavior_score_for_day = len(current_day_take_skip) * 3 / len(user.doses) + len(unique_time_buckets) * 2 / len (user.doses) - 3
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


def get_current_user_and_dose_window(truncated_phone_number):
    user = None
    current_dose_window = None
    user = User.query.filter(User.phone_number == truncated_phone_number).one_or_none()
    if user is not None:
        for dose_window in user.dose_windows:
            if dose_window.within_dosing_period():
                current_dose_window = dose_window
    return user, current_dose_window


def get_time_of_day(dose_window_obj):
    if dose_window_obj is None:
        return None
    user = dose_window_obj.user
    local_start_date = dose_window_obj.next_start_date.astimezone(timezone(user.timezone))
    if local_start_date.hour > 2 and local_start_date.hour < 12:
        return "morning"
    elif local_start_date.hour >= 12 and local_start_date.hour < 18:
        return "afternoon"
    return "evening"


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
    user, dose_window = get_current_user_and_dose_window(recovered_cookie)
    if user is not None:
        if request.remote_addr not in IP_BLACKLIST: # blacklist my IPs to reduce data pollution, but not really working
            log_event_new("patient_portal_load", user.id, dose_window.id if dose_window else None, description=request.remote_addr)
        # grab data from user object
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
        relevant_events = EventLog.query.filter(EventLog.event_type.in_(combined_list), EventLog.user == user).order_by(EventLog.event_time.asc()).all()
        dose_history_events = list(filter(lambda event: event.event_type in take_record_events and event.medication in user.doses, relevant_events))
        user_behavior_events = list(filter(lambda event: event.event_type in user_driven_events, relevant_events))
        event_data_by_time = {}
        for event in dose_history_events:
            time_of_day = get_time_of_day(event.dose_window)
            if time_of_day not in event_data_by_time:
                event_data_by_time[time_of_day] = {"events": []}
            event_data_by_time[time_of_day]["events"].append(EventLogSchema().dump(event))
        for current_dose_window in user.dose_windows:
            event_data_by_time[get_time_of_day(current_dose_window)]["dose"] = DoseWindowSchema().dump(current_dose_window)
        paused_service = user.paused
        behavior_learning_scores = generate_behavior_learning_scores_new(user_behavior_events, user)
        dose_to_take_now = False if dose_window is None else not dose_window.is_recorded_for_today
        dose_windows = [DoseWindowSchema().dump(dw) for dw in user.dose_windows]
        return jsonify({
            "phoneNumber": recovered_cookie,
            "eventData": event_data_by_time,
            "patientName": PATIENT_NAME_MAP[phone_number],
            "takeNow": dose_to_take_now,
            "pausedService": bool(paused_service),
            "behaviorLearningScores": behavior_learning_scores,
            "doseWindows": dose_windows
        })
    return jsonify(), 401


def send_pause_message(user):
    client.messages.create(
        body=PAUSE_MESSAGE,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+1{user.phone_number}"
    )

def send_upcoming_dose_message(user, dose_window):
    client.messages.create(
        body=f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(FUTURE_MESSAGE_SUFFIXES).substitute(time=dose_window.next_start_date.astimezone(timezone(user.timezone)).strftime('%I:%M %p'))}",
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+1{user.phone_number}"
    )


@app.route("/user/pause", methods=["POST"])
def pause_user():
    recovered_cookie = request.cookies.get("phoneNumber")
    user, _ = get_current_user_and_dose_window(recovered_cookie)
    user.pause(scheduler, send_pause_message)


@app.route("/user/resume", methods=["POST"])
def resume_user():
    recovered_cookie = request.cookies.get("phoneNumber")
    user, _ = get_current_user_and_dose_window(recovered_cookie)
    user.resume(scheduler, send_intro_text_new, send_upcoming_dose_message)


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
            user, _ = get_current_user_and_dose_window(phone_number)
            log_event_new("successful_login", user.id, None, None, description=request.remote_addr)
        return out
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
        if "NOALERTS" not in os.environ:
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
def new_admin_page():
    return app.send_static_file('new_admin.html')


@app.route("/admin/messages", methods=["GET"])
def admin_get_messages_for_number():
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


@app.route("/admin/online", methods=["POST"])
def admin_online_toggle():
    online_status = get_online_status()
    if online_status:  # is online, we need to clear manual takeover on going offline
        all_users = User.query.filter(User.manual_takeover.is_(True)).all()
        for user in all_users:
            user.manual_takeover = False
    online_record = Online.query.get(1)
    online_record.online = not online_status
    db.session.commit()
    return jsonify()

def extract_integer(message):
    try:
        return int(message)
    except ValueError:
        return None

def convert_to_user_local_time(user_obj, dt):
    user_tz = timezone(user_obj.timezone)
    return user_tz.localize(dt.replace(tzinfo=None))


@app.route("/admin/everything", methods=["GET"])
def get_all_admin_data():
    all_users_in_system = User.query.order_by(User.name).all()
    return_dict = {"users": []}
    for user in all_users_in_system:
        user_dict = {
            "user": UserSchema().dump(user),
            "dose_windows": [],
            "medications": []
        }
        for dose_window in user.dose_windows:
            dose_window_json = DoseWindowSchema().dump(dose_window)
            dose_window_json["action_required"] = not dose_window.is_recorded_for_today and dose_window.within_dosing_period()
            user_dict["dose_windows"].append(dose_window_json)
        for medication in user.doses:
            user_dict["medications"].append(MedicationSchema().dump(medication))
        return_dict["users"].append(user_dict)
    global_event_stream = EventLog.query.order_by(EventLog.event_time.desc()).limit(100).all()
    return_dict["events"] = [EventLogSchema().dump(event) for event in global_event_stream]
    return_dict["online"] = get_online_status()
    return jsonify(return_dict)


@app.route("/admin/manualTakeover", methods=["POST"])
def toggle_manual_takeover_for_user():
    user_id = int(request.json["userId"])
    user = User.query.get(user_id)
    if user is not None:
        user.manual_takeover = not user.manual_takeover
    db.session.commit()
    return jsonify()


def get_nearest_dose_window(input_time, user):
    for dose_window in user.dose_windows:
        if dose_window.within_dosing_period(input_time, day_agnostic=True):
            return dose_window, False  # not outside of dose window
    # dose window fuzzy matching
    nearest_dose_window = min(user.dose_windows, key=lambda dw: min(
        abs(dw.next_start_date - input_time),
        abs(dw.next_start_date - timedelta(days=1) - input_time),
        abs(dw.next_end_date - input_time),
        abs(dw.next_end_date - timedelta(days=1) - input_time)
    ))

    return nearest_dose_window, True

def get_most_recent_12_hour_time(input_time):
    now = get_time_now()
    most_recent_time = input_time
    # cycle forward
    while most_recent_time < now - timedelta(hours=12):
        most_recent_time += timedelta(hours=12)
    # cycle back
    while most_recent_time > now:
        most_recent_time -= timedelta(hours=12)
    return most_recent_time


@app.route('/bot', methods=['POST'])
def bot():
    incoming_msg_list = segment_message(request.values.get('Body', ''))
    incoming_phone_number = request.values.get('From', None)
    user, dose_window = get_current_user_and_dose_window(incoming_phone_number[2:])
    if user and not user.paused:
        # we weren't able to parse any part of the message
        if len(incoming_msg_list) == 0:
            log_event_new("not_interpretable", user.id, None if dose_window is None else dose_window.id, description=request.values.get('Body', ''))
            text_fallback(incoming_phone_number)
        for incoming_msg in incoming_msg_list:
            if user.manual_takeover:
                log_event_new("manually_silenced", user.id, None if dose_window is None else dose_window.id, description=incoming_msg["raw"])
                text_fallback(incoming_phone_number)
            else:
                if incoming_msg["type"] == "take":
                    # all doses not recorded, we record now
                    excited = incoming_msg["modifiers"]["emotion"] == "excited"
                    input_time = incoming_msg.get("payload")
                    dose_window_to_mark = None
                    out_of_range = False
                    if input_time is not None:
                        input_time = get_most_recent_12_hour_time(input_time)
                    else:
                        input_time = get_time_now()
                    dose_window_to_mark, out_of_range = get_nearest_dose_window(input_time, user) if dose_window is None else (dose_window, False)
                    print(dose_window_to_mark)
                    # dose_window_to_mark will never be None unless the user has no dose windows, but we'll handle that upstream
                    if dose_window_to_mark.is_recorded_for_today:
                        associated_doses = dose_window_to_mark.medications
                        for dose in associated_doses:
                            log_event_new("attempted_rerecord", user.id, dose_window_to_mark.id, dose.id, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ALREADY_RECORDED,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                    else: # we need to record the dose
                        for medication in dose_window_to_mark.medications:
                            log_event_new("take", user.id, dose_window_to_mark.id, medication.id, description=medication.id, event_time=input_time)
                        outgoing_copy = get_take_message_new(excited, user, input_time=input_time)
                        client.messages.create(
                            body=outgoing_copy,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                        if out_of_range:
                            client.messages.create(
                                body=SUGGEST_DOSE_WINDOW_CHANGE,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:  # not out of range, remove jobs
                            remove_jobs_helper(dose_window.id, ["absent", "followup", "boundary"], new=True)
                elif incoming_msg["type"] == "skip":
                    if dose_window is not None:
                        if dose_window.is_recorded_for_today:
                            associated_doses = dose_window.medications
                            for dose in associated_doses:
                                log_event_new("attempted_rerecord", user.id, dose_window.id, dose.id, description=incoming_msg["raw"])
                            client.messages.create(
                                body=ALREADY_RECORDED,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        else:
                            # all doses not recorded, we record now
                            input_time = incoming_msg.get("payload")
                            for dose in dose_window.medications:
                                log_event_new("skip", user.id, dose_window.id, dose.id, description=dose.id, event_time=input_time)
                            # text patient confirmation
                            client.messages.create(
                                body=SKIP_MSG,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["absent", "followup", "boundary"], new=True)
                    else:
                        log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG,
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
                        log_event_new("user_reported_error", user.id, None if dose_window is None else dose_window.id, None)
                    elif incoming_msg["payload"] in ["1", "2", "3"]:
                        if dose_window is not None:
                            associated_doses = dose_window.medications
                            message_delays = {
                                "1": timedelta(minutes=10),
                                "2": timedelta(minutes=30),
                                "3": timedelta(hours=1)
                            }
                            log_event_new("requested_time_delay", user.id, dose_window.id, None, description=f"{message_delays[incoming_msg['payload']]}")
                            next_alarm_time = get_time_now() + message_delays[incoming_msg["payload"]]
                            too_close = False
                            dose_end_time = dose_window.next_end_date - timedelta(days=1)
                            if next_alarm_time > dose_end_time - timedelta(minutes=10):
                                next_alarm_time = dose_end_time - timedelta(minutes=10)
                                too_close = True
                            if next_alarm_time > get_time_now():
                                log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(user.timezone))}")
                                client.messages.create(
                                    body=REMINDER_TOO_CLOSE_MSG.substitute(
                                        time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M"),
                                        reminder_time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                    ),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                                remove_jobs_helper(dose_window.id, ["followup", "absent"], new=True)
                                scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                    args=[dose_window.id],
                                    trigger="date",
                                    run_date=next_alarm_time,
                                    misfire_grace_time=5*60
                                )
                            else:
                                client.messages.create(
                                    body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                        else:
                            log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                            client.messages.create(
                                body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                if incoming_msg["type"] == "delay_minutes":
                    if dose_window is not None:
                        minute_delay = incoming_msg["payload"]
                        log_event_new("requested_time_delay", user.id, dose_window.id, None, description=f"{timedelta(minutes=minute_delay)}")
                        next_alarm_time = get_time_now() + timedelta(minutes=minute_delay)
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(user.timezone))}")
                            client.messages.create(
                                body=REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"], new=True)
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window.id],
                                trigger="date",
                                run_date=next_alarm_time,
                                misfire_grace_time=5*60
                            )
                        else:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                    else:
                        log_event_new("out_of_range", user.id, dose_window.id, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "requested_alarm_time":
                    if dose_window is not None:
                        next_alarm_time = convert_to_user_local_time(user, incoming_msg["payload"])
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body=REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")) if too_close else CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(USER_TIMEZONE)).strftime("%I:%M")
                                ),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"], new=True)
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window.id],
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
                        log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "activity":
                    if dose_window is not None:
                        log_event_new("activity", user.id, dose_window.id, None, description=incoming_msg["raw"])
                        next_alarm_time = get_time_now() + (timedelta(minutes=random.randint(10, 30)) if incoming_msg["payload"]["type"] == "short" else timedelta(minutes=random.randint(30, 60)))
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        # TODO: remove repeated code block
                        too_close = False
                        dose_end_time = dose_window.next_end_date - timedelta(days=1)
                        if next_alarm_time > dose_end_time - timedelta(minutes=10):
                            next_alarm_time = dose_end_time - timedelta(minutes=10)
                            too_close = True
                        if next_alarm_time > get_time_now():
                            log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(USER_TIMEZONE))}")
                            client.messages.create(
                                body=incoming_msg["payload"]["response"],
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                            remove_jobs_helper(dose_window.id, ["followup", "absent"], new=True)
                            scheduler.add_job(f"{dose_window.id}-followup-new", send_followup_text_new,
                                args=[dose_window.id],
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
                        log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                if incoming_msg["type"] == "thanks":
                    log_event_new("conversational", user.id, None, None, description=incoming_msg["raw"])
                    client.messages.create(
                        body=get_thanks_message(),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
                if incoming_msg["type"] == "website_request":
                    log_event_new("website_request", user.id, None, None, description=incoming_msg["raw"])
                    client.messages.create(
                        body=REQUEST_WEBSITE,
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


# TODO: unit test
@app.route("/admin/manual", methods=["POST"])
def manual_send_reminder():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    reminder_type = incoming_data["reminderType"]
    manual_time = incoming_data["manualTime"]
    if not manual_time:
        if reminder_type == "absent":
            send_absent_text_new(dose_window_id)
        elif reminder_type == "followup":
            send_followup_text_new(dose_window_id)
        elif reminder_type == "initial":
            send_intro_text_new(dose_window_id)
    else:
        event_time_obj = datetime.strptime(manual_time, "%Y-%m-%dT%H:%M")
        if os.environ["FLASK_ENV"] != "local":
            event_time_obj += timedelta(hours=7)  # HACK to transform to UTC
        if reminder_type == "absent":
            scheduler.add_job(f"{dose_window_id}-absent-new", send_absent_text_new,
                args=[dose_window_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
        elif reminder_type == "followup":
            scheduler.add_job(f"{dose_window_id}-followup-new", send_followup_text_new,
                args=[dose_window_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
        elif reminder_type == "initial":
            scheduler.add_job(f"{dose_window_id}-initial-new", send_intro_text_new,
                args=[dose_window_id],
                trigger="date",
                run_date=event_time_obj,  # HACK, assumes this executes after start_date
                misfire_grace_time=5*60
            )
    return jsonify()

@app.route("/admin/manual/event", methods=["POST"])
def admin_manually_create_event():
    incoming_data = request.json
    dose_window_id = int(incoming_data["doseWindowId"])
    event_type = incoming_data["eventType"]
    event_time_raw = incoming_data["manualTime"]
    dose_window = DoseWindow.query.get(dose_window_id)
    for medication in dose_window.medications:
        if not event_time_raw:
            log_event_new(event_type, dose_window.user.id, dose_window.id, medication.id)
        else:
            event_time_obj = datetime.strptime(event_time_raw, "%Y-%m-%dT%H:%M")
            if os.environ["FLASK_ENV"] != "local":
                event_time_obj += timedelta(hours=7)  # HACK to transform to UTC
            log_event_new(event_type, dose_window.user.id, dose_window.id, medication.id, event_time=event_time_obj)
    return jsonify()

@app.route("/admin/manual/event/delete", methods=["POST"])
def admin_manually_delete_event():
    event_id = int(request.json["eventId"])
    event_to_delete = EventLog.query.get(event_id)
    if event_to_delete:
        db.session.delete(event_to_delete)
        db.session.commit()
    return jsonify()

@app.route("/admin/text", methods=["POST"])
def admin_send_text():
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    text = incoming_data["text"]
    client.messages.create(
        body=text,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+1{target_phone_number}"
    )
    user, dose_window = get_current_user_and_dose_window(target_phone_number)
    log_event_new("manual_text", user.id, dose_window.id if dose_window else None)
    return jsonify()

@app.route("/admin/editDoseWindow", methods=["POST"])
def admin_edit_dose_window():
    incoming_data = request.json
    start_hour = int(incoming_data["startHour"])
    start_minute = int(incoming_data["startMinute"])
    end_hour = int(incoming_data["endHour"])
    end_minute = int(incoming_data["endMinute"])
    dose_window_id = int(incoming_data["doseWindowId"])
    relevant_dose_window = DoseWindow.query.get(dose_window_id)
    if relevant_dose_window is not None:
        relevant_dose_window.edit_window(start_hour,
            start_minute, end_hour, end_minute,
            scheduler, send_intro_text_new, send_boundary_text_new
        )
    return jsonify()

@app.route("/user/updateDoseWindow", methods=["POST"])
def user_edit_dose_window():
    incoming_data = request.json
    start_hour = incoming_data["startHour"]
    start_minute = incoming_data["startMinute"]
    end_hour = incoming_data["endHour"]
    end_minute = incoming_data["endMinute"]
    dose_window_id = incoming_data["doseWindowId"]
    relevant_dose_window = DoseWindow.query.get(dose_window_id)
    user_tz = timezone(relevant_dose_window.user.timezone)
    target_start_date = user_tz.localize(datetime(2012, 5, 12, start_hour, start_minute, 0, 0, tzinfo=None)).astimezone(pytzutc)
    target_end_date = user_tz.localize(datetime(2012, 5, 12, end_hour, end_minute, 0, 0, tzinfo=None)).astimezone(pytzutc)
    if relevant_dose_window is not None:
        log_event_new("edit_dose_window", relevant_dose_window.user.id, relevant_dose_window.id)
        relevant_dose_window.edit_window(target_start_date.hour,
            target_start_date.minute, target_end_date.hour, target_end_date.minute,
            scheduler, send_intro_text_new, send_boundary_text_new
        )
    return jsonify()

def get_online_status():
    online_record = Online.query.filter_by(id=1).one_or_none()
    if online_record is None:
        online_record = Online(online=False)
        db.session.add(online_record)
        db.session.commit()
    return online_record.online

# NEW
def maybe_schedule_absent_new(dose_window_obj):
    end_date = dose_window_obj.next_end_date - timedelta(days=1)
    desired_absent_reminder = min(get_time_now() + timedelta(minutes=random.randint(45,75)), end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > get_time_now():
        scheduler.add_job(f"{dose_window_obj.id}-absent-new", send_absent_text_new,
            args=[dose_window_obj.id],
            trigger="date",
            run_date=desired_absent_reminder,
            misfire_grace_time=5*60
        )

def remove_jobs_helper(dose_id, jobs_list, new=False):
    for job in jobs_list:
        job_id = f"{dose_id}-{job}-new" if new else f"{dose_id}-{job}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)


def exists_remaining_reminder_job(dose_id, job_list):
    for job in job_list:
        if scheduler.get_job(f"{dose_id}-{job}"):
            return True
    return False


# NEW
def send_followup_text_new(dose_window_obj_id):
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=get_followup_message(),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+11{dose_window_obj.user.phone_number}"
        )
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"], new=True)
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("followup", dose_window_obj.user.id, dose_window_obj.id, medication_id=None)


# NEW
def send_absent_text_new(dose_window_obj_id):
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    client.messages.create(
        body=get_absent_message(),
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{dose_window_obj.user.phone_number}"
    )
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"], new=True)
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("absent", dose_window_obj.user.id, dose_window_obj.id, medication_id=None)


# NEW
def send_boundary_text_new(dose_window_obj_id):
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    client.messages.create(
        body=CLINICAL_BOUNDARY_MSG.substitute(time=get_time_now().astimezone(timezone(dose_window_obj.user.timezone)).strftime('%I:%M')) if dose_window_obj.user.phone_number in CLINICAL_BOUNDARY_PHONE_NUMBERS else BOUNDARY_MSG,
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{dose_window_obj.user.phone_number}"
    )
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"], new=True)
    log_event_new("boundary", dose_window_obj.user.id, dose_window_obj.id, medication_id=None)


# NEW
def send_intro_text_new(dose_window_obj_id, manual=False, welcome_back=False):
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    client.messages.create(
        body=f"{get_initial_message(dose_window_obj.id, get_time_now().astimezone(timezone(dose_window_obj.user.timezone)).strftime('%I:%M'), welcome_back, dose_window_obj.user.phone_number)}{ACTION_MENU}",
        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
        to=f"+11{dose_window_obj.user.phone_number}"
    )
    scheduler.add_job(f"{dose_window_obj.id}-boundary-new", send_boundary_text_new,
        args=[dose_window_obj.id],
        trigger="date",
        run_date=dose_window_obj.next_end_date if manual else dose_window_obj.next_end_date - timedelta(days=1),  # HACK, assumes this executes after start_date
        misfire_grace_time=5*60
    )
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("initial", dose_window_obj.user.id, dose_window_obj.id)

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


scheduler.add_listener(scheduler_error_alert, EVENT_JOB_MISSED | EVENT_JOB_ERROR)
scheduler.init_app(app)
scheduler.start()

if __name__ == '__main__':
    app.run(host='0.0.0.0')