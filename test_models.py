import pytest
from unittest import mock
from datetime import datetime
from pytz import utc
from freezegun import freeze_time


from models import (
    EventLog,
    # schemas
    UserSchema,
    DoseWindowSchema,
    MedicationSchema,
    associate_medication_with_dose_window,
    deactivate_medication,
    dissociate_medication_from_dose_window
)

def test_function(*_, **__):
    pass

@pytest.fixture
def take_event_record(db_session, dose_window_record, medication_record):
    event_obj = EventLog(
        event_type="take",
        user_id=dose_window_record.user.id,
        event_time=datetime(2012, 1, 1, 10+7, 23, 15),
        medication_id=medication_record.id,
        dose_window_id=dose_window_record.id
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj


@pytest.fixture
def boundary_event_record(db_session, dose_window_record):
    event_obj = EventLog(
        event_type="boundary",
        user_id=dose_window_record.user.id,
        event_time=datetime(2012, 1, 1, 10+7, 23, 15),
        medication_id=None,
        dose_window_id=dose_window_record.id
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj

# testing schemas
def test_user_schema(user_record, dose_window_record, medication_record, medication_record_2):
    user_schema = UserSchema()
    assert user_schema.dump(user_record) == {
        "dose_windows": [
            {
            "active": True,
            "end_hour": 18,
            "end_minute": 0,
            "id": dose_window_record.id,
            "start_hour": 16,
            "start_minute": 0
            }
        ],
        "doses": [
            {
                "active": True,
                "id": medication_record.id,
                "instructions": None,
                "medication_name": "Zoloft"
            },
            {
                "active": True,
                "id": medication_record_2.id,
                "instructions": None,
                "medication_name": "Lisinopril"
            }
        ],
        "id": user_record.id,
        "manual_takeover": False,
        "name": "Peter",
        "paused": False,
        "phone_number": "3604508655",
        "timezone": "US/Pacific"
    }

def test_dose_window_schema(dose_window_record, medication_record, medication_record_2, user_record):
    dose_window_schema = DoseWindowSchema()
    assert dose_window_schema.dump(dose_window_record) == {
        'start_hour': 16,
        'active': True,
        'medications': [
            {
                'active': True,
                'id': medication_record.id,
                'medication_name': 'Zoloft',
                'instructions': None
            }, {
                'active': True,
                'id': medication_record_2.id,
                'medication_name': 'Lisinopril',
                'instructions': None
            }
        ],
        'end_minute': 0,
        'start_minute': 0,
        'id': dose_window_record.id,
        'end_hour': 18,
        'user': {
            'name': 'Peter',
            'manual_takeover': False,
            'phone_number': '3604508655',
            'id': user_record.id,
            'paused': False,
            'timezone': 'US/Pacific'
        }
    }

def test_dose_window_scheduler(dose_window_record, medication_record, scheduler):
    # assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is None
    dose_window_record.schedule_initial_job(scheduler, test_function)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    dose_window_record.remove_jobs(scheduler, ["initial", "absent", "boundary", "followup"])
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is None

@freeze_time("2012-01-01 13:00:00")
def test_edit_dose_window_when_not_in_window(dose_window_record, medication_record, scheduler):
    stub_fn = mock.Mock()
    dose_window_record.edit_window(11, 0, 12, 0, scheduler, stub_fn, stub_fn)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-boundary-new") is None

@freeze_time("2012-01-01 17:00:00")
def test_edit_dose_window_when_in_window(dose_window_record, medication_record, scheduler):
    stub_fn = mock.Mock()
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    dose_window_record.edit_window(11, 0, 12, 0, scheduler, stub_fn, stub_fn)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-boundary-new") is None
    assert scheduler.get_job(f"{dose_window_record.id}-followup-new") is None
    assert scheduler.get_job(f"{dose_window_record.id}-absent-new") is None


@freeze_time("2012-01-01 17:00:00")
def test_edit_dose_window_when_in_window_boundary_later(dose_window_record, medication_record, scheduler):
    stub_fn = mock.Mock()
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    dose_window_record.edit_window(19, 0, 23, 0, scheduler, stub_fn, stub_fn)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-boundary-new") is None
    assert scheduler.get_job(f"{dose_window_record.id}-followup-new") is None
    assert scheduler.get_job(f"{dose_window_record.id}-absent-new") is None


@freeze_time("2012-01-01 17:00:00")
def test_edit_dose_window_when_in_window_boundary_later_start_earlier(dose_window_record, medication_record, scheduler):
    stub_fn = mock.Mock()
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn,
        args=[dose_window_record.id],
        trigger="date",
        run_date=datetime(2012, 1, 1, 18, tzinfo=utc),
        misfire_grace_time=5*60
    )
    dose_window_record.edit_window(11, 0, 23, 0, scheduler, stub_fn, stub_fn)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-boundary-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-followup-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-absent-new") is not None


@freeze_time("2012-01-01 17:00:00")
def test_edit_dose_window_when_in_window(dose_window_record, medication_record, scheduler):
    stub_fn = mock.Mock()
    dose_window_record.edit_window(11, 0, 12, 0, scheduler, stub_fn, stub_fn)
    assert scheduler.get_job(f"{dose_window_record.id}-initial-new") is not None
    assert scheduler.get_job(f"{dose_window_record.id}-boundary-new") is None


@freeze_time("2012-01-01 17:00:00")
def test_toggle_user_pause(dose_window_record_for_paused_user, user_record_paused, medication_record_for_paused_user, scheduler):
    send_upcoming_dose_message = mock.Mock()
    send_intro_text = mock.Mock()
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is None
    user_record_paused.resume(scheduler, send_intro_text, send_upcoming_dose_message)
    assert send_intro_text.called
    assert not send_upcoming_dose_message.called
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is not None
    user_record_paused.pause(scheduler, test_function)
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is None

@freeze_time("2012-01-01 12:00:00")
def test_toggle_user_pause_out_of_range(dose_window_record_for_paused_user, user_record_paused, medication_record_for_paused_user, scheduler):
    send_upcoming_dose_message = mock.Mock()
    send_intro_text = mock.Mock()
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is None
    user_record_paused.resume(scheduler, send_intro_text, send_upcoming_dose_message)
    assert not send_intro_text.called
    assert send_upcoming_dose_message.called
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is not None
    user_record_paused.pause(scheduler, test_function)
    assert scheduler.get_job(f"{dose_window_record_for_paused_user.id}-initial-new") is None



def test_medication_schema(dose_window_record, medication_record, user_record):
    medication_schema = MedicationSchema()
    assert medication_schema.dump(medication_record) == {
        'instructions': None,
        'user': {
            'phone_number': '3604508655',
            'name': 'Peter',
            'paused': False,
            'manual_takeover': False,
            'id': user_record.id,
            'timezone': 'US/Pacific'
        },
        'active': True,
        'id': medication_record.id,
        'medication_name': 'Zoloft',
        'dose_windows': [
            {
                'end_minute': 0,
                'start_minute': 0,
                'active': True,
                'id': dose_window_record.id,
                'start_hour': 16,
                'end_hour': 18
            }
        ]
    }

def test_medication_is_not_recorded(dose_window_record, medication_record):
    assert not medication_record.is_recorded_for_day(dose_window_record)


@freeze_time("2012-01-01 17:00:00")
def test_medication_is_recorded(dose_window_record, medication_record, take_event_record):
    assert medication_record.is_recorded_for_day(dose_window_record)


@freeze_time("2012-01-02 17:00:00")
def test_medication_is_recorded_out_of_range(dose_window_record, medication_record, take_event_record):
    assert not medication_record.is_recorded_for_day(dose_window_record)


@freeze_time("2012-01-02 17:00:00")
def test_within_dosing_period(dose_window_record):
    assert dose_window_record.within_dosing_period()


@freeze_time("2012-01-02 15:00:00")
def test_not_within_dosing_period(dose_window_record):
    assert not dose_window_record.within_dosing_period()


@freeze_time("2012-01-01 17:00:00")  # HACK: needed to invalidate scheduler jobs at end of test run because we're using prod scheduler.
def test_create_dose_record_scheduler_status(dose_window_record, scheduler):
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is None

@freeze_time("2012-01-01 17:00:00")
def test_create_medication_scheduler_status(dose_window_record, medication_record, scheduler):
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is not None


@freeze_time("2012-01-01 17:00:00")
def test_medication_activation_scheduler_status(dose_window_record, medication_record, scheduler):
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is not None
    deactivate_medication(scheduler, medication_record)
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is None

@freeze_time("2012-01-01 17:00:00")
def test_associating_medication_scheduler_status(dose_window_record, medication_record, scheduler):
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is not None
    dissociate_medication_from_dose_window(scheduler, medication_record, dose_window_record)
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is None
    associate_medication_with_dose_window(medication_record, dose_window_record, scheduler_tuple=(scheduler, test_function))
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-initial-new")
    assert scheduled_job is not None


@freeze_time("2012-01-02 17:00:00")  # jan 2 so boundary record is in the past
def test_delete_past_boundary_record(dose_window_record, boundary_event_record, db_session):
    dose_window_record.remove_boundary_event(days_delta=-2)
    assert len(db_session.query(EventLog).all()) == 1
    dose_window_record.remove_boundary_event(days_delta=-1)
    assert len(db_session.query(EventLog).all()) == 0
