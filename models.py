from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
from pytz import utc as pytzutc, timezone
from sqlalchemy import func

db = SQLAlchemy()

def get_time_now(tzaware=True):
    return datetime.now(pytzutc) if tzaware else datetime.utcnow()
# sqlalchemy models & deserializers

# new tables
dose_medication_linker = db.Table('dose_medication_linker',
    db.Column('dose_window_id', db.Integer, db.ForeignKey('dose_window.id')),
    db.Column('medication_id', db.Integer, db.ForeignKey('medication.id'))
)
class User(db.Model):
    __tablename__ = 'user'
    id = db.Column(db.Integer, primary_key=True)
    phone_number = db.Column(db.String(10), nullable=False)
    name = db.Column(db.String, nullable=False)
    dose_windows = db.relationship("DoseWindow", backref="user")
    doses = db.relationship("Medication", backref="user")
    events = db.relationship("EventLog", backref="user")
    manual_takeover = db.Column(db.Boolean, nullable=False)
    paused = db.Column(db.Boolean, nullable=False)
    timezone = db.Column(db.String, nullable=False)

    def __init__(self, phone_number, name, dose_windows=[], doses=[], events=[], manual_takeover=False, paused=False, timezone="US/Pacific"):
        self.phone_number = phone_number
        self.name = name
        self.dose_windows = dose_windows
        self.doses = doses
        self.events = events
        self.manual_takeover = manual_takeover
        self.paused = paused
        self.timezone = timezone

    @property
    def current_day_bounds(self):
        local_timezone = timezone(self.timezone)
        local_time_now = local_timezone.localize(get_time_now(tzaware=False))
        start_of_day = local_time_now.replace(hour=0, minute=0, second=0, microsecond=0)
        end_of_day = start_of_day + timedelta(days=1)
        return start_of_day, end_of_day


class DoseWindow(db.Model):
    __tablename__ = 'dose_window'
    id = db.Column(db.Integer, primary_key=True)
    # remmeber, UTC only
    day_of_week = db.Column(db.Integer, nullable=False)
    start_hour = db.Column(db.Integer, nullable=False)
    end_hour = db.Column(db.Integer, nullable=False)
    start_minute = db.Column(db.Integer, nullable=False)
    end_minute = db.Column(db.Integer, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medications = db.relationship("Medication", secondary=dose_medication_linker, back_populates="dose_windows")
    events = db.relationship("EventLog", backref="dose_window")
    active = db.Column(db.Boolean)

    def __init__(self, day_of_week, start_hour, start_minute, end_hour, end_minute, user_id, medications=[], events=[], active=True):
        self.day_of_week = day_of_week
        self.start_hour = start_hour
        self.start_minute = start_minute
        self.end_hour = end_hour
        self.end_minute = end_minute
        self.user_id = user_id
        self.medications = medications
        self.events = events
        self.active = active

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
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    medication_name = db.Column(db.String, nullable=False)
    instructions = db.Column(db.String)
    events = db.relationship("EventLog", backref="medication")
    dose_windows = db.relationship("DoseWindow", secondary=dose_medication_linker, back_populates="medications")
    active = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, medication_name, instructions="", events=[], dose_windows=[], active=True):
        self.user_id = user_id
        self.medication_name = medication_name
        self.instructions = instructions
        self.events = events
        self.dose_windows = dose_windows
        self.active = active

    def is_recorded_for_today(self, dose_window_obj, user_obj):
        start_of_day, end_of_day = user_obj.current_day_bounds
        relevant_medication_history_records = EventLog.query.filter(
            EventLog.dose_window_id == dose_window_obj.id,
            EventLog.medication_id == self.id,
            EventLog.event_time > start_of_day,
            EventLog.event_time < end_of_day
        ).all()
        return len(relevant_medication_history_records) > 0

class EventLog(db.Model):
    __tablename__ = 'event_log'
    id = db.Column(db.Integer, primary_key=True)
    event_type = db.Column(db.String, nullable=False)
    description = db.Column(db.String)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
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
