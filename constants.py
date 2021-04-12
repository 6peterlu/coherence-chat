from string import Template

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

TAKE_MSG_EXCITED = Template("""🕒 $time\nDose recorded! (:\n💊💊💊💊""")

SKIP_MSG = """Dose skipped. I won't send you any more reminders for this dose today."""

UNKNOWN_MSG = """I can understand the following commands:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour
[x] report an error
"I need help", "I'm confused"
a specific amount of time such as "2 hours", "20 minutes"
activities such as "eating dinner", "on a walk", etc.
"""

ERROR_MSG = """Something went wrong. Please text 'x' and I'll be notified."""

NO_DOSE_MSG = """There's no dose to be taken right now. If you've received this message in error, please text 'x' and I'll be notified."""

REMINDER_TOO_LATE_MSG = Template("""Sorry, I can't schedule a reminder after your latest dose time, which is $time.""")

REMINDER_TOO_CLOSE_MSG = Template("""I can't schedule a reminder after your latest dose time of $time, so I've scheduled it at $reminder_time. See you then!""")

MANUAL_TEXT_NEEDED_MSG = Template("""The phone number $number requires your manual intervention.""")

ACTION_MENU = """I can understand the following commands:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour
a specific amount of time such as "2 hours", "20 minutes"
activities such as "eating dinner", "on a walk", etc."""

USER_ERROR_REPORT = Template("""$phone_number has reported an error.""")

USER_ERROR_RESPONSE = """Thanks for reporting. I've noted the error and am working on it."""