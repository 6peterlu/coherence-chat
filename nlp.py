# handler for all regexing and message segmentation (later, more stuff I hope)
from datetime import timedelta
from pytz import timezone, utc as pytzutc
import os
import string
import re

# parse timestrings
import parsedatetime

# fuzzy nlp handling
import spacy

nlp = spacy.load("en_core_web_sm")

# parse datetime calendar object
cal = parsedatetime.Calendar()

USER_TIMEZONE = "US/Pacific"

MEDICATION_TAKEN_REGEX = r'(?:\W|^)(taken|take|t)(?:\W|$)'
TIME_EXTRACTION_REGEX = r'(\d+(?:\:\d+)?)\s*(pm|am|hr|hours|hour|mins|min)?'
SKIP_REGEX = r'(?:\W|^)(skipped|skipping|skip|s)(?:\W|$)'
SPECIAL_COMMANDS_REGEX = r'(?:\W|^)(\d+|x)(?:\W|$)'

COMPUTING_PREFIX = "Computing ideal reminder time...done."

RECOGNIZED_ACTIVITIES = {
    "brunch": {"type": "long", "response": f"{COMPUTING_PREFIX} Have a great brunch! We'll check in later.", "concept": "meal"},
    "dinner": {"type": "long", "response": f"{COMPUTING_PREFIX} Have a great dinner! We'll check in later.", "concept": "meal"},
    "lunch": {"type": "long", "response": f"{COMPUTING_PREFIX} Have a great lunch! We'll check in later.", "concept": "meal"},
    "breakfast": {"type": "long", "response": f"{COMPUTING_PREFIX} Have a great breakfast! We'll check in later.", "concept": "meal"},
    "eating": {"type": "long", "response": f"{COMPUTING_PREFIX} Enjoy your meal! We'll check in later.", "concept": "meal"},
    "meeting": {"type": "long", "response": f"{COMPUTING_PREFIX} Have a productive meeting! We'll check in later.", "concept": "work"},
    "out": {"type": "long", "response": f"{COMPUTING_PREFIX} No problem, we'll check in later.", "concept": "away"},
    "busy": {"type": "long", "response": f"{COMPUTING_PREFIX} No problem, we'll check in later.", "concept": "work"},
    "later": {"type": "long", "response": f"{COMPUTING_PREFIX} No problem, we'll check in later.", "concept": "work"},
    "reading": {"type": "long", "response": f"{COMPUTING_PREFIX} Enjoy your book, we'll check in later.", "concept": "leisure"},
    "sleeping": {"type": "long", "response": f"{COMPUTING_PREFIX} Sleep well! We'll see you later.", "concept": "leisure"},
    "golf": {"type": "long", "response": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later.", "concept": "leisure"},
    "tennis": {"type": "long", "response": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later.", "concept": "leisure"},
    "swimming": {"type": "long", "response": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later.", "concept": "leisure"},
    "basketball": {"type": "long", "response": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later.", "concept": "leisure"},
    "tv": {"type": "long", "response": f"{COMPUTING_PREFIX} Have fun, we'll check in later.", "concept": "leisure"},
    "working": {"type": "long", "response": f"{COMPUTING_PREFIX} No problem, we'll check in later.", "concept": "work"},
    "walking": {"type": "short", "response": f"{COMPUTING_PREFIX} Enjoy your walk! We'll check in later.", "concept": "leisure"},
    "walk": {"type": "short", "response": f"{COMPUTING_PREFIX} Enjoy your walk! We'll check in later.", "concept": "leisure"},
    "bathroom": {"type": "short", "response": f"{COMPUTING_PREFIX} No problem, we'll check in in a bit.", "concept": "errand"},
    "run":  {"type": "short", "response": f"{COMPUTING_PREFIX} Have a great run! We'll see you later.", "concept": "leisure"},
    "running":  {"type": "short", "response": f"{COMPUTING_PREFIX} Have a great run! We'll see you later.", "concept": "leisure"},
    "basketball":  {"type": "short", "response": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later.", "concept": "leisure"},
    "shower":  {"type": "short", "response": f"{COMPUTING_PREFIX} No problem, we'll check in later.", "concept": "errand"},
    "phone": {"type": "short", "response": f"{COMPUTING_PREFIX} Have a great call! We'll check in later.", "concept": "work"},
    "call": {"type": "short", "response": f"{COMPUTING_PREFIX} Have a great call! We'll check in later.", "concept": "work"},
}

THANKS_VERSIONS = ["thank", "ty"]

# re-integrate spacy later
# SPACY_EMBEDDINGS = {token: nlp(token) for token in RECOGNIZED_ACTIVITIES}


def get_datetime_obj_from_string(timestring, force=False):
    next_alarm_time, parse_status = cal.parseDT(timestring, tzinfo=pytzutc)
    # HACK: required to get this to work on local
    if os.environ["FLASK_ENV"] == "local":
        pacific_time = timezone(USER_TIMEZONE)
        next_alarm_time = pacific_time.localize(next_alarm_time.replace(tzinfo=None))
    if parse_status != 0:
        return next_alarm_time
    if force:
        if len(timestring) <= 2:
            modified_timestring = f"{timestring}:00"
            next_alarm_time, parse_status = cal.parseDT(modified_timestring, tzinfo=pytzutc)
            # HACK: required to get this to work on local
            if os.environ["FLASK_ENV"] == "local":
                pacific_time = timezone(USER_TIMEZONE)
                next_alarm_time = pacific_time.localize(next_alarm_time.replace(tzinfo=None))
            if parse_status != 0:
                return next_alarm_time
    return None

def segment_message(raw_message_str):
    message_segments = []
    processed_msg = raw_message_str.lower().strip()
    excited = "!" in processed_msg
    # remove all punctuation besides : and @
    punctuation = string.punctuation.replace("@", "").replace(":", "")
    processed_msg = processed_msg.translate(str.maketrans("", "", punctuation))
    # remove brackets
    processed_msg = processed_msg.replace("[", "").replace("]", "")
    extracted_time = re.findall(TIME_EXTRACTION_REGEX, processed_msg)
    taken_data = re.findall(MEDICATION_TAKEN_REGEX, processed_msg)
    skip_data = re.findall(SKIP_REGEX, processed_msg)
    special_commands = re.findall(SPECIAL_COMMANDS_REGEX, processed_msg)
    reconstructed_time = None
    next_alarm_time = None
    if extracted_time:
        reconstructed_time = extracted_time[0][0]
        if extracted_time[0][1]:
            reconstructed_time += " " + extracted_time[0][1]
        next_alarm_time = get_datetime_obj_from_string(reconstructed_time)
    if taken_data:
        if reconstructed_time and next_alarm_time is None:
            next_alarm_time = get_datetime_obj_from_string(reconstructed_time, force=True)
        message_body = {"type": "take", "modifiers": {"emotion": "excited" if excited else "neutral"}}
        # disable this for now, because its really broken
        # if next_alarm_time is not None:
        #     # maybe this is only needed in the pm?
        #     # next_alarm_time -= timedelta(hours=12)  # go back to last referenced time
        #     message_body["payload"] = next_alarm_time
        message_segments.append(message_body)
    elif skip_data:
        message_segments.append({"type": "skip"})
    elif next_alarm_time is not None:
        message_segments.append({"type": "requested_alarm_time", "payload": next_alarm_time})
    else:
        if special_commands:
            command = special_commands[0]
            if command not in ['1', '2', '3', 'x']:  # must be a manual minute entry
                message_segments.append({"type": "delay_minutes", "payload": int(command)})
            else:
                message_segments.append({"type": "special", "payload": command})
        # still process activities if there are special commands
        for activity in RECOGNIZED_ACTIVITIES:
            if activity in processed_msg:
                message_segments.append({"type": "activity", "payload": RECOGNIZED_ACTIVITIES[activity]})
                break
    for thanks_version in THANKS_VERSIONS:
        if thanks_version in processed_msg:
            message_segments.append({"type": "thanks", "modifiers": {"emotion": "excited" if excited else "neutral"}})

    message_segments = [{**message, "raw": raw_message_str} for message in message_segments]
    return message_segments
