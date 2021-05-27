import pytz
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.dialects import postgresql
from datetime import datetime, timedelta, timezone as dt_timezone
from pytz import utc as pytzutc, timezone
from marshmallow import Schema, fields
from marshmallow_enum import EnumField
from werkzeug.security import check_password_hash, generate_password_hash
from itsdangerous import (TimedJSONWebSignatureSerializer
                          as Serializer, BadSignature, SignatureExpired)
import os
import enum

db = SQLAlchemy()

def get_time_now(tzaware=True):
    return datetime.now(pytzutc) if tzaware else datetime.utcnow()


# sqlalchemy models & deserializers

dose_medication_linker = db.Table('dose_medication_linker',
    db.Column('dose_window_id', db.Integer, db.ForeignKey('dose_window.id', ondelete='CASCADE', name="dose_medication_linker_dose_window_fkey_custom")),
    db.Column('medication_id', db.Integer, db.ForeignKey('medication.id', ondelete='CASCADE', name="dose_medication_linker_medication_fkey_custom"))
)


# enum type for sqlalchemy integration, src: https://www.michaelcho.me/article/using-python-enums-in-sqlalchemy-models
class IntEnum(db.TypeDecorator):
    """
    Enables passing in a Python enum and storing the enum's *value* in the db.
    The default would have stored the enum's *name* (ie the string).
    """
    impl = db.Integer

    def __init__(self, enumtype, *args, **kwargs):
        super(IntEnum, self).__init__(*args, **kwargs)
        self._enumtype = enumtype

    def process_bind_param(self, value, _):
        if isinstance(value, int):
            return value

        return value.value

    def process_result_value(self, value, _):
        return self._enumtype(value)

class UserState(enum.Enum):
    INTRO = 'intro'
    DOSE_WINDOWS_REQUESTED = 'dose_windows_requested'
    DOSE_WINDOW_TIMES_REQUESTED = 'dose_window_times_requested'
    TIMEZONE_REQUESTED = 'timezone_requested'
    PAYMENT_METHOD_REQUESTED = 'payment_method_requested'
    PAUSED = 'paused'
    ACTIVE = 'active'
    SUBSCRIPTION_EXPIRED = 'subscription_expired'
    PAYMENT_VERIFICATION_PENDING = 'payment_verification_pending'  # TODO: deprecate this
class UserSecondaryState(enum.Enum):
    PAYMENT_VERIFICATION_PENDING = 'payment_verification_pending'

class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String, nullable=False)
    dose_windows = db.relationship("DoseWindow", backref="user", passive_deletes=True, cascade="delete, merge, save-update", order_by="DoseWindow.id.asc()")
    doses = db.relationship("Medication", backref="user", passive_deletes=True, cascade="delete, merge, save-update", order_by="Medication.id.asc()")
    events = db.relationship("EventLog", backref="user", order_by="EventLog.event_time.asc()", passive_deletes=True, cascade="delete, merge, save-update")
    manual_takeover = db.Column(db.Boolean, nullable=False)
    timezone = db.Column(db.String, nullable=False)
    password_hash = db.Column(db.String, nullable=True)
    tracked_health_metrics = db.Column(postgresql.ARRAY(db.String), default=[])
    pending_announcement = db.Column(db.String)
    onboarding_type = db.Column(db.String)  # "free trial", "standard", None
    end_of_service = db.Column(db.DateTime)
    state = db.Column(
        db.Enum(UserState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=False
    )
    secondary_state = db.Column(
        db.Enum(UserSecondaryState, values_callable=lambda obj: [e.value for e in obj]),
        nullable=True
    )
    stripe_customer_id = db.Column(db.String)  # cross reference for stripe customer object.
    early_adopter = db.Column(db.Boolean)  # just some special treats for our early users!
    secret_text_code = db.Column(db.Integer)  # 2FA codes

    def __init__(
        self,
        phone_number,
        name,
        dose_windows=[],
        doses=[],
        events=[],
        manual_takeover=False,
        timezone="US/Pacific",
        end_of_service=None,
        onboarding_type="standard",  # paying user
        state=UserState.INTRO
    ):
        self.phone_number = phone_number
        self.name = name
        self.dose_windows = dose_windows
        self.doses = doses
        self.events = events
        self.manual_takeover = manual_takeover
        self.timezone = timezone
        self.onboarding_type = onboarding_type
        self.end_of_service = end_of_service
        self.state = state
        self.early_adopter = False  # all new created users are False

    # TODO: determine bounds from dose window settings. for now, it's hardcoded to 4AM (which is not gonna work).
    @property
    def current_day_bounds(self):
        local_timezone = timezone(self.timezone)
        local_time_now = get_time_now().astimezone(local_timezone)
        if local_time_now.hour < 4:  # go back to previous day since you're after midnight
            local_time_now -= timedelta(days=1)
        start_of_day = local_time_now.replace(hour=4, minute=0, second=0, microsecond=0) # 4AM -> 4AM
        end_of_day = start_of_day + timedelta(days=1)
        return start_of_day, end_of_day

    @property
    def active_dose_windows(self):
        return list(filter(lambda dw: dw.active, self.dose_windows))

    def past_day_bounds(self, days_delta=0):  # negative is past days
        start_of_day, end_of_day = self.current_day_bounds
        return start_of_day + timedelta(days=days_delta), end_of_day + timedelta(days=days_delta)

    def get_day_delta(self, input_time):
        start_of_day, _ = self.current_day_bounds
        return (input_time - start_of_day).days

    def resume(self, scheduler, send_intro_text_new, send_upcoming_dose_message, silent=False):
        print("resume")
        print(self.state)
        text_sent = False
        if self.state == UserState.PAUSED:
            self.state = UserState.ACTIVE
            active_dose_windows = list(filter(lambda dw: dw.active, self.dose_windows))
            sorted_dose_windows = sorted(active_dose_windows, key=lambda dw: dw.next_start_date)
            print(active_dose_windows)
            for dw in sorted_dose_windows:
                print(dw.next_start_date)
            for i, dose_window in enumerate(sorted_dose_windows):
                dose_window.schedule_initial_job(scheduler, send_intro_text_new)
                if not silent:
                    print("not silent")
                    # send resume messages
                    if dose_window.within_dosing_period() and not dose_window.is_recorded():
                        print("sending intro text")
                        send_intro_text_new(dose_window.id, welcome_back=True)
                        text_sent = True
            if not text_sent and len(sorted_dose_windows) > 0:
                send_upcoming_dose_message(self, sorted_dose_windows[0])
            db.session.commit()

    def pause(self, scheduler, send_pause_message, silent=False):
        print("pause")
        if self.state == UserState.ACTIVE:
            self.state = UserState.PAUSED
            for dose_window in self.dose_windows:
                dose_window.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])
            if not silent:
                send_pause_message(self)
            db.session.commit()


    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
        self.secret_text_code = None
        db.session.commit()

    def verify_password(self, password):
        if not self.password_hash:
            return False  # if password is not set, no authing
        return check_password_hash(self.password_hash, password)

    def generate_auth_token(self, expiration = 2592000):  # 30 days
        s = Serializer(os.environ["TOKEN_SECRET"], expires_in = expiration)
        return s.dumps({ 'id': self.id })

    @staticmethod
    def verify_auth_token(token):
        s = Serializer(os.environ["TOKEN_SECRET"])
        try:
            data = s.loads(token)
        except SignatureExpired:
            return None # valid token, but expired
        except BadSignature:
            return None # invalid token
        user = User.query.get(data['id'])
        return user

    @property
    def already_sent_intro_today(self):
        start_of_day, end_of_day = self.current_day_bounds
        num_intro_events_today = EventLog.query.filter(
            EventLog.event_time >= start_of_day,
            EventLog.event_time < end_of_day,
            EventLog.event_type == "initial",
            EventLog.user == self
        ).count()  # count is no more efficient than actually querying; this can be optimized: https://stackoverflow.com/questions/14754994/why-is-sqlalchemy-count-much-slower-than-the-raw-query
        return num_intro_events_today > 0

    @property
    def charge_date(self):
        if self.end_of_service is None:
            return None
        return self.end_of_service - timedelta(days=1)

class DoseWindow(db.Model):
    __tablename__ = 'dose_window'
    id = db.Column(db.Integer, primary_key=True)
    # remember, UTC only
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    start_minute = db.Column(db.Integer, nullable=False)
    end_minute = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name="dose_window_user_fkey_custom"), nullable=False)
    medications = db.relationship("Medication", secondary=dose_medication_linker, back_populates="dose_windows", order_by="Medication.id.asc()")
    events = db.relationship("EventLog", backref="dose_window", order_by="EventLog.event_time.asc()")
    active = db.Column(db.Boolean)  # active dose windows can be interacted in, even if the bot is paused.

    def __init__(
        self, start_hour, start_minute, end_hour,
        end_minute, user_id
    ):
        self.start_hour = start_hour
        self.start_minute = start_minute
        self.end_hour = end_hour
        self.end_minute = end_minute
        self.user_id = user_id
        self.medications = []
        self.events = []
        self.active = True


    # flip active and schedule or remove jobs appropriately
    def toggle_active(self, scheduler_tuple=None):
        self.active = not self.active
        # need a scheduler object to take actions
        if scheduler_tuple is not None:
            scheduler, func_to_schedule = scheduler_tuple
            if self.active and scheduler_tuple and self.medications and not self.user.state == UserState.PAUSED:
                self.schedule_initial_job(scheduler, func_to_schedule)
            if not self.active and scheduler_tuple:
                self.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])
        db.session.commit()

    def deactivate(self, scheduler):
        if self.active:
            self.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])
            self.active = False
            db.session.commit()


    def valid_hour(self, hour):
        return hour >= 0 and hour <= 23

    def valid_minute(self, minute):
        return minute >= 0 and minute <= 59

    def edit_window(self, new_start_hour,
        new_start_minute, new_end_hour, new_end_minute,
        scheduler, send_intro_text_new, send_boundary_text_new
    ):
        currently_outgoing_jobs = self.within_dosing_period() and not self.is_recorded()
        if not self.valid_hour(new_start_hour) or not self.valid_minute(new_start_minute) or not self.valid_hour(new_end_hour) or not self.valid_minute(new_end_minute):
            return
        self.start_hour = new_start_hour
        self.start_minute = new_start_minute
        self.end_hour = new_end_hour
        self.end_minute = new_end_minute
        db.session.commit()
        # clear initial
        self.remove_jobs(scheduler, ["initial"])
        self.schedule_initial_job(scheduler, send_intro_text_new)
        if currently_outgoing_jobs:  # manage the jobs currently in flight
            if self.next_end_date - timedelta(days=1) < get_time_now():  # we're after the new end time, clear all jobs.
                self.remove_jobs(scheduler, ["followup", "absent", "boundary"])
            else:
                if self.next_start_date - timedelta(days=1) > get_time_now():  # we start after the current time, clear all jobs
                    self.remove_jobs(scheduler, ["followup", "absent", "boundary"])
                else:  # we're still in the range, so leave the existing jobs and just move the end one.
                    self.remove_jobs(scheduler, ["boundary"])
                    scheduler.add_job(f"{self.id}-boundary-new", send_boundary_text_new,
                        args=[self.id],
                        trigger="date",
                        run_date=self.next_end_date - timedelta(days=1),
                        misfire_grace_time=5*60
                    )


    def schedule_initial_job(self, scheduler, send_intro_text_new):
        if scheduler.get_job(f"{self.id}-initial-new") is None and not self.user.state == UserState.PAUSED:
            scheduler.add_job(
                f"{self.id}-initial-new",
                send_intro_text_new,
                trigger="interval",
                start_date=self.next_start_date,
                days=1,
                args=[self.id],
                misfire_grace_time=5*60
            )

    def remove_jobs(self, scheduler, jobs_list):
        for job in jobs_list:
            job_id = f"{self.id}-{job}-new"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)


    def jobs_scheduled(self, scheduler):
        job_id = f"{self.id}-initial-new"
        return scheduler.get_job(job_id) is not None


    def is_recorded(self, days_delta=0):
        for medication in self.medications:
            if not medication.is_recorded_for_day(self, days_delta=days_delta):
                return False
        return True

    def remove_boundary_event(self, days_delta=0):
        start_of_day, end_of_day = self.user.past_day_bounds(days_delta)
        EventLog.query.filter(
            EventLog.dose_window_id == self.id,
            EventLog.event_time >= start_of_day,
            EventLog.event_time < end_of_day,
            EventLog.event_type == "boundary"
        ).delete(synchronize_session=False)
        db.session.commit()


    @property
    def next_start_date(self):
        alarm_starttime = get_time_now().replace(hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0)
        if alarm_starttime < get_time_now():
            alarm_starttime += timedelta(days=1)
        return alarm_starttime

    @property
    def next_end_date(self):
        alarm_endtime = get_time_now().replace(hour=self.end_hour, minute=self.end_minute, second=0, microsecond=0)
        if alarm_endtime < get_time_now():
            alarm_endtime += timedelta(days=1)
        if alarm_endtime < self.next_start_date:
            alarm_endtime += timedelta(days=1)
        return alarm_endtime

    @property
    def bounds_for_current_day(self):
        start_of_day, end_of_day = self.user.current_day_bounds
        start_date = self.next_start_date
        while not (start_date < end_of_day and start_date > start_of_day):
            start_date -= timedelta(days=1)
        end_date = self.next_end_date
        while not (end_date < end_of_day and end_date >= start_of_day):
            end_date -= timedelta(days=1)
        return start_date, end_date


    def dosing_period_status(self, time=None, day_agnostic=False):
        time_to_compare = get_time_now() if time is None else time
        if day_agnostic:
            time_now = get_time_now()
            time_to_compare.replace(time_now.year, time_now.month, time_now.day)
        start_date, end_date = self.bounds_for_current_day
        if time_to_compare < start_date:
            return "before"
        elif time_to_compare >= start_date and time_to_compare < end_date:
            return "during"
        else:
            return "after"


    # TODO: deprecate
    def within_dosing_period(self, time=None, day_agnostic=False):
        time_to_compare = get_time_now() if time is None else time
        if day_agnostic:
            time_now = get_time_now()
            time_to_compare.replace(time_now.year, time_now.month, time_now.day)
        # boundary condition
        return self.next_end_date - timedelta(days=1) > time_to_compare and self.next_start_date - timedelta(days=1) <= time_to_compare



class Medication(db.Model):
    __tablename__ = 'medication'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name="medication_user_fkey_custom"), nullable=False)
    medication_name = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String)
    events = db.relationship("EventLog", backref="medication", order_by="EventLog.event_time.asc()")
    dose_windows = db.relationship("DoseWindow", secondary=dose_medication_linker, back_populates="medications", order_by="DoseWindow.id.asc()")
    active = db.Column(db.Boolean, nullable=False)

    def __init__(
        self,
        user_id,
        medication_name,
        scheduler_tuple=None,
        instructions=None,
        events=[],
        dose_windows=[],
        active=True,
    ):
        self.user_id = user_id
        self.medication_name = medication_name
        self.instructions = instructions
        self.events = events
        self.active = active
        for dose_window in dose_windows:
            associate_medication_with_dose_window(self, dose_window, scheduler_tuple=scheduler_tuple)

    def is_recorded_for_day(self, dose_window_obj, days_delta=0):
        start_of_day, end_of_day = self.user.past_day_bounds(days_delta)
        relevant_medication_history_records = EventLog.query.filter(
            EventLog.dose_window_id == dose_window_obj.id,
            EventLog.medication_id == self.id,
            EventLog.event_time >= start_of_day,
            EventLog.event_time < end_of_day,
            EventLog.event_type.in_(["take", "skip"])
        ).all()
        return len(relevant_medication_history_records) > 0


def deactivate_medication(scheduler, medication):
    medication.active = False
    dose_windows = [*medication.dose_windows]
    medication.dose_windows = []  # dissociate medication from all dose_windows
    db.session.flush()
    for dose_window in dose_windows:
        if dose_window.jobs_scheduled(scheduler) and not dose_window.medications:
            dose_window.remove_jobs(scheduler, ["initial", "absent", "boundary", "followup"])


def associate_medication_with_dose_window(medication, dose_window, scheduler_tuple=None):
    medication.dose_windows.append(dose_window)
    if scheduler_tuple:
        scheduler, func_to_schedule = scheduler_tuple
        dose_window.schedule_initial_job(scheduler, func_to_schedule)


def dissociate_medication_from_dose_window(scheduler, medication, dose_window):
    medication.dose_windows.remove(dose_window)
    db.session.flush()
    if dose_window.jobs_scheduled(scheduler) and not dose_window.medications:
        dose_window.remove_jobs(scheduler, ["initial", "absent", "boundary", "followup"])


class EventLog(db.Model):
    __tablename__ = 'event_log'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name="event_user_fkey_custom"))
    dose_window_id = db.Column(db.Integer, db.ForeignKey('dose_window.id'))
    medication_id = db.Column(db.Integer, db.ForeignKey('medication.id'))
    event_time = db.Column(db.DateTime, nullable=False)

    def __init__(self, event_type, user_id, dose_window_id, medication_id, event_time=None, description=None):
        self.event_type = event_type
        self.user_id = user_id
        self.dose_window_id = dose_window_id
        self.medication_id = medication_id
        self.event_time = get_time_now() if event_time is None else event_time
        self.description = description

    @property
    def aware_event_time(self):
        return self.event_time.replace(tzinfo=datetime.now().astimezone().tzinfo)


class Online(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    online = db.Column(db.Boolean)
    def __repr__(self):
        return f"<Online {id}>"


class LandingPageSignup(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    phone_number = db.Column(db.String)
    email = db.Column(db.String)
    trial_code = db.Column(db.String)
    signup_time = db.Column(db.DateTime)
    def __init__(self, name, phone_number, email, trial_code):
        self.name = name
        self.phone_number = phone_number
        self.email = email
        self.trial_code = trial_code
        self.signup_time = get_time_now()
    def __repr__(self):
        return f"<LandingPageSignup {id}>"


# marshmallow schemas
class UserSchema(Schema):
    id = fields.Integer()
    phone_number = fields.String()
    name = fields.String()
    manual_takeover = fields.Boolean()
    timezone = fields.String()
    dose_windows = fields.List(fields.Nested(
        lambda: DoseWindowSchema(exclude=("user", "medications"))
        ))
    doses = fields.List(fields.Nested(
        lambda: MedicationSchema(exclude=("user", "dose_windows"))
    ))
    pending_announcement = fields.String()
    onboarding_type = fields.String()
    state = EnumField(UserState, by_value=True)

class DoseWindowSchema(Schema):
    id = fields.Integer()
    start_hour = fields.Integer()
    start_minute = fields.Integer()
    end_hour = fields.Integer()
    end_minute = fields.Integer()
    user = fields.Nested(UserSchema(exclude=("dose_windows", "doses")))
    medications = fields.List(fields.Nested(lambda: MedicationSchema(exclude=("dose_windows", "user"))))
    active = fields.Boolean()


class MedicationSchema(Schema):
    id = fields.Integer()
    medication_name = fields.String()
    instructions = fields.String()
    active = fields.Boolean()
    dose_windows = dose_windows = fields.List(fields.Nested(
        DoseWindowSchema(exclude=("user", "medications"))
        ))
    user = fields.Nested(UserSchema(exclude=("dose_windows", "doses")))



class EventLogSchema(Schema):
    id = fields.Integer()
    event_type = fields.String()
    description = fields.String()
    event_time = fields.DateTime(format='%Y-%m-%dT%H:%M:%S+00:00')  # UTC time
    user = fields.Nested(UserSchema(exclude=("dose_windows", "doses")))
    medication = fields.Nested(MedicationSchema(exclude=("dose_windows", "user")))
    dose_window = fields.Nested(DoseWindowSchema(exclude=("user", "medications")))

# class LandingPageSignup(db.Model):
#     id = db.Column(db.Integer, primary_key=True)
#     name = db.Column(db.String)
#     phone_number = db.Column(db.String)
#     email = db.Column(db.String)
#     trial_code = db.Column(db.String)
#     def __repr__(self):
#         return f"<LandingPageSignup {id}>"
class LandingPageSignupSchema(Schema):
    id = fields.Integer()
    name = fields.String()
    phone_number = fields.String()
    email = fields.String()
    trial_code = fields.String()
    signup_time = fields.DateTime(format='%Y-%m-%dT%H:%M:%S+00:00')