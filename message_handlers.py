from models import (
    DoseWindow,
    EventLog,
    Online,
    db
)
from time_helpers import get_time_now
from pytz import timezone
from datetime import timedelta
import os
import random
from constants import (
    ABSENT_MSGS,
    ACTION_OUT_OF_RANGE_MSG,
    ALREADY_RECORDED,
    BLOOD_GLUCOSE_MESSAGE,
    BLOOD_PRESSURE_MESSAGE,
    BOUNDARY_MSG,
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
    PAUSE_MESSAGE,
    REMINDER_OUT_OF_RANGE_MSG,
    REMINDER_TOO_CLOSE_MSG,
    REMINDER_TOO_LATE_MSG,
    REQUEST_DOSE_WINDOW_COUNT,
    REQUEST_DOSE_WINDOW_END_TIME,
    REQUEST_DOSE_WINDOW_START_TIME,
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
    WEIGHT_MESSAGE,
    WELCOME_BACK_MESSAGES
)
from ai import get_reminder_time_within_range

BUFFER_TIME_MINS = 10

TWILIO_PHONE_NUMBERS = {
    "local": "2813771848",
    "production": "2673824152"
}

# handle incoming messages for different user states
def active_state_message_handler(
    incoming_msg_list,
    user,
    dose_window,
    incoming_phone_number,
    raw_message
):
    from bot import client, scheduler
    # we weren't able to parse any part of the message
    if len(incoming_msg_list) == 0:
        log_event_new("not_interpretable", user.id, None if dose_window is None else dose_window.id, description=raw_message)
        text_fallback(incoming_phone_number)
    for incoming_msg in incoming_msg_list:
        print(user.manual_takeover)
        if user.manual_takeover:
            log_event_new("manually_silenced", user.id, None if dose_window is None else dose_window.id, description=incoming_msg["raw"])
            text_fallback(incoming_phone_number)
        else:
            if incoming_msg["type"] == "take":
                # all doses not recorded, we record now
                excited = incoming_msg["modifiers"]["emotion"] == "excited"
                input_time_data = incoming_msg.get("payload")
                dose_window_to_mark = None
                out_of_range = False
                input_time = None
                if input_time_data is not None:
                    input_time = get_most_recent_matching_time(input_time_data, user)
                else:
                    input_time = get_time_now()
                dose_window_to_mark, out_of_range = get_nearest_dose_window(input_time, user)
                days_delta = user.get_day_delta(input_time)
                # dose_window_to_mark will never be None unless the user has no dose windows, but we'll handle that upstream
                if dose_window_to_mark.is_recorded(days_delta=days_delta):
                    associated_doses = dose_window_to_mark.medications
                    for dose in associated_doses:
                        log_event_new("attempted_rerecord", user.id, dose_window_to_mark.id, dose.id, description=incoming_msg["raw"])
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=ALREADY_RECORDED,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                else: # we need to record the dose
                    for medication in dose_window_to_mark.medications:
                        log_event_new("take", user.id, dose_window_to_mark.id, medication.id, description=medication.id, event_time=input_time)
                    dose_window_to_mark.remove_boundary_event(days_delta=days_delta)
                    outgoing_copy = get_take_message_new(excited, user, input_time=input_time)
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=outgoing_copy,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                    if out_of_range and "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=SUGGEST_DOSE_WINDOW_CHANGE,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
                    if dose_window and dose_window.is_recorded():  # not out of range, remove jobs
                        remove_jobs_helper(dose_window.id, ["absent", "followup", "boundary"], new=True)
            elif incoming_msg["type"] == "skip":
                if dose_window is not None:
                    if dose_window.is_recorded():
                        associated_doses = dose_window.medications
                        for dose in associated_doses:
                            log_event_new("attempted_rerecord", user.id, dose_window.id, dose.id, description=incoming_msg["raw"])
                        if "NOALERTS" not in os.environ:
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
                        if "NOALERTS" not in os.environ:
                            client.messages.create(
                                body=f"{SKIP_MSG}{f' {get_random_emoji()}' if incoming_msg['modifiers']['emotion'] == 'smiley' else ''}",
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                        remove_jobs_helper(dose_window.id, ["absent", "followup", "boundary"], new=True)
                else:
                    log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
            elif incoming_msg["type"] == "special":
                if incoming_msg["payload"] == "x":
                    if "NOALERTS" not in os.environ:
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
                            if "NOALERTS" not in os.environ:
                                confirmation_msg = CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(user.timezone)).strftime('%I:%M'))
                                if incoming_msg['modifiers']['emotion'] == 'smiley':
                                    confirmation_msg = append_emoji_suffix(confirmation_msg)
                                client.messages.create(
                                    body=(REMINDER_TOO_CLOSE_MSG.substitute(
                                        time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M"),
                                        reminder_time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M"))
                                        if too_close else confirmation_msg
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
                            if "NOALERTS" not in os.environ:
                                client.messages.create(
                                    body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                    from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                    to=incoming_phone_number
                                )
                    else:
                        log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                        if "NOALERTS" not in os.environ:
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
                        if "NOALERTS" not in os.environ:
                            confirmation_msg = CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M"))
                            if incoming_msg['modifiers']['emotion'] == 'smiley':
                                confirmation_msg = append_emoji_suffix(confirmation_msg)
                            client.messages.create(
                                body=(REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M")) if too_close
                                    else confirmation_msg),
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
                        if "NOALERTS" not in os.environ:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                else:
                    log_event_new("out_of_range", user.id, dose_window.id, None, description=incoming_msg["raw"])
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
            if incoming_msg["type"] == "requested_alarm_time":
                if dose_window is not None:
                    next_alarm_time = get_most_recent_matching_time(incoming_msg["payload"], user, after=True)
                    # TODO: remove repeated code block
                    too_close = False
                    dose_end_time = dose_window.next_end_date - timedelta(days=1)
                    if next_alarm_time > dose_end_time - timedelta(minutes=10):
                        next_alarm_time = dose_end_time - timedelta(minutes=10)
                        too_close = True
                    if next_alarm_time > get_time_now():
                        log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(user.timezone))}")
                        if "NOALERTS" not in os.environ:
                            confirmation_msg = CONFIRMATION_MSG.substitute(time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M"))
                            if incoming_msg['modifiers']['emotion'] == 'smiley':
                                confirmation_msg = append_emoji_suffix(confirmation_msg)
                            client.messages.create(
                                body=(REMINDER_TOO_CLOSE_MSG.substitute(
                                    time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M"),
                                    reminder_time=next_alarm_time.astimezone(timezone(user.timezone)).strftime("%I:%M"))
                                    if too_close else confirmation_msg
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
                        if "NOALERTS" not in os.environ:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                else:
                    log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
            if incoming_msg["type"] == "activity":
                if dose_window is not None:
                    log_event_new("activity", user.id, dose_window.id, None, description=incoming_msg["raw"])
                    reminder_range_start = get_time_now() + (timedelta(minutes=10) if incoming_msg["payload"]["type"] == "short" else timedelta(minutes=30))
                    reminder_range_end = get_time_now() + (timedelta(minutes=30) if incoming_msg["payload"]["type"] == "short" else timedelta(minutes=60))
                    next_alarm_time = get_reminder_time_within_range(reminder_range_start, reminder_range_end, user)
                    dose_end_time = dose_window.next_end_date - timedelta(days=1)
                    # TODO: remove repeated code block
                    too_close = False
                    dose_end_time = dose_window.next_end_date - timedelta(days=1)
                    if next_alarm_time > dose_end_time - timedelta(minutes=10):
                        next_alarm_time = dose_end_time - timedelta(minutes=10)
                        too_close = True
                    if next_alarm_time > get_time_now():
                        log_event_new("reminder_delay", user.id, dose_window.id, None, description=f"delayed to {next_alarm_time.astimezone(timezone(user.timezone))}")
                        if "NOALERTS" not in os.environ:
                            canned_response = incoming_msg["payload"]["response"]
                            if incoming_msg['modifiers']['emotion'] == 'smiley':
                                canned_response = append_emoji_suffix(canned_response)
                            client.messages.create(
                                body=canned_response,
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
                        if "NOALERTS" not in os.environ:
                            client.messages.create(
                                body=REMINDER_TOO_LATE_MSG.substitute(time=dose_end_time.astimezone(timezone(user.timezone)).strftime("%I:%M")),
                                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                                to=incoming_phone_number
                            )
                else:
                    log_event_new("out_of_range", user.id, None, None, description=incoming_msg["raw"])
                    if "NOALERTS" not in os.environ:
                        client.messages.create(
                            body=ACTION_OUT_OF_RANGE_MSG if incoming_msg in ["t", "s"] else REMINDER_OUT_OF_RANGE_MSG,
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
            if incoming_msg["type"] == "thanks":
                log_event_new("conversational", user.id, None, None, description=incoming_msg["raw"])
                if "NOALERTS" not in os.environ:
                    if random.random() < 0.5:  # only send thanks response 50% of the time to reduce staleness
                        client.messages.create(
                            body=get_thanks_message(),
                            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                            to=incoming_phone_number
                        )
            if incoming_msg["type"] == "website_request":
                log_event_new("website_request", user.id, None, None, description=incoming_msg["raw"])
                if "NOALERTS" not in os.environ:
                    client.messages.create(
                        body=REQUEST_WEBSITE,
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
            if incoming_msg["type"] == "health_metric":
                log_event_new(f"hm_{incoming_msg['payload']['type']}", user.id, None, None, description=incoming_msg["payload"]["value"])
                if "NOALERTS" not in os.environ:
                    client.messages.create(
                        body=get_health_metric_response_message(incoming_msg['payload']['type'], incoming_msg["payload"]["value"], user),
                        from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                        to=incoming_phone_number
                    )
    if user.pending_announcement:
        log_event_new(f"feature_announcement", user.id, None, None, description=user.pending_announcement)
        if "NOALERTS" not in os.environ:
            client.messages.create(
                body=user.pending_announcement,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=incoming_phone_number
            )
        user.pending_announcement = None
        db.session.commit()


def text_fallback(phone_number):
    from bot import client, get_online_status  # inline import to avoid circular issues
    if get_online_status():
        # if we're online, don't send the unknown text and let us respond.
        if "NOALERTS" not in os.environ:
            client.messages.create(
                body=MANUAL_TEXT_NEEDED_MSG.substitute(number=phone_number),
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to="+13604508655"  # admin phone #
            )
    else:
        if "NOALERTS" not in os.environ:
            client.messages.create(
                body=UNKNOWN_MSG,
                from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
                to=phone_number
            )

# texts and jobs
def remove_jobs_helper(dose_id, jobs_list, new=False):
    from bot import scheduler
    for job in jobs_list:
        job_id = f"{dose_id}-{job}-new" if new else f"{dose_id}-{job}"
        if scheduler.get_job(job_id):
            scheduler.remove_job(job_id)

def send_followup_text_new(dose_window_obj_id):
    from bot import scheduler, client
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

def maybe_schedule_absent_new(dose_window_obj):
    from bot import scheduler
    end_date = dose_window_obj.next_end_date - timedelta(days=1)
    reminder_range_start = get_time_now() + timedelta(minutes=40)
    reminder_range_end = get_time_now() + timedelta(minutes=90)
    next_alarm_time = get_reminder_time_within_range(reminder_range_start, reminder_range_end, dose_window_obj.user)
    desired_absent_reminder = min(next_alarm_time, end_date - timedelta(minutes=BUFFER_TIME_MINS))
    # room to schedule absent
    if desired_absent_reminder > get_time_now():
        scheduler.add_job(f"{dose_window_obj.id}-absent-new", send_absent_text_new,
            args=[dose_window_obj.id],
            trigger="date",
            run_date=desired_absent_reminder,
            misfire_grace_time=5*60
        )

# NEW
def send_absent_text_new(dose_window_obj_id):
    from bot import client, scheduler
    dose_window_obj = DoseWindow.query.get(dose_window_obj_id)
    if "NOALERTS" not in os.environ:
        client.messages.create(
            body=get_absent_message(),
            from_=f"+1{TWILIO_PHONE_NUMBERS[os.environ['FLASK_ENV']]}",
            to=f"+11{dose_window_obj.user.phone_number}"
        )
    remove_jobs_helper(dose_window_obj.id, ["absent", "followup"], new=True)
    maybe_schedule_absent_new(dose_window_obj)
    log_event_new("absent", dose_window_obj.user.id, dose_window_obj.id, medication_id=None)


# DB interface helpers
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


# message copy helpers, move elsewhere eventually?
def get_take_message_new(excited, user_obj, input_time=None):
    take_time = get_time_now() if input_time is None else input_time
    timezone_translated_time = take_time.astimezone(timezone(user_obj.timezone)).strftime('%b %d, %I:%M %p')
    return TAKE_MSG_EXCITED.substitute(time=timezone_translated_time) if excited else TAKE_MSG.substitute(time=timezone_translated_time)


def get_random_emoji():
    return random.choice(["💫", "🌈", "🌱", "🏆", "💎", "💡", "🔆", "(:", "☺️", "👍", "😇", "😊"])

def append_emoji_suffix(input_str):
    return f"{input_str} {get_random_emoji()}"

def get_thanks_message():
    return random.choice(THANKS_MESSAGES)

def get_health_metric_response_message(health_metric_type, description, user):
    timezone_translated_time = get_time_now().astimezone(timezone(user.timezone)).strftime('%b %d, %I:%M %p')
    if health_metric_type == "glucose":
        return BLOOD_GLUCOSE_MESSAGE.substitute(blood_glucose=description, time=timezone_translated_time)
    if health_metric_type == "weight":
        return WEIGHT_MESSAGE.substitute(weight=description, time=timezone_translated_time)
    if health_metric_type == "blood pressure":
        return BLOOD_PRESSURE_MESSAGE.substitute(blood_pressure=description, time=timezone_translated_time)
    return None

def get_followup_message():
    return random.choice(FOLLOWUP_MSGS)

def get_absent_message():
    return random.choice(ABSENT_MSGS)

# time helpers TODO: move to time.py
def get_most_recent_matching_time(input_time_data, user, after=False):  # if after is true, get time after
    now = get_time_now()
    most_recent_time = input_time_data["time"]
    if input_time_data["needs_tz_convert"]:  # nlp class requests tz convert for this time
        local_tz = timezone(user.timezone)
        most_recent_time = local_tz.localize(input_time_data["time"].replace(tzinfo=None))  # user enters in their local time
    am_pm_defined = input_time_data["am_pm_defined"]
    cycle_interval = 24 if am_pm_defined else 12
    # cycle forward
    if after:
        while most_recent_time > now + timedelta(hours=cycle_interval):
            most_recent_time -= timedelta(hours=cycle_interval)
        # cycle back
        while most_recent_time < now:
            most_recent_time += timedelta(hours=cycle_interval)
    else:
        while most_recent_time < now - timedelta(hours=cycle_interval):
            most_recent_time += timedelta(hours=cycle_interval)
        # cycle back
        while most_recent_time > now:
            most_recent_time -= timedelta(hours=cycle_interval)
    return most_recent_time

def get_nearest_dose_window(input_time, user):
    for dose_window in user.active_dose_windows:
        if dose_window.within_dosing_period(input_time, day_agnostic=True):
            return dose_window, False  # not outside of dose window
    # dose window fuzzy matching
    nearest_dose_window = min(user.active_dose_windows, key=lambda dw: min(
        abs(dw.next_start_date - input_time),
        abs(dw.next_start_date - timedelta(days=1) - input_time),
        abs(dw.next_end_date - input_time),
        abs(dw.next_end_date - timedelta(days=1) - input_time)
    ))
    return nearest_dose_window, True
