# handler for all regexing and message segmentation (later, more stuff I hope)
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

MEDICATION_TAKEN_REGEX = r'(?:\s+|^)(taken|take|t)(?:\s+|$)'
TIME_EXTRACTION_REGEX = r'(\d+(?:\:\d+)?)\s*(pm|am|hr|hours|hour|mins|min)?'
SKIP_REGEX = r'(?:\s+|^)(skipped|skipping|skip|s)(?:\s+|$)'
SPECIAL_COMMANDS_REGEX = r'(?:\s+|^)(\d+|x)(?:\s+|$)'

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

def segment_message(raw_message_str):
    message_segments = []
    processed_msg = raw_message_str.lower().strip()
    excited = "!" in processed_msg
    # grab time before punctuation is removed because we need the :
    extracted_time = re.findall(TIME_EXTRACTION_REGEX, processed_msg)
    # remove all punctuation
    processed_msg = processed_msg.translate(str.maketrans("", "", string.punctuation))
    # remove brackets
    processed_msg = processed_msg.replace("[", "").replace("]", "")
    taken_data = re.findall(MEDICATION_TAKEN_REGEX, processed_msg)
    print(taken_data)
    skip_data = re.findall(SKIP_REGEX, processed_msg)
    special_commands = re.findall(SPECIAL_COMMANDS_REGEX, processed_msg)
    parse_status = 0
    if extracted_time:
        reconstructed_time = extracted_time[0][0]
        if extracted_time[0][1] is not None:
            reconstructed_time += " " + extracted_time[0][1]
        print(reconstructed_time)
        datetime_data, parse_status = cal.parseDT(reconstructed_time)
        next_alarm_time = datetime_data
        if os.environ['FLASK_ENV'] == "local":  # HACK: required to get this to work on local
            pacific_time = timezone(USER_TIMEZONE)
            next_alarm_time = pacific_time.localize(datetime_data.replace(tzinfo=None))
    if taken_data:
        message_body = {"type": "take", "modifiers": {"emotion": "excited" if excited else "neutral"}}
        if parse_status != 0:
            message_body["payload"] = next_alarm_time
        message_segments.append(message_body)
    elif skip_data:
        message_segments.append({"type": "skip"})
    elif parse_status != 0:
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
