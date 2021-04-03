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

ABSENT_MSG = """Hope you're having a great day. Just a friendly note to take your medication 😊
[T] mark medication as taken
[S] skip this dose
If now isn’t a good time, you can also reply with
[1] to check in with you in 10 minutes,
[2] to check in in 30,
[3] to check in in an hour,
or any other time delay you prefer (“35 min”)."""

BOUNDARY_MSG = """It's the end of the designated dose period. We've marked the dose as skipped."""

CONFIRMATION_MSG = Template("""Great, we'll check in again at $time. See you then!""")

TAKE_MSG = """Awesome work. Take confirmed."""

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

ACTION_MENU = """You can reply with the following commands:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour
[x] report an error
activities such as "eating dinner", "on a walk", etc."""