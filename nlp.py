# handler for all regexing and message segmentation (later, more stuff I hope)
from datetime import timedelta
from pytz import timezone, utc as pytzutc
import os
import string
import re
import tzlocal

# parse timestrings
import parsedatetime

# fuzzy nlp handling
import spacy

nlp = spacy.load("en_core_web_sm")

# parse datetime calendar object
cal = parsedatetime.Calendar()

USER_TIMEZONE = "US/Pacific"

MEDICATION_TAKEN_REGEX = r'(?:\W|^)(taken|take|t)(?:\W|$)'
TIME_DELAY_EXTRACTION_REGEX = r'(\d+)\s*(minutes|minute|mins|min|hours|hour|hr)'
ABSOLUTE_TIME_EXTRACTION_REGEX = r'(\d+(?:\:\d+)?)\s*(am|pm)?'
SKIP_REGEX = r'(?:\W|^)(skipped|skipping|skip|s)(?:\W|$)'
SPECIAL_COMMANDS_REGEX = r'(?:\W|^)(\d+|x)(?:\W|$)'
WEBSITE_REGEX = r'((?:\W|^)(?:w)(?:\W|$)|website|site)'

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

def get_datetime_obj_from_string(input_str, expanded_search=False, format_restrictions=False):
    output_time = None
    # search for time delays if flagged
    if expanded_search:
        extracted_time_delay = re.findall(TIME_DELAY_EXTRACTION_REGEX, input_str)
        reconstructed_time = " ".join([" ".join(time_pair) for time_pair in extracted_time_delay])
        computed_time, parse_status = cal.parseDT(reconstructed_time, tzinfo=tzlocal.get_localzone())
        if parse_status != 0:
            output_time = computed_time
    if output_time is None:
        if format_restrictions and not re.match(r'(pm|am|\:)', input_str):
            return None
        extracted_absolute_time = re.findall(ABSOLUTE_TIME_EXTRACTION_REGEX, input_str)
        if extracted_absolute_time:
            reconstructed_time = extracted_absolute_time[0][0]
            if len(reconstructed_time) <= 2 and ":" not in reconstructed_time:
                reconstructed_time += ":00"
            if extracted_absolute_time[0][1]:
                reconstructed_time += " " + extracted_absolute_time[0][1]
            computed_time, parse_status = cal.parseDT(reconstructed_time, tzinfo=pytzutc)
            if parse_status != 0:
                output_time = computed_time
    return output_time

def segment_message(raw_message_str):
    message_segments = []
    processed_msg = raw_message_str.lower().strip()
    excited = "!" in processed_msg
    # remove all punctuation besides : and @
    punctuation = string.punctuation.replace("@", "").replace(":", "")
    processed_msg = processed_msg.translate(str.maketrans("", "", punctuation))
    # remove brackets
    processed_msg = processed_msg.replace("[", "").replace("]", "")
    taken_data = re.findall(MEDICATION_TAKEN_REGEX, processed_msg)
    skip_data = re.findall(SKIP_REGEX, processed_msg)
    special_commands = re.findall(SPECIAL_COMMANDS_REGEX, processed_msg)
    website_request = re.findall(WEBSITE_REGEX, processed_msg)

    extracted_time = get_datetime_obj_from_string(processed_msg, expanded_search=True, format_restrictions=True)

    if taken_data:
        next_alarm_time = get_datetime_obj_from_string(processed_msg, expanded_search=False)
        message_body = {"type": "take", "modifiers": {"emotion": "excited" if excited else "neutral"}}
        # if "NEW_DATA_MODEL" in os.environ:
        # # only enabled for new data model
        #     if next_alarm_time is not None:
        #         # maybe this is only needed in the pm?
        #         # next_alarm_time -= timedelta(hours=12)  # go back to last referenced time
        #         message_body["payload"] = next_alarm_time
        message_segments.append(message_body)
    elif skip_data:
        message_segments.append({"type": "skip"})
    elif extracted_time is not None:
        message_segments.append({"type": "requested_alarm_time", "payload": extracted_time})
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
        if website_request:
            message_segments.append({"type": "website_request"})
    for thanks_version in THANKS_VERSIONS:
        if thanks_version in processed_msg:
            message_segments.append({"type": "thanks", "modifiers": {"emotion": "excited" if excited else "neutral"}})

    message_segments = [{**message, "raw": raw_message_str} for message in message_segments]
    return message_segments
