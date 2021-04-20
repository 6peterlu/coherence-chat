# handler for all regexing and message segmentation (later, more stuff I hope)
import string
import re

MEDICATION_TAKEN_REGEX = '(taken|take|t)\s?(?:(?:at|@)\s?(\S+)?)?'

COMPUTING_PREFIX = "Computing ideal reminder time...done."

RECOGNIZED_ACTIVITIES = {
    "brunch": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have a great brunch! We'll check in later."},
    "dinner": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have a great dinner! We'll check in later."},
    "lunch": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have a great lunch! We'll check in later."},
    "breakfast": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have a great breakfast! We'll check in later."},
    "eating": {"type": "long", "payload": f"{COMPUTING_PREFIX} Enjoy your meal! We'll check in later."},
    "meeting": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have a productive meeting! We'll check in later."},
    "out": {"type": "long", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in later."},
    "busy": {"type": "long", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in later."},
    "later": {"type": "long", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in later."},
    "reading": {"type": "long", "payload": f"{COMPUTING_PREFIX} Enjoy your book, we'll check in later."},
    "sleeping": {"type": "long", "payload": f"{COMPUTING_PREFIX} Sleep well! We'll see you later."},
    "golf": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later."},
    "tennis": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later."},
    "swimming": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later."},
    "basketball": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later."},
    "tv": {"type": "long", "payload": f"{COMPUTING_PREFIX} Have fun, we'll check in later."},
    "working": {"type": "long", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in later."},
    "walking": {"type": "short", "payload": f"{COMPUTING_PREFIX} Enjoy your walk! We'll check in later."},
    "walk": {"type": "short", "payload": f"{COMPUTING_PREFIX} Enjoy your walk! We'll check in later."},
    "bathroom": {"type": "short", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in in a bit."},
    "run":  {"type": "short", "payload": f"{COMPUTING_PREFIX} Have a great run! We'll see you later."},
    "running":  {"type": "short", "payload": f"{COMPUTING_PREFIX} Have a great run! We'll see you later."},
    "basketball":  {"type": "short", "payload": f"{COMPUTING_PREFIX} Have fun out there! We'll see you later."},
    "shower":  {"type": "short", "payload": f"{COMPUTING_PREFIX} No problem, we'll check in later."},
    "phone": {"type": "short", "payload": f"{COMPUTING_PREFIX} Have a great call! We'll check in later."},
    "call": {"type": "short", "payload": f"{COMPUTING_PREFIX} Have a great call! We'll check in later."},
}

def segment_message(raw_message_str):
    processed_msg = raw_message_str.lower().strip()
    excited = "!" in processed_msg
    # remove all punctuation
    processed_msg = processed_msg.translate(str.maketrans("", "", string.punctuation))
    # remove brackets
    processed_msg = processed_msg.replace("[", "").replace("]", "")
    taken_data = re.findall(MEDICATION_TAKEN_REGEX, raw_message_str)
    return taken_data
