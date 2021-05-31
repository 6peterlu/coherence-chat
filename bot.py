from flask import Flask, request, jsonify, send_from_directory, g
from flask_cors import CORS
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
from itertools import groupby
from werkzeug.middleware.proxy_fix import ProxyFix
from models import (
    LandingPageSignup,
    LandingPageSignupSchema,
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
    EventLogSchema,
    # database object
    db,
    # enums
    UserState,
    UserSecondaryState
)

from nlp import segment_message, get_datetime_obj_from_string
from health_metrics import METRIC_LIST, process_health_metric_event_stream
from message_handlers import (
    active_state_message_handler,
    dose_window_times_requested_message_handler,
    dose_windows_requested_message_handler,
    intro_state_message_handler,
    log_event_new,
    maybe_schedule_absent_new,
    payment_requested_message_handler,
    remove_jobs_helper,
    send_absent_text_new,
    send_followup_text_new,
    timezone_requested_message_handler
)
from time_helpers import convert_naive_to_local_machine_time, get_start_of_day, get_time_now

from dateutil.relativedelta import relativedelta

from ai import get_reminder_time_within_range

from apscheduler.events import (
    EVENT_JOB_ERROR,
    EVENT_JOB_MISSED
)

from flask_httpauth import HTTPBasicAuth

from flask_apscheduler.auth import HTTPBasicAuth as SchedulerAuth

from werkzeug.exceptions import HTTPException

# payments
import stripe


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

import logging
from constants import (
    ABSENT_MSGS,
    ACTION_OUT_OF_RANGE_MSG,
    ALREADY_RECORDED,
    BLOOD_GLUCOSE_MESSAGE,
    BLOOD_PRESSURE_MESSAGE,
    BOUNDARY_MSG,
    CANCELLATION_RESPONSE,
    CLINICAL_BOUNDARY_MSG,
    CONFIRMATION_MSG,
    COULDNT_PARSE_DATE,
    COULDNT_PARSE_NUMBER,
    FUTURE_MESSAGE_SUFFIXES,
    INITIAL_MSGS,
    FOLLOWUP_MSGS,
    INITIAL_SUFFIXES,
    MANUAL_TEXT_NEEDED_MSG,
    ONBOARDING_COMPLETE,
    PASSWORD_UPDATED_MESSAGE,
    PAUSE_MESSAGE,
    PAUSE_RESPONSE_MESSAGE,
    PAYMENT_METHOD_FAILURE,
    REMINDER_OUT_OF_RANGE_MSG,
    REMINDER_TOO_CLOSE_MSG,
    REMINDER_TOO_LATE_MSG,
    RENEWAL_COMPLETE,
    REQUEST_DOSE_WINDOW_COUNT,
    REQUEST_DOSE_WINDOW_END_TIME,
    REQUEST_DOSE_WINDOW_START_TIME,
    REQUEST_WEBSITE,
    SECRET_CODE_MESSAGE,
    SERVER_ERROR_ALERT,
    SKIP_MSG,
    SUBSCRIPTION_EXPIRED_RESPONSE_MESSAGE,
    SUGGEST_DOSE_WINDOW_CHANGE,
    TAKE_MSG,
    TAKE_MSG_EXCITED,
    THANKS_MESSAGES,
    TIME_OF_DAY_PREFIX_MAP,
    UNKNOWN_MSG,
    ACTION_MENU,
    USER_CANCELLED_NOTIF,
    USER_ERROR_REPORT,
    USER_ERROR_RESPONSE,
    USER_PAYMENT_METHOD_FAIL_NOTIF,
    USER_RENEWED_NOTIF,
    USER_SIGNUP_NOTIF,
    USER_SUBSCRIBED_NOTIF,
    WEIGHT_MESSAGE,
    WELCOME_BACK_MESSAGES
)

# allow no reminders to be set within 10 mins of boundary
BUFFER_TIME_MINS = 10
ADMIN_TIMEZONE = "US/Pacific"
TWILIO_PHONE_NUMBERS = {
    "local": "2813771848",
    "production": "2673824152"
}

# numbers for which the person should NOT take it after the dose period.
CLINICAL_BOUNDARY_PHONE_NUMBERS = ["8587761377"]

ADMIN_PHONE_NUMBER = "3604508655"

ACTIVITY_BUCKET_SIZE_MINUTES = 10

logging.basicConfig()
logging.getLogger('apscheduler').setLevel(logging.DEBUG)

auth = HTTPBasicAuth()

# set configuration values
class Config(object):
    SCHEDULER_API_ENABLED = True
    SCHEDULER_AUTH = SchedulerAuth()
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
app = Flask(__name__, static_folder='./web/build', static_url_path='/')
app.config.from_object(Config())
app.wsgi_app = ProxyFix(app.wsgi_app)
CORS(app)



# sqlalchemy db
db.app = app
db.init_app(app)

# needed for first init after db erasure
# db.create_all()

# parse datetime calendar object
cal = parsedatetime.Calendar()

# twilio objects
account_sid = os.environ['TWILIO_ACCOUNT_SID']
auth_token = os.environ['TWILIO_AUTH_TOKEN']
client = Client(account_sid, auth_token)

# initialize scheduler
scheduler = APScheduler()


# set stripe API key
stripe.api_key = os.environ["STRIPE_API_KEY"]


def get_initial_message(dose_window_obj, time_string, welcome_back=False, phone_number=None):
    current_time_of_day = get_time_of_day(dose_window_obj)
    if welcome_back:
        return f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"
    random_choice = random.random()
    if random_choice < 0.8 or current_time_of_day is None:
        return random.choice(INITIAL_MSGS).substitute(time=time_string)
    else:
        return f"{random.choice(TIME_OF_DAY_PREFIX_MAP[current_time_of_day])} {random.choice(INITIAL_SUFFIXES).substitute(time=time_string)}"


@auth.verify_password
def verify_password(token, _):
    print("verifying pass")
    # first try to authenticate by token
    user = User.verify_auth_token(token)
    if not user:
        return False  # kick you to login screen
    g.user = user

    # side effect, update user status to subscription passed if time has passed
    # probably bad practice but i'm not sure if @before_request has a g.user object.
    # I don't see how it would
    if g.user.end_of_service is not None and get_time_now() > convert_naive_to_local_machine_time(g.user.end_of_service):
        if g.user.state in [UserState.ACTIVE, UserState.PAUSED]:
            g.user.state = UserState.SUBSCRIPTION_EXPIRED
            db.session.commit()
    return True


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

@app.errorhandler(404)
def not_found(_):
    print("404")
    return app.send_static_file('index.html')


@app.route("/css/<path:path>", methods=["GET"])
def serve_css(path):
    return send_from_directory('css', path)

@app.route("/svg/<path:path>", methods=["GET"])
def serve_svg(path):
    return send_from_directory('svg', path)




# send alert texts on exceptions
@app.errorhandler(HTTPException)
def handle_exception(e):
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=SERVER_ERROR_ALERT.substitute(code=e.code, name=e.name, description=e.description),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{ADMIN_PHONE_NUMBER}"
        )
    return e  # pass through


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


# def generate_behavior_learning_scores_new(user_behavior_events, user):
#     # end time is end of yesterday.
#     end_time = get_time_now().astimezone(timezone(user.timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
#     user_behavior_events_until_today = list(filter(lambda event: event.aware_event_time < end_time, user_behavior_events))
#     if len(user_behavior_events_until_today) == 0 or len(user.doses) == 0:
#         return {}
#     behavior_scores_by_day = {}
#     # starts at earliest day
#     current_day_bucket = user_behavior_events_until_today[0].aware_event_time.astimezone(timezone(user.timezone)).replace(hour=0, minute=0, second=0, microsecond=0)
#     # latest_day = user_behavior_events_until_today[len(user_behavior_events_until_today) - 1].aware_event_time.astimezone(timezone(USER_TIMEZONE)).replace(hour=0, minute=0, second=0, microsecond=0)
#     while current_day_bucket < end_time:
#         current_day_events = list(filter(lambda event: event.aware_event_time < current_day_bucket + timedelta(days=1) and event.aware_event_time > current_day_bucket, user_behavior_events_until_today))
#         current_day_take_skip = list(filter(lambda event: event.event_type in ["take", "skip"], current_day_events))
#         unique_time_buckets = []
#         for k, _ in groupby([event.event_time for event in current_day_events], round_date):
#             unique_time_buckets.append(k)
#         behavior_score_for_day = len(current_day_take_skip) * 3 / len(user.doses) + len(unique_time_buckets) * 2 / len (user.doses) - 3
#         behavior_scores_by_day[current_day_bucket] = behavior_score_for_day
#         current_day_bucket += timedelta(days=1)
#     score_sum = 0
#     starting_buffer = len(behavior_scores_by_day) - 7  # combine all data before last 7 days
#     output_scores = []
#     for day in behavior_scores_by_day:
#         score_sum += behavior_scores_by_day[day]
#         if score_sum < 0:
#             score_sum = 0
#         elif score_sum > 100:
#             score_sum = 100
#         if starting_buffer <= 0:
#             output_scores.append((day.strftime('%a'), int(score_sum)))
#         else:
#             starting_buffer -= 1
#     return output_scores


def get_current_user_and_dose_window(truncated_phone_number):
    user = None
    current_dose_window = None
    user = User.query.filter(User.phone_number == truncated_phone_number).one_or_none()
    if user is not None:
        for dose_window in user.active_dose_windows:
            if dose_window.within_dosing_period():
                current_dose_window = dose_window
    return user, current_dose_window


def translate_time_of_day(dt, user=None):
    utc_time = pytzutc.localize(dt)
    if user is not None:
        local_time = utc_time.astimezone(timezone(user.timezone))
    if local_time.hour > 2 and local_time.hour < 12:
        return "morning"
    elif local_time.hour >= 12 and local_time.hour < 18:
        return "afternoon"
    return "evening"


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


@app.route("/user/landingPageSignup", methods=["POST"])
def landing_page_signup():
    new_signup = LandingPageSignup(
        request.json["name"],
        request.json["phoneNumber"],
        request.json["email"],
        request.json["trialCode"]
    )
    db.session.add(new_signup)
    db.session.commit()
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=USER_SIGNUP_NOTIF.substitute(name=request.json["name"]),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{request.json['name']}"
        )
    return jsonify()

@app.route("/patientState", methods=["GET"])
@auth.login_required
def get_patient_state():
    return jsonify({"state": g.user.state.value})

@app.route("/patientData/new", methods=["GET"])
@auth.login_required
def auth_patient_data():
    user = g.user
    calendar_month = int(request.args.get("calendarMonth"))
    calendar_year = int(request.args.get("calendarYear"))
    impersonating = False
    if user.phone_number == ADMIN_PHONE_NUMBER:
        impersonating_phone_number = request.args.get("phoneNumber")
        if impersonating_phone_number is not None:
            impersonated_user = User.query.filter_by(phone_number=impersonating_phone_number).one_or_none()
            if impersonated_user is not None:
                user = impersonated_user
                impersonating = True
    dose_window = None
    for user_dose_window in user.active_dose_windows:
        if user_dose_window.within_dosing_period():
            dose_window = user_dose_window
    if not impersonating:
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
    health_metric_event_types = [f"hm_{name}" for name in METRIC_LIST]
    combined_list = list(set(take_record_events) | set(user_driven_events) | set(health_metric_event_types))
    print(EventLog.query.filter(EventLog.event_type == "hm_weight", EventLog.user == user).order_by(EventLog.event_time.asc()).all())
    relevant_events = EventLog.query.filter(EventLog.event_type.in_(combined_list), EventLog.user == user).order_by(EventLog.event_time.asc()).all()
    requested_time_window = (
        timezone(user.timezone).localize(datetime(calendar_year, calendar_month, 1, 4, tzinfo=None)).astimezone(pytzutc).replace(tzinfo=None),
        timezone(user.timezone).localize(datetime(calendar_year, calendar_month, 1, 4, tzinfo=None) + relativedelta(months=1)).astimezone(pytzutc).replace(tzinfo=None)  # christ
    )
    dose_history_events = list(filter(lambda event: (
        event.event_type in take_record_events and
        event.dose_window in user.dose_windows and
        event.event_time < requested_time_window[1] and
        event.event_time > requested_time_window[0]
        ), relevant_events))
    # user_behavior_events = list(filter(lambda event: event.event_type in user_driven_events, relevant_events))
    health_metric_events = list(filter(lambda event: event.event_type in health_metric_event_types, relevant_events))
    print(health_metric_events)
    event_data = []
    current_day = requested_time_window[0]
    while current_day < requested_time_window[1]:
        events_of_day = list(filter(
            lambda event: event.event_time < current_day + timedelta(days=1) and event.event_time > current_day,
            dose_history_events
        ))
        day_status = None
        daily_event_summary = {"time_of_day":{}}
        for event in events_of_day:
            time_of_day = translate_time_of_day(event.event_time, user=user)
            if time_of_day not in daily_event_summary["time_of_day"]:
                daily_event_summary["time_of_day"][time_of_day] = []
            if event.event_type == "boundary":
                day_status = "missed"
                daily_event_summary["time_of_day"][time_of_day].append({"type": "missed", "time": event.event_time})
            elif event.event_type == "skip":
                if day_status != "missed":
                    day_status = "skip"
                daily_event_summary["time_of_day"][time_of_day].append({"type": "skipped", "time": event.event_time})
            else:
                daily_event_summary["time_of_day"][time_of_day].append({"type": "taken", "time": event.event_time})
                if day_status is None:
                    day_status = "taken"
        daily_event_summary["day_status"] = day_status
        event_data.append(daily_event_summary)
        current_day += timedelta(days=1)

    paused_service = user.state != UserState.ACTIVE
    # behavior_learning_scores = generate_behavior_learning_scores_new(user_behavior_events, user)
    dose_to_take_now = False if dose_window is None else not dose_window.is_recorded()
    dose_windows = [DoseWindowSchema().dump(dw) for dw in sorted(user.active_dose_windows, key=lambda dw: dw.bounds_for_current_day[0])]  # sort by start time
    subscription_end_date = None
    if user.end_of_service is not None:
        if user.state == UserState.SUBSCRIPTION_EXPIRED:
            subscription_end_date = convert_naive_to_local_machine_time(user.end_of_service)
        else:
            subscription_end_date = convert_naive_to_local_machine_time(user.charge_date)
    return jsonify({
        "phoneNumber": user.phone_number,
        "eventData": event_data,
        "patientName": user.name,
        "patientId": user.id,
        "takeNow": dose_to_take_now,
        "pausedService": bool(paused_service),
        "state": user.state.value,
        "secondaryState": user.secondary_state.value if user.secondary_state else None,
        # "behaviorLearningScores": behavior_learning_scores,
        "doseWindows": dose_windows,
        "impersonateList": User.query.with_entities(User.name, User.phone_number).all() if user.phone_number == ADMIN_PHONE_NUMBER else None,
        "month": calendar_month,
        "impersonating": impersonating,
        "healthMetricData": process_health_metric_event_stream(health_metric_events, user.tracked_health_metrics),
        "subscriptionEndDate": subscription_end_date,
        "earlyAdopterStatus": bool(user.early_adopter),
        "timezone": user.timezone,
        "token": g.user.generate_auth_token().decode('ascii')  # refresh auth token
    })

@app.route("/doseWindow/update/new", methods=["POST"])
@auth.login_required
def update_dose_window_new():
    incoming_dw_data = request.json["updatedDoseWindow"]
    dose_window = None
    if "id" in incoming_dw_data:
        dose_window_id = int(incoming_dw_data["id"])
        dose_window = DoseWindow.query.get(dose_window_id)
    else:
        dose_window = DoseWindow(0, 0, 0, 0, g.user.id)  # if no id given, make a new one
        db.session.add(dose_window)
        new_med = Medication(g.user.id, "", dose_windows=[dose_window])
        db.session.add(new_med)
        db.session.commit()
    if dose_window is None:
        return jsonify(), 400
    dose_window.start_hour = int(incoming_dw_data["start_hour"])
    dose_window.start_minute = int(incoming_dw_data["start_minute"])
    dose_window.end_hour = int(incoming_dw_data["end_hour"])
    dose_window.end_minute = int(incoming_dw_data["end_minute"])
    db.session.commit()
    return jsonify()


@app.route("/doseWindow/deactivate/new", methods=["POST"])
@auth.login_required
def deactivate_dose_window_new():
    incoming_dw_id = int(request.json["doseWindowId"])
    dose_window = DoseWindow.query.get(incoming_dw_id)
    if dose_window is None:
        return jsonify(), 400
    dose_window.deactivate(scheduler)
    return jsonify()


@app.route("/user/pause/new", methods=["POST"])
@auth.login_required
def pause_user_new():
    g.user.pause(scheduler, send_pause_message)
    return jsonify()

@app.route("/user/resume/new", methods=["POST"])
@auth.login_required
def resume_user_new():
    g.user.resume(scheduler, send_intro_text_new, send_upcoming_dose_message)
    return jsonify()

@app.route("/user/healthMetrics/set", methods=["POST"])
@auth.login_required
def set_tracking_health_metric():
    metrics_to_track = request.json["metricList"]
    print(metrics_to_track)
    g.user.tracked_health_metrics = metrics_to_track
    db.session.commit()
    return jsonify()


def send_pause_message(user):
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=PAUSE_MESSAGE,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{user.phone_number}"
        )

def send_upcoming_dose_message(user, dose_window):
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=f"{random.choice(WELCOME_BACK_MESSAGES)} {random.choice(FUTURE_MESSAGE_SUFFIXES).substitute(time=dose_window.next_start_date.astimezone(timezone(user.timezone)).strftime('%I:%M %p'))}",
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{user.phone_number}"
        )


@app.route("/login/new", methods=["POST"])
def react_login():
    phone_number = request.json.get("phoneNumber")
    secret_code = request.json.get("secretCode")
    try:
        secret_code = int(secret_code)
    except ValueError:
        pass
    password = request.json.get("password")
    numeric_filter = filter(str.isdigit, phone_number)
    phone_number = "".join(numeric_filter)
    if len(phone_number) == 11 and phone_number[0] == "1":
        phone_number = phone_number[1:]
    print(phone_number)
    user = User.query.filter_by(phone_number=phone_number).one_or_none()
    if not user:
        return jsonify(), 401
    if user.verify_password(password):
        print("returning token")
        return jsonify({"token": user.generate_auth_token().decode('ascii'), "status": "success", "state": user.state.value}), 200  # return token
    if user.password_hash and password:
        return jsonify(), 401
    phone_number_formatted = f"+11{phone_number}"
    if not secret_code:
        if not user.password_hash:
            secret_code = random.randint(100000, 999999)
            if "NOALERTS" not in os.environ:
                client.messages.create(
                    body=SECRET_CODE_MESSAGE.substitute(code=secret_code),
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=phone_number_formatted
                )
            user.secret_text_code = secret_code
            db.session.commit()
            return jsonify({"status": "2fa"})
        else:
            return jsonify({"status": "password"})
    print(user.secret_text_code)
    print(secret_code)
    print(user.secret_text_code == secret_code)
    secret_code_verified = user.secret_text_code == secret_code
    if not secret_code_verified:
        print("failed here")
        return jsonify(), 401
    if not password:
        return jsonify({"status": "register"})
    user.set_password(password)
    return jsonify({"status": "success", "token": user.generate_auth_token().decode('ascii'), "state": user.state.value})

@app.route("/admin", methods=["GET"])
def new_admin_page():
    return app.send_static_file('new_admin.html')


@app.route("/admin/messages", methods=["GET"])
@auth.login_required
def admin_get_messages_for_number():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
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
            "date_sent": message.date_sent.astimezone(timezone(ADMIN_TIMEZONE)).strftime("%b %d, %I:%M%p")
        }
        for message in combined_list
    ]
    return jsonify(json_blob)


@app.route("/admin/online", methods=["POST"])
@auth.login_required
def admin_online_toggle():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
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
@auth.login_required
def get_all_admin_data():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    phone_number = request.args.get("phoneNumber")
    matching_users = User.query.filter(User.phone_number == phone_number).all()
    all_users_in_system = User.query.with_entities(User.name, User.phone_number, User.state).order_by(User.name).all()
    return_dict = {"users": []}
    for user in matching_users:  # always len 1
        user_dict = {
            "user": UserSchema().dump(user),
            "dose_windows": [],
            "medications": []
        }
        for dose_window in user.active_dose_windows:
            dose_window_json = DoseWindowSchema().dump(dose_window)
            dose_window_json["action_required"] = not dose_window.is_recorded() and dose_window.within_dosing_period()
            user_dict["dose_windows"].append(dose_window_json)
        for medication in user.doses:
            user_dict["medications"].append(MedicationSchema().dump(medication))
        return_dict["users"].append(user_dict)
    state_dict = {}
    phone_number_set = set()
    for user_tuple in all_users_in_system:
        if user_tuple[2].value not in state_dict:
            state_dict[user_tuple[2].value] = []
        state_dict[user_tuple[2].value].append({"name": user_tuple[0], "phone_number": user_tuple[1]})
        phone_number_set.add(user_tuple[1])
    global_event_stream = EventLog.query.order_by(EventLog.event_time.desc()).limit(100).all()
    return_dict["events"] = [EventLogSchema().dump(event) for event in global_event_stream]
    return_dict["online"] = get_online_status()
    return_dict["user_list_by_state"] = state_dict
    return_dict["signups"] = [LandingPageSignupSchema().dump(signup) for signup in list(filter(lambda s: s.phone_number not in phone_number_set, LandingPageSignup.query.order_by(LandingPageSignup.signup_time).all()))]
    return jsonify(return_dict)

@app.route("/admin/deleteSignupRecord", methods=["POST"])
@auth.login_required
def delete_signup_record():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    signup_record = LandingPageSignup.query.get(request.json.get("signupId"))
    db.session.delete(signup_record)
    db.session.commit()
    return jsonify()

@app.route("/admin/manualTakeover", methods=["POST"])
@auth.login_required
def toggle_manual_takeover_for_user():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    user_id = int(request.json["userId"])
    user = User.query.get(user_id)
    if user is not None:
        user.manual_takeover = not user.manual_takeover
        if user.manual_takeover:  # we took over a user, we have to go online.
            online_status = get_online_status()
            if not online_status:
                online_record = Online.query.first()
                online_record.online = True
        db.session.commit()
    return jsonify()

@app.route("/admin/pauseUser", methods=["POST"])
@auth.login_required
def admin_pause_user():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    user_id = int(request.json["userId"])
    user = User.query.get(user_id)
    if user is not None:
        user.pause(scheduler, send_pause_message, silent=True)
    return jsonify()


@app.route("/admin/resumeUser", methods=["POST"])
@auth.login_required
def admin_resume_user():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    user_id = int(request.json["userId"])
    user = User.query.get(user_id)
    if user is not None:
        user.resume(scheduler, send_intro_text_new, send_upcoming_dose_message, silent=True)
    return jsonify()


@app.route("/admin/setPendingAnnouncement", methods=["POST"])
@auth.login_required
def admin_set_pending_announcement():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    announcement = request.json["announcement"]
    user_id = request.json.get("userId")
    if user_id:
        users = [User.query.get(user_id)]
    else:
        users = User.query.all()
    for user in users:
        if not user.state == UserState.PAUSED:
            user.pending_announcement = announcement;
    db.session.commit()
    return jsonify()


# random helpers
def get_online_status():
    online_record = Online.query.filter_by(id=1).one_or_none()
    if online_record is None:
        print("online record was none, creating new")
        online_record = Online(online=False)
        db.session.add(online_record)
        db.session.commit()
        print("db commit finished")
    return online_record.online


# TODO: write tests
@app.route('/bot', methods=['POST'])
def bot():
    raw_message = request.values.get('Body', '')
    incoming_msg_list = segment_message(request.values.get('Body', ''))
    incoming_phone_number = request.values.get('From', None)
    user, dose_window = get_current_user_and_dose_window(incoming_phone_number[2:])
    if user:
        if user.end_of_service is not None:
            if get_time_now() > convert_naive_to_local_machine_time(user.end_of_service):
                if user.state in [UserState.ACTIVE, UserState.PAUSED]:
                    user.state = UserState.SUBSCRIPTION_EXPIRED
                    db.session.commit()
        print(f"current user state: {user.state}")
        if user.state == UserState.ACTIVE:
            active_state_message_handler(incoming_msg_list, user, dose_window, incoming_phone_number, raw_message)
        elif user.state == UserState.INTRO:
            intro_state_message_handler(user, incoming_phone_number, raw_message)
        elif user.state == UserState.DOSE_WINDOWS_REQUESTED:
            dose_windows_requested_message_handler(user, incoming_phone_number, raw_message)
        elif user.state == UserState.DOSE_WINDOW_TIMES_REQUESTED:
            dose_window_times_requested_message_handler(user, incoming_phone_number, raw_message)
        elif user.state == UserState.TIMEZONE_REQUESTED:
            timezone_requested_message_handler(user, incoming_phone_number, raw_message)
        elif user.state == UserState.PAYMENT_METHOD_REQUESTED:
            payment_requested_message_handler(user, incoming_phone_number, raw_message)
        elif user.state == UserState.PAUSED:
            client.messages.create(
                body=PAUSE_RESPONSE_MESSAGE,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
        elif user.state == UserState.SUBSCRIPTION_EXPIRED:
            client.messages.create(
                body=SUBSCRIPTION_EXPIRED_RESPONSE_MESSAGE,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
    return jsonify()


# TODO: unit test
@app.route("/admin/manual", methods=["POST"])
@auth.login_required
def manual_send_reminder():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
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
@auth.login_required
def admin_manually_create_event():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
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
@auth.login_required
def admin_manually_delete_event():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    event_id = int(request.json["eventId"])
    event_to_delete = EventLog.query.get(event_id)
    if event_to_delete:
        db.session.delete(event_to_delete)
        db.session.commit()
    return jsonify()

@app.route("/admin/text", methods=["POST"])
@auth.login_required
def admin_send_text():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    incoming_data = request.json
    target_phone_number = incoming_data["phoneNumber"]
    text = incoming_data["text"]
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=text,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{target_phone_number}"
        )
    user, dose_window = get_current_user_and_dose_window(target_phone_number)
    log_event_new("manual_text", user.id, dose_window.id if dose_window else None)
    return jsonify()

@app.route("/admin/editDoseWindow", methods=["POST"])
@auth.login_required
def admin_edit_dose_window():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
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

@app.route("/admin/createUser", methods=["POST"])
@auth.login_required
def admin_create_user():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    incoming_data = request.json
    phone_number = incoming_data["phoneNumber"]
    onboarding_type = incoming_data.get("onboardingType")
    name = incoming_data["name"]
    new_user = User(
        phone_number=phone_number,
        name=name,
        onboarding_type=onboarding_type,  # user starts with intro state
    )
    db.session.add(new_user)
    db.session.commit()
    return jsonify()

@app.route("/admin/createDoseWindow", methods=["POST"])
@auth.login_required
def admin_create_dose_window_and_medication_for_user():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    incoming_data = request.json
    user_id = int(incoming_data["userId"])
    if User.query.get(user_id) is not None:
        new_dw = DoseWindow(0,0,0,0,user_id)
        db.session.add(new_dw)
        new_med = Medication(user_id, "", dose_windows=[new_dw])
        db.session.add(new_med)
        db.session.commit()
    return jsonify()


@app.route("/admin/deactivateDoseWindow", methods=["POST"])
@auth.login_required
def admin_deactivate_dose_window():
    if g.user.phone_number != ADMIN_PHONE_NUMBER:
        return jsonify(), 401
    incoming_data = request.json
    dw_id = int(incoming_data["doseWindowId"])
    dw = DoseWindow.query.get(dw_id)
    if dw is not None:
        dw.deactivate(scheduler)
    return jsonify()


@app.route("/user/updateDoseWindow", methods=["POST"])
@auth.login_required
def user_edit_dose_window():
    incoming_data = request.json
    start_hour = incoming_data["startHour"]
    start_minute = incoming_data["startMinute"]
    end_hour = incoming_data["endHour"]
    end_minute = incoming_data["endMinute"]
    dose_window_id = incoming_data["doseWindowId"]
    relevant_dose_window = DoseWindow.query.get(dose_window_id)
    if relevant_dose_window.user.id != g.user.id:
        return jsonify(), 401
    user_tz = timezone(relevant_dose_window.user.timezone)
    # TODO: move tz conversion logic to time_helpers.py
    # TODO: stop hardcoding the day here, you're going to have daylight savings issues
    target_start_date = user_tz.localize(datetime(2012, 5, 12, start_hour, start_minute, 0, 0, tzinfo=None)).astimezone(pytzutc)
    target_end_date = user_tz.localize(datetime(2012, 5, 12, end_hour, end_minute, 0, 0, tzinfo=None)).astimezone(pytzutc)
    if relevant_dose_window is not None:
        log_event_new("edit_dose_window", relevant_dose_window.user.id, relevant_dose_window.id)
        relevant_dose_window.edit_window(target_start_date.hour,
            target_start_date.minute, target_end_date.hour, target_end_date.minute,
            scheduler, send_intro_text_new, send_boundary_text_new
        )
    return jsonify()

@app.route("/user/profile", methods=["GET"])
@auth.login_required
def get_user_profile():
    return jsonify(UserSchema().dump(g.user))

@app.route("/user/updateTimezone", methods=["POST"])
@auth.login_required
def update_user_timezone():
    # first, check if user timezone changed
    if request.json["timezone"] != g.user.timezone:
        for dw in g.user.active_dose_windows:
            # get original alarm time
            dw_start_time = timezone(request.json["timezone"]).localize(get_time_now().replace(hour=dw.start_hour, minute=dw.start_minute).astimezone(timezone(g.user.timezone)).replace(tzinfo=None)).astimezone(pytzutc)
            dw_end_time = timezone(request.json["timezone"]).localize(get_time_now().replace(hour=dw.end_hour, minute=dw.end_minute).astimezone(timezone(g.user.timezone)).replace(tzinfo=None)).astimezone(pytzutc)
            dw.edit_window(
                dw_start_time.hour, dw_start_time.minute, dw_end_time.hour, dw_end_time.minute,
                scheduler, send_intro_text_new, send_boundary_text_new
            )
    g.user.timezone = request.json["timezone"]
    db.session.commit()
    # HACK: nuclear option for handling timezones
    # this also disallows us from using this endpoint as currently constituted for any other profile updates.
    if g.user.state == UserState.ACTIVE:
        g.user.pause(scheduler, send_pause_message, silent=True)
        g.user.resume(scheduler, send_intro_text_new, send_upcoming_dose_message, silent=True)
    return jsonify()

@app.route("/user/password", methods=["POST"])
@auth.login_required
def update_user_password():
    g.user.set_password(request.json["password"])
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=PASSWORD_UPDATED_MESSAGE,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{g.user.phone_number}"
        )
    db.session.commit()
    return jsonify()

def get_stripe_data(user):
    if g.user.stripe_customer_id is None:
        customer = stripe.Customer.create(name=g.user.name, phone=g.user.phone_number)
        g.user.stripe_customer_id = customer.id
        db.session.commit()
    else:
        customer = stripe.Customer.retrieve(
            g.user.stripe_customer_id,
            expand=["subscriptions", "invoice_settings.default_payment_method"]
        )
    if g.user.secondary_state == UserSecondaryState.PAYMENT_VERIFICATION_PENDING:
        return customer, None  # we're verifying, terminate early
    # TODO: allow people to change their payment methods.
    secret_key = None
    if customer.invoice_settings.default_payment_method is None:
        print(customer)
        # cancel incomplete subscriptions
        if hasattr(customer, "subscriptions") and customer.subscriptions is not None:  # it's none if we newly made a customer
            for subscription in customer.subscriptions.data:
                print("\n\n\n\n\n\nsubscription************\n\n\n\n\n\n")
                print(subscription)
                # subscription = stripe.Subscription.retrieve(subscription_id)
                if subscription.status in ["incomplete", "trialing"]:
                    stripe.Subscription.delete(subscription.id)
        # case 1: user is creating and paying for subscription, return payment_intent
        # criteria for case 1: user is in payment_method_requested or subscription_expired
        if g.user.state in [UserState.PAYMENT_METHOD_REQUESTED, UserState.SUBSCRIPTION_EXPIRED]:
            subscription = stripe.Subscription.create(
                customer=customer.id,
                items=[{
                    # 'price': "price_1IvWVmEInVrsQDJoBEtnprCX" if os.environ["FLASK_ENV"] == "production" else "price_1IrxibEInVrsQDJoNPvvYYkl",  # from stripe dashboard
                    "price": "price_1IrxibEInVrsQDJoNPvvYYkl"
                }],
                payment_behavior='default_incomplete',
                expand=['latest_invoice.payment_intent']
            )
            secret_key = subscription.latest_invoice.payment_intent.client_secret
        # user is creating payment method but not paying immediately, return setup_intent
        # criteria for case 2: user is active or paused and has end_of_service
        elif g.user.state in [UserState.ACTIVE, UserState.PAUSED] and g.user.end_of_service is not None:
            active_subscription = None
            if hasattr(customer, "subscriptions"):
                for subscription in customer.subscriptions.data:
                    subscription = stripe.Subscription.retrieve(subscription.id, expand=["latest_invoice.payment_intent"])
                    if subscription.status == "active":
                        active_subscription = subscription
                        break
            if active_subscription is None:
                new_subscription = stripe.Subscription.create(
                    customer=customer.id,
                    items=[{
                        # 'price': "price_1IvWVmEInVrsQDJoBEtnprCX" if os.environ["FLASK_ENV"] == "production" else "price_1IrxibEInVrsQDJoNPvvYYkl",  # from stripe dashboard
                        "price": "price_1IrxibEInVrsQDJoNPvvYYkl"
                    }],
                    payment_behavior='default_incomplete',
                    expand=['pending_setup_intent'],
                    trial_end=int(convert_naive_to_local_machine_time(g.user.charge_date).timestamp())
                )
                secret_key = new_subscription.pending_setup_intent.client_secret
            else:
                secret_key = active_subscription.latest_invoice.payment_intent.client_secret
    return customer, secret_key


@app.route("/user/cancelSubscription", methods=["POST"])
@auth.login_required
def user_cancel_subscription():
    print("hit endpoint")
    if g.user.stripe_customer_id is None:
        return jsonify(), 400
    customer = stripe.Customer.retrieve(g.user.stripe_customer_id, expand=["subscriptions"])
    if len(customer.subscriptions.data) == 0:
        print("no subscriptions found")
        return jsonify(), 200
    for subscription in customer.subscriptions.data:
        print(subscription)
        print(subscription.status)
        if subscription.status in ["active", "trialing", "incomplete"]:
            stripe.Subscription.delete(subscription.id)
    g.user.end_of_service = get_time_now()  # subscription time ends now
    db.session.commit()
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=CANCELLATION_RESPONSE,
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{g.user.phone_number}"
        )
        client.messages.create(
            body=USER_CANCELLED_NOTIF.substitute(phone_number=g.user.phone_number),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+1{ADMIN_PHONE_NUMBER}"
        )
    return jsonify(), 200


@app.route("/user/renewSubscription", methods=["POST"])
@auth.login_required
def user_renew_subscription():
    customer = stripe.Customer.retrieve(
        g.user.stripe_customer_id,
        expand=["subscriptions", "invoice_settings.default_payment_method"]
    )
    if customer is None:
        return jsonify(), 400
    if customer.invoice_settings.default_payment_method is None:
        return jsonify(), 400
    for subscription in customer.subscriptions.data:
        if subscription.status in ["active", "trialing"]:
            return jsonify(), 400  # you already have an active subscription
    subscription = stripe.Subscription.create(
        customer=customer.id,
        items=[{
            # 'price': "price_1IvWVmEInVrsQDJoBEtnprCX" if os.environ["FLASK_ENV"] == "production" else "price_1IrxibEInVrsQDJoNPvvYYkl",  # from stripe dashboard
            "price": "price_1IrxibEInVrsQDJoNPvvYYkl"
        }],
        payment_behavior='default_incomplete',
        expand=['latest_invoice.payment_intent']
    )
    stripe.PaymentIntent.confirm(
        subscription.latest_invoice.payment_intent.id,
        payment_method=customer.invoice_settings.default_payment_method
    )
    return jsonify(), 200


# TODO: error handling
@app.route("/user/getPaymentData", methods=["GET"])
@auth.login_required
def user_get_payment_info():
    customer, secret_key = get_stripe_data(g.user)
    return_dict = {
        "state": g.user.state.value,
        "secondary_state": g.user.secondary_state.value if g.user.secondary_state is not None else None,
        "client_secret": secret_key,
        "publishable_key": os.environ["STRIPE_PUBLISHABLE_KEY"]
    }
    if g.user.state in [UserState.PAUSED, UserState.ACTIVE, UserState.PAYMENT_METHOD_REQUESTED]:
        g.user.stripe_customer_id = customer.id
        db.session.commit()
        if g.user.state in [UserState.PAUSED, UserState.ACTIVE]:  # subscription is currently active, retrive addl data
            return_dict["subscription_end_date"] = convert_naive_to_local_machine_time(g.user.charge_date) if g.user.end_of_service is not None else None
            if g.user.stripe_customer_id is not None:
                default_payment_method = customer.invoice_settings.default_payment_method
                return_dict["payment_method"] = None if default_payment_method is None else {"brand": default_payment_method.card.brand, "last4": default_payment_method.card.last4 }
        # get stripe payment method data
    elif g.user.state == UserState.SUBSCRIPTION_EXPIRED:
        return_dict["subscription_end_date"] = convert_naive_to_local_machine_time(g.user.end_of_service)
        return_dict["subscription_expired"] = True
        if g.user.stripe_customer_id is not None:
            default_payment_method = customer.invoice_settings.default_payment_method
            return_dict["payment_method"] = None if default_payment_method is None else {"brand": default_payment_method.card.brand, "last4": default_payment_method.card.last4 }
    return jsonify(return_dict)


@app.route("/user/submitPaymentInfo", methods=["POST"])
@auth.login_required
def user_submit_payment_info():
    if g.user.secondary_state is None:
        g.user.secondary_state = UserSecondaryState.PAYMENT_VERIFICATION_PENDING
        db.session.commit()
    return jsonify()


@app.route("/webhook/stripe", methods=["POST"])
def stripe_webhook():
    payload = request.json
    print(payload)
    try:
        event = stripe.Event.construct_from(
            payload, stripe.api_key
        )
    except ValueError:
        # Invalid payload
        return jsonify(), 400
    if event.type in ["payment_intent.succeeded", "setup_intent.succeeded"]:
        # set submitted card as customer's default payment method for future charging
        related_user = User.query.filter(User.stripe_customer_id == event.data.object.customer).one_or_none()
        stripe.Customer.modify(event.data.object.customer, invoice_settings={"default_payment_method": event.data.object.payment_method})
        if related_user is None:
            return jsonify(), 401
        print(f"secondary state: {related_user.secondary_state}")
        if related_user.secondary_state == UserSecondaryState.PAYMENT_VERIFICATION_PENDING:
            related_user.secondary_state = None
            db.session.add(related_user)
            db.session.commit()
    elif event.type == "invoice.payment_succeeded":  # consider bill paid
        related_user = User.query.filter(User.stripe_customer_id == event.data.object.customer).one_or_none()
        if related_user is None:
            return jsonify(), 401
        if related_user.state in [UserState.PAYMENT_METHOD_REQUESTED, UserState.SUBSCRIPTION_EXPIRED]:
            # the user is officially on a "free trial" until 1 month + 1 day, but they already paid at the start
            subscription_end_day = get_start_of_day(related_user.timezone, days_delta=1, months_delta=1)
            # give them till start of tomorrow for free
            stripe.Subscription.modify(
                sid=event.data.object.subscription,
                trial_end=int(subscription_end_day.timestamp()),
                proration_behavior="none"
            )
            related_user.end_of_service = subscription_end_day + timedelta(days=1)  # one extra day for a service termination grace period.
            print(related_user.state)
            if related_user.state == UserState.PAYMENT_METHOD_REQUESTED:
                subscription = stripe.Subscription.retrieve(event.data.object.subscription, expand=["latest_invoice.payment_intent.payment_method"])
                print(subscription.latest_invoice.payment_intent)
                print(subscription.blah)
                if subscription.latest_invoice.payment_intent is not None:  # attach payment method, if there was one associated
                    stripe.Customer.modify(event.data.object.customer, invoice_settings={"default_payment_method": subscription.latest_invoice.payment_intent.payment_method})
                if "NOALERTS" not in os.environ:
                    client.messages.create(
                        body=ONBOARDING_COMPLETE,
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=f"+1{related_user.phone_number}"
                    )
                    client.messages.create(
                        body=USER_SUBSCRIBED_NOTIF.substitute(phone_number=related_user.phone_number),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=f"+1{ADMIN_PHONE_NUMBER}"
                    )
                related_user.state = UserState.PAUSED
            elif related_user.state == UserState.SUBSCRIPTION_EXPIRED:
                if "NOALERTS" not in os.environ:
                    client.messages.create(
                        body=RENEWAL_COMPLETE,
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=f"+1{related_user.phone_number}"
                    )
                    client.messages.create(
                        body=USER_RENEWED_NOTIF.substitute(phone_number=related_user.phone_number),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=f"+1{ADMIN_PHONE_NUMBER}"
                    )
                related_user.state = UserState.ACTIVE  # autoactive after renewal
            related_user.secondary_state = None  # not sure if this is needed but just in case
            db.session.commit()
        if related_user.state in [UserState.ACTIVE, UserState.PAUSED]:  # subscription auto-renewal
            subscription = stripe.Subscription.retrieve(event.data.object.subscription)
            if subscription.status == "active":
                related_user.end_of_service = datetime.fromtimestamp(subscription.current_period_end) + timedelta(days=1)
                db.session.commit()

    elif event.type == "payment_intent.payment_failed" or event.type == "charge.failed" or event.type == "invoice.payment_failed":
        related_user = User.query.filter(User.stripe_customer_id == event.data.object.customer).one_or_none()
        if related_user is None:
            return jsonify(), 401
        if related_user.state == UserState.PAYMENT_METHOD_REQUESTED:
            if related_user.secondary_state == UserSecondaryState.PAYMENT_VERIFICATION_PENDING:
                related_user.secondary_state = None  # clear verifying status
            if "NOALERTS" not in os.environ:
                client.messages.create(
                    body=PAYMENT_METHOD_FAILURE,
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=f"+1{related_user.phone_number}"
                )
                client.messages.create(
                    body=USER_PAYMENT_METHOD_FAIL_NOTIF.substitute(phone_number=related_user.phone_number),
                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                    to=f"+1{ADMIN_PHONE_NUMBER}"
                )
            db.session.commit()
    else:
        print(f"unhandled event type {event.type}")

    return jsonify(), 200

def exists_remaining_reminder_job(dose_id, job_list):
    for job in job_list:
        if scheduler.get_job(f"{dose_id}-{job}"):
            return True
    return False


# NEW
def send_boundary_text_new(dose_window_obj_id):
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    if "NOALERTS" not in os.environ:
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
    print(dose_window_obj.is_recorded())
    if not dose_window_obj.is_recorded():  # only send if the dose window object hasn't been recorded yet.
        if "NOALERTS" not in os.environ:
            client.messages.create(
                body=f"{get_initial_message(dose_window_obj, get_time_now().astimezone(timezone(dose_window_obj.user.timezone)).strftime('%I:%M'), welcome_back, dose_window_obj.user.phone_number)}{'' if dose_window_obj.user.already_sent_intro_today else ACTION_MENU}",
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

scheduler.add_listener(scheduler_error_alert, EVENT_JOB_MISSED | EVENT_JOB_ERROR)
scheduler.init_app(app)
scheduler.start()


@scheduler.authenticate
def authenticate(auth):
    """Check auth."""
    return verify_password(auth["username"], None)

if __name__ == '__main__':
    app.run(host='0.0.0.0')