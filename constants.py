from string import Template

MORNING_PREFIXES = [
    "Good morning!",
    "Hope your day is off to a great start.",
    "Looking forward to a great day together."
]

AFTERNOON_PREFIXES = [
    "Hope your day is going well so far.",
    "Hope you had a great lunch.",
    "Good afternoon!"
]

EVENING_PREFIXES = [
    "Good evening!",
    "Hope you got to catch the sunset today!",
    "Last medication for the day!"
]

TIME_OF_DAY_PREFIX_MAP = {
    "morning": MORNING_PREFIXES,
    "afternoon": AFTERNOON_PREFIXES,
    "evening": EVENING_PREFIXES
}

WELCOME_BACK_MESSAGES = [
    "It's great to see you again!",
    "Welcome back!",
    "Looking forward to helping you out with your medication.",
    "Glad to see you again."
]

FUTURE_MESSAGE_SUFFIXES = [
    Template("""I'll be back at $time to check in."""),
    Template("""See you at $time!"""),
    Template("""I'll text again at $time about your dose.""")
]

PAUSE_MESSAGE = "You've paused me, so I won't text you about your medications until I am resumed. You can resume me at https://coherence-chat.herokuapp.com/ at any time. You can still let me know when you've taken or skipped a dose, and I will still record it for you."

INITIAL_SUFFIXES = [
    Template("""Here’s your $time reminder.\n"""),
    Template("""It's $time, which means it's time for your dose!\n"""),
    Template("""Are you ready for your $time dose?\n"""),
    Template("""Let me know if you can take your $time dose.\n"""),
    Template("""Just wanted to let you know it's time for your $time dose.\n"""),
    Template("""Just wanted to let you know that it's $time and remind you about your dose.\n""")
]

INITIAL_MSGS = [
    Template("""Here’s your $time reminder.\n"""),
    Template("""It's $time, which means it's time for your dose!\n"""),
    Template("""Hope you're having a great day. Just wanted to let you know that it's $time and remind you about your dose.\n"""),
    Template("""Hello 👋 You have a dose to take at $time.\n"""),
    Template("""Hey there, just wanted to let you know it's time for your $time dose.\n"""),
    Template("""Are you ready for your $time dose?\n"""),
    Template("""Let me know if you can take your $time dose.\n"""),
]

FOLLOWUP_MSGS = [
    """Hello, checking in at your requested time.\n""",
    """Hey, hope you're having a great day. Just checking in again.\n""",
    """Hello! Following up on my last message.\n""",
    """Just wanted to see if now is a better time.\n""",
    """Following up to see if you are free now!\n""",
    """Let me know if you're free now!\n"""
]

ABSENT_MSGS = [
    """Hope you're having a great day. Just a friendly note to take your medication.\n""",
    """Hello, just wanted to make sure you remember to stick to your meds today!\n""",
    """You're doing great, and I hope you'll keep it up by taking your medication today.\n""",
    """Hope everything is going well. Just wanted to let you know you haven't marked your medication as taken yet!\n""",
    """I'm here to support you in your medication habits! Just wanted to see if you've taken your medication yet.\n""",
    """Hello friend! Wanted to check in about your medication.\n""",
    """I haven't gotten a record of your dose yet, so please let us know if you've taken it.\n""",
]

BOUNDARY_MSG = """It's the end of the designated dose period. I've marked the dose as missed."""

CLINICAL_BOUNDARY_MSG = Template("""It's $time, so here's a reminder not to take your medication after this point.""")

CONFIRMATION_MSG = Template("""Great, I'll text again at $time. See you then!""")

TAKE_MSG = Template("""🕒 $time\nDose recorded.\n💊💊💊💊""")

TAKE_MSG_EXCITED = Template("""🕒 $time\nDose recorded! 🎉\n💊💊💊💊""")

SKIP_MSG = """Dose skipped."""

UNKNOWN_MSG = """You can reply
"T" to mark medication as taken
"S" to skip this dose
"1" to check in with you in 10 minutes
"2" to check in in 30
"3" to check in in an hour
"x" to report an error
"w" to get the website link
"I need help", "I'm confused"
a specific amount of time such as "2 hours", "20 minutes"
activities such as "eating dinner", "on a walk", etc.

If you need further support, please text us at (650) 667-1146‬, and we'll back to you within 1 business day.
"""

ERROR_MSG = """Something went wrong. Please text 'x' and I'll be notified."""

REMINDER_OUT_OF_RANGE_MSG = """I can tell you're trying to set a reminder, but there's no dose to be reminded about right now. You're good to go!"""

ACTION_OUT_OF_RANGE_MSG = """Thanks for letting me know. I don't have an active dose for you right now, but I'll look into it and make sure to record your doses correctly."""

REMINDER_TOO_LATE_MSG = Template("""Sorry, I can't schedule a reminder after your latest dose time, which is $time.""")

REMINDER_TOO_CLOSE_MSG = Template("""I can't schedule a reminder after your latest dose time of $time, so I've scheduled it at $reminder_time. See you then!""")

MANUAL_TEXT_NEEDED_MSG = Template("""The phone number $number requires your manual intervention.""")

ACTION_MENU = """You can reply
"T" to mark medication as taken
"S" to skip this dose
"1" to check in with you in 10 minutes
"2" to check in in 30
"3" to check in in an hour
a specific amount of time such as "2 hours", "20 minutes"
activities such as "eating dinner", "on a walk", etc."""

USER_ERROR_REPORT = Template("""$phone_number has reported an error.""")

USER_ERROR_RESPONSE = """Thanks for reporting. I've noted the error and am working on it."""

SECRET_CODE_MESSAGE = Template("""Your secret code for Coherence is $code. Don't share it with anyone!""")

THANKS_MESSAGES = [
    "No problem, glad to help.",
    "Happy to help! You're doing great.",
    "Glad to be helpful!",
    "Glad I could help out!"
]

ALREADY_RECORDED = "We already have a record of this dose. If you'd like to edit it, please go to https://www.coherence-chat.herokuapp.com and tap on the current day."

REQUEST_WEBSITE = "You can access your medication take history and much more at https://coherence-chat.herokuapp.com. Also, you can text us at our customer service number (650) 667-1146‬, and we'll back to you within 1 business day."