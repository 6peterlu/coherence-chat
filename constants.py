from string import Template

INITIAL_MSGS = [
    Template("""Here’s your $time reminder.\n"""),
    Template("""It's $time, which means it's time for your dose!\n"""),
    Template("""Hope you're having a great day. Just wanted to let you know that it's $time and remind you about your dose.\n"""),
    Template("""Hello 👋 You have a dose to take at $time.\n"""),
    Template("""Hey there, just wanted to let you know it's time for your $time dose.\n"""),
]

FOLLOWUP_MSGS = [
"""Hello, checking in at your requested time.
""",
"""Hey, hope you're having a great day. Just checking in again.
""",
"""Hello! Following up on my last message.
""",
"""Just wanted to see if now is a better time.
""",
"""Following up to see if you are free now!
"""
]

ABSENT_MSG = [
    """Hope you're having a great day. Just a friendly note to take your medication 😊\n""",
    """Hello, just wanted to make sure you remember to stick to your meds today!\n""",
    """You're doing great, and we hope you'll keep it up by taking your medication today 😊\n""",
    """Hope everything is going well. Just wanted to let you know you haven't marked your medication as taken yet!\n""",
    """We're here to support you in your medication habits!\n""",
    """Hello friend 😊 Wanted to check in about your medication.\n""",
]

BOUNDARY_MSG = """It's the end of the designated dose period. We've marked the dose as skipped."""

CONFIRMATION_MSG = Template("""Great, we'll text again at $time. See you then!""")

TAKE_MSG = """Awesome! We've recorded it for you. 💊"""

SKIP_MSG = """Skip confirmed."""

UNKNOWN_MSG = """I can only understand the following commands right now:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour
[x] report an error
activities such as "eating dinner", "on a walk", etc.

Working hard on understanding more! 📚🧠
"""

ERROR_MSG = """Something went wrong. Please text 'x' and we'll be notified."""

NO_DOSE_MSG = """There's no dose to be taken right now. If you've received this message in error, please text 'x' and we'll be notified."""

REMINDER_TOO_LATE_MSG = Template("""Sorry, we can't schedule a reminder after your latest dose time, which is $time.""")

REMINDER_TOO_CLOSE_MSG = Template("""We can't schedule a reminder after your latest dose time of $time, so we've scheduled it at $reminder_time. See you then!""")

MANUAL_TEXT_NEEDED_MSG = Template("""The phone number $number requires your manual intervention.""")

ACTION_MENU = """I can understand the following commands:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour
a specific amount of time such as "2 hours", "20 minutes"
activities such as "eating dinner", "on a walk", etc."""