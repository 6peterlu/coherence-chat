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
    dose_windows = db.relationship("DoseWindow", backref="user", passive_deletes=True, cascade="delete, merge, save-update", order_by="DoseWindow.id.asc()")
    doses = db.relationship("Medication", backref="user", passive_deletes=True, cascade="delete, merge, save-update", order_by="Medication.id.asc()")
    events = db.relationship("EventLog", backref="user", order_by="EventLog.event_time.asc()", passive_deletes=True, cascade="delete, merge, save-update")
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

    # TODO: determine bounds from dose window settings. for now, it's hardcoded to 2AM (which is not gonna work).
    @property
    def current_day_bounds(self):
        local_timezone = timezone(self.timezone)
        local_time_now = get_time_now().astimezone(local_timezone)
        start_of_day = local_time_now.replace(hour=2, minute=0, second=0, microsecond=0) # 2AM -> 2AM
        end_of_day = start_of_day + timedelta(days=1)
        return start_of_day, end_of_day

    def resume(self, scheduler, send_intro_text_new, send_upcoming_dose_message):
        if self.paused:
            self.paused = False
            sorted_dose_windows = sorted(self.dose_windows, key=lambda dw: dw.next_start_date)
            for i, dose_window in enumerate(sorted_dose_windows):
                if dose_window.active:
                    dose_window.schedule_initial_job(scheduler, send_intro_text_new)
                    # send resume messages
                    if dose_window.within_dosing_period() and not dose_window.is_recorded_for_today:
                        send_intro_text_new(dose_window.id, welcome_back=True)
                    elif i == 0:  # upcoming dose
                        send_upcoming_dose_message(self, dose_window)
            db.session.commit()

    def pause(self, scheduler, send_pause_message):
        if not self.paused:
            self.paused = True
            for dose_window in self.dose_windows:
                dose_window.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])
            send_pause_message(self)
            db.session.commit()

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
            if self.active and scheduler_tuple and self.medications and not self.user.paused:
                self.schedule_initial_job(scheduler, func_to_schedule)
            if not self.active and scheduler_tuple:
                self.remove_jobs(scheduler, ["initial", "followup", "boundary", "absent"])
        db.session.commit()

    def valid_hour(self, hour):
        return hour >= 0 and hour <= 23

    def valid_minute(self, minute):
        return minute >= 0 and minute <= 59

    def edit_window(self, new_start_hour,
        new_start_minute, new_end_hour, new_end_minute,
        scheduler, send_intro_text_new, send_boundary_text_new
    ):
        currently_outgoing_jobs = self.within_dosing_period() and not self.is_recorded_for_today
        if not self.valid_hour(new_start_hour) or not self.valid_minute(new_start_minute) or not self.valid_hour(new_end_hour) or not self.valid_minute(new_end_minute):
            print("invalid...rejecting")
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
        if scheduler.get_job(f"{self.id}-initial-new") is None and not self.user.paused:
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
        print("removing jobs")
        for job in jobs_list:
            job_id = f"{self.id}-{job}-new"
            if scheduler.get_job(job_id):
                scheduler.remove_job(job_id)


    def jobs_scheduled(self, scheduler):
        job_id = f"{self.id}-initial-new"
        return scheduler.get_job(job_id) is not None


    @property
    def is_recorded_for_today(self):
        for medication in self.medications:
            if not medication.is_recorded_for_today(self):
                return False
        return True


    @property
    def next_start_date(self):
        alarm_starttime = get_time_now().replace(hour=self.start_hour, minute=self.start_minute, second=0, microsecond=0)
        if alarm_starttime < get_time_now():
            alarm_starttime += timedelta(days=1)
        return alarm_starttime
    @property
    def next_end_date(self):
        print(self.end_hour)
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
    dose_windows = db.relationship("DoseWindow", secondary=dose_medication_linker, back_populates="medications", order_by="DoseWindow.id.asc()")
    active = db.Column(db.Boolean, nullable=False)

    def __init__(self, user_id, medication_name, scheduler_tuple=None, instructions=None, events=[], dose_windows=[], active=True):
        self.user_id = user_id
        self.medication_name = medication_name
        self.instructions = instructions
        self.events = events
        self.active = active
        for dose_window in dose_windows:
            associate_medication_with_dose_window(self, dose_window, scheduler_tuple=scheduler_tuple)

    def is_recorded_for_today(self, dose_window_obj):
        start_of_day, end_of_day = self.user.current_day_bounds
        relevant_medication_history_records = EventLog.query.filter(
            EventLog.dose_window_id == dose_window_obj.id,
            EventLog.medication_id == self.id,
            EventLog.event_time > start_of_day,
            EventLog.event_time < end_of_day,
            EventLog.event_type.in_(["take", "skip", "boundary"])
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


# marshmallow schemas
class UserSchema(Schema):
    id = fields.Integer()
    phone_number = fields.String()
    name = fields.String()
    manual_takeover = fields.Boolean()
    paused = fields.Boolean()
    timezone = fields.String()
    dose_windows = fields.List(fields.Nested(
        lambda: DoseWindowSchema(exclude=("user", "medications"))
        ))
    doses = fields.List(fields.Nested(
        lambda: MedicationSchema(exclude=("user", "dose_windows"))
    ))

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