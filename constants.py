from string import Template

DAILY_MSG = Template("""Here’s your $time reminder.
[T] mark medication as taken
[S] skip this dose
If now isn’t a good time, you can also reply with
[1] to check in with you in 10 minutes,
[2] to check in in 30,
[3] to check in in an hour,
or any other time delay you prefer (“35 min”).
""")

FOLLOWUP_MSG = """Hello, checking in at your requested time.
[T] mark medication as taken
[S] skip this dose
If now isn’t a good time, you can also reply with
[1] to check in with you in 10 minutes,
[2] to check in in 30,
[3] to check in in an hour,
or any other time delay you prefer (“35 min”)."""

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

UNKNOWN_MSG = """Sorry, I can only understand the following commands right now:
[T] mark medication as taken
[S] skip this dose
[1] check in with you in 10 minutes
[2] to check in in 30
[3] to check in in an hour

Working hard on understanding more! 📚🧠
"""

ERROR_MSG = """Something went wrong. Please reach out to +1(360)450-8655 with a description of how you got this message. Thank you!"""

NO_DOSE_MSG = """There's no dose to be taken right now. If you've received this message in error, please reach out to +1(360)450-8655 with a description of your situation. Thank you!"""

REMINDER_TOO_LATE_MSG = Template("""Sorry, we can't schedule a reminder after your latest dose time, which is $time.""")

REMINDER_TOO_CLOSE_MSG = Template("""We can't schedule a reminder after your latest dose time of $time, so we've scheduled it right before, at $reminder_time. See you then!""")

MANUAL_TEXT_NEEDED_MSG = Template("""The phone number $number requires your manual intervention.""")