from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta, timezone as dt_timezone
from pytz import utc as pytzutc, timezone
from marshmallow import Schema, fields

db = SQLAlchemy()

def get_time_now(tzaware=True):
    return datetime.now(pytzutc) if tzaware else datetime.utcnow()
# sqlalchemy models & deserializers

# new tables
dose_medication_linker = db.Table('dose_medication_linker',
    db.Column('dose_window_id', db.Integer, db.ForeignKey('dose_window.id', ondelete='CASCADE', name="dose_medication_linker_dose_window_fkey_custom")),
    db.Column('medication_id', db.Integer, db.ForeignKey('medication.id', ondelete='CASCADE', name="dose_medication_linker_medication_fkey_custom"))
)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(10), nullable=False, unique=True)
    name = db.Column(db.String, nullable=False)
    dose_windows = db.relationship("DoseWindow", backref="user", passive_deletes=True)
    doses = db.relationship("Medication", backref="user", passive_deletes=True)
    events = db.relationship("EventLog", backref="user", order_by="EventLog.event_time.asc()", passive_deletes=True)
    manual_takeover = db.Column(db.Boolean, nullable=False)
    paused = db.Column(db.Boolean, nullable=False)
    timezone = db.Column(db.String, nullable=False)

    def __init__(
        self,
        phone_number,
        name,
        dose_windows=[],
        doses=[],
        events=[],
        manual_takeover=False,
        paused=False,
        timezone="US/Pacific",
    ):
        self.phone_number = phone_number
        self.name = name
        self.dose_windows = dose_windows
        self.doses = doses
        self.events = events
        self.manual_takeover = manual_takeover
        self.paused = paused
        self.timezone = timezone

    # TODO: determine bounds from dose window settings. for now, it's hardcoded to midnight (which is not gonna work).
    @property
    def current_day_bounds(self):
        local_timezone = timezone(self.timezone)
        local_time_now = local_timezone.localize(get_time_now(tzaware=False))
        start_of_day = local_time_now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return start_of_day, end_of_day

    def toggle_pause(self, scheduler_tuple):
        self.paused = not self.paused
        for dose_window in self.dose_windows:
            dose_window.remove_jobs(scheduler_tuple[0], ["initial", "followup", "boundary", "absent"])
            if dose_window.active:
                if self.paused:
                    print("removing jobs")
                else:
                    dose_window.schedule_initial_job(*scheduler_tuple)

class DoseWindow(db.Model):
    __tablename__ = 'dose_window'
    id = db.Column(db.Integer, primary_key=True)
    # remember, UTC only
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    start_minute = db.Column(db.Integer, nullable=False)
    end_minute = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name="dose_window_user_fkey_custom"), nullable=False)
    medications = db.relationship("Medication", secondary=dose_medication_linker, back_populates="dose_windows")
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
            if self.active and scheduler_tuple and self.medications and not self.user.paused:
                self.schedule_initial_job(scheduler, func_to_schedule)
            if not self.active and scheduler_tuple:
                self.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])


    def schedule_initial_job(self, scheduler, func_to_schedule):
        if scheduler.get_job(f"{self.id}-initial-new") is None and not self.user.paused:
            scheduler.add_job(
                f"{self.id}-initial-new",
                func_to_schedule,
                trigger="interval",
                start_date=self.next_start_date,
                days=1,
                args=[self.id],
                misfire_grace_time=5*60
            )

    def remove_jobs(self, scheduler, jobs_list):
        scheduler.remove_job(f"{self.id}-initial-new")
        # for job in jobs_list:
        #     job_id = f"{self.id}-{job}-new"
        #     if scheduler.get_job(job_id):
        #         scheduler.remove_job(job_id)


    def jobs_scheduled(self, scheduler):
        job_id = f"{self.id}-initial-new"
        return scheduler.get_job(job_id) is not None


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

    def within_dosing_period(self, time=None):
        time_to_compare = get_time_now() if time is None else time
        # boundary condition
        return self.next_end_date - timedelta(days=1) > time_to_compare and self.next_start_date - timedelta(days=1) < time_to_compare


class Medication(db.Model):
    __tablename__ = 'medication'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE', name="medication_user_fkey_custom"), nullable=False)
    medication_name = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String)
    events = db.relationship("EventLog", backref="medication", order_by="EventLog.event_time.asc()")
    dose_windows = db.relationship("DoseWindow", secondary=dose_medication_linker, back_populates="medications")
    active = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, medication_name, scheduler_tuple=None, instructions=None, events=[], dose_windows=[], active=True):
        self.user_id = user_id
        self.medication_name = medication_name
        self.instructions = instructions
        self.events = events
        self.active = active
        for dose_window in dose_windows:
            associate_medication_with_dose_window(self, dose_window, scheduler_tuple=scheduler_tuple)
    # TODO: unit test this
    def is_recorded_for_today(self, dose_window_obj):
        start_of_day, end_of_day = self.user.current_day_bounds
        relevant_medication_history_records = EventLog.query.filter(
            EventLog.dose_window_id == dose_window_obj.id,
            EventLog.medication_id == self.id,
            EventLog.event_time > start_of_day,
            EventLog.event_time < end_of_day
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
        print("calling schedule initial job")
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


# old tables
class Dose(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    start_minute = db.Column(db.Integer, nullable=False)
    end_minute = db.Column(db.Integer, nullable=False)
    patient_name = db.Column(db.String(80), nullable=False)
    phone_number = db.Column(db.String(13), nullable=False)  # +11234567890
    medication_name = db.Column(db.String(80), nullable=True)
    active = db.Column(db.Boolean)

    # TODO: extend this repr to include all fields
    def __repr__(self):
        return '<Dose %r>' % self.patient_name

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

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

    def within_dosing_period(self, time=None):
        time_to_compare = get_time_now() if time is None else time
        # boundary condition
        return self.next_end_date - timedelta(days=1) > time_to_compare and self.next_start_date - timedelta(days=1) < time_to_compare

    def already_recorded(self):
        matching_events = Event.query.filter(
            Event.description == str(self.id),
            Event.event_type.in_(["take", "skip"]),
            Event.event_time > self.next_start_date - timedelta(days=1),
            Event.event_time < self.next_end_date - timedelta(days=1)
        ).all()
        if len(matching_events) > 0:
            return True
        return False


class Reminder(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    dose_id = db.Column(db.Integer)
    send_time = db.Column(db.DateTime, nullable=False)
    reminder_type = db.Column(db.String(10), nullable=False)  # using string for readability

    def __repr__(self):
        return f"<Reminder {id}>"
    def as_dict(self):
       return_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       return_dict["send_time"] = self.send_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
       return return_dict

class Online(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    online = db.Column(db.Boolean)
    def __repr__(self):
        return f"<Online {id}>"

class Concept(db.Model):
    name = db.Column(db.String, primary_key=True)  # must be unique
    time_range_start = db.Column(db.Integer)  # in minutes
    time_range_end = db.Column(db.Integer)  # in minutes

    def as_dict(self):
       return {c.name: getattr(self, c.name) for c in self.__table__.columns}

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String, nullable=False)
    event_time = db.Column(db.DateTime, nullable=False)
    phone_number = db.Column(db.String(13), nullable=False)
    description = db.Column(db.String)

    def as_dict(self):
       return_dict = {c.name: getattr(self, c.name) for c in self.__table__.columns}
       return_dict["event_time"] = self.event_time.replace(tzinfo=datetime.now().astimezone().tzinfo)
       return return_dict

    @property
    def aware_event_time(self):
        return self.event_time.replace(tzinfo=datetime.now().astimezone().tzinfo)

# list of users that have all messages manually responded to
class ManualTakeover(db.Model):
    phone_number = db.Column(db.String(13), primary_key=True)

# list of users that have paused the reminder service
class PausedService(db.Model):
    phone_number = db.Column(db.String(13), primary_key=True)


# marshmallow schemas
class UserSchema(Schema):
    id = fields.Integer()
    phone_number = fields.String()
    name = fields.String()
    manual_takeover = fields.Boolean()
    paused = fields.Boolean()
    timezone = fields.String()
    dose_windows = fields.List(fields.Nested(
        lambda: DoseWindowSchema(exclude=("user", "events", "medications"))
        ))
    doses = fields.List(fields.Nested(
        lambda: MedicationSchema(exclude=("user", "dose_windows", "events"))
    ))
    events = fields.List(fields.Nested(
        lambda: EventLogSchema(exclude=("user", "dose_window", "medication"))
    ))

class DoseWindowSchema(Schema):
    id = fields.Integer()
    start_hour = fields.Integer()
    start_minute = fields.Integer()
    end_hour = fields.Integer()
    end_minute = fields.Integer()
    user = fields.Nested(UserSchema(exclude=("dose_windows", "events", "doses")))
    medications = fields.List(fields.Nested(lambda: MedicationSchema(exclude=("dose_windows", "user", "events"))))
    events = fields.List(fields.Nested(lambda: EventLogSchema(exclude=("user", "dose_window", "medication"))))
    active = fields.Boolean()


class MedicationSchema(Schema):
    id = fields.Integer()
    medication_name = fields.String()
    instructions = fields.String()
    active = fields.Boolean()
    events = fields.List(fields.Nested(lambda: EventLogSchema(exclude=("user", "dose_window", "medication"))))
    dose_windows = dose_windows = fields.List(fields.Nested(
        DoseWindowSchema(exclude=("user", "events", "medications"))
        ))
    user = fields.Nested(UserSchema(exclude=("dose_windows", "events", "doses")))



class EventLogSchema(Schema):
    id = fields.Integer()
    event_type = fields.String()
    description = fields.String()
    event_time = fields.DateTime(format='%Y-%m-%dT%H:%M:%S+00:00')  # UTC time
    user = fields.Nested(UserSchema(exclude=("dose_windows", "events", "doses")))
    medication = fields.Nested(MedicationSchema(exclude=("dose_windows", "user", "events")))
    dose_window = fields.Nested(DoseWindowSchema(exclude=("user", "events", "medications")))