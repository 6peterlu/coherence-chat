from bot import drop_all_new_tables, port_legacy_data
import pytest
from unittest import mock
from datetime import datetime, timedelta
from pytz import timezone
import os

from models import (
    Event, Dose, Reminder, ManualTakeover,
    # new models
    DoseWindow,
    EventLog,
    Medication,
    User,
    # new schemas,
    DoseWindowSchema,
    EventLogSchema,
    MedicationSchema,
    UserSchema
)

from freezegun import freeze_time

@pytest.fixture
def dose_record(db_session):
    dose_obj = Dose(
        start_hour=11,
        end_hour=1,
        start_minute=0,
        end_minute=0,
        patient_name="Peter",
        phone_number="+113604508655",
        medication_name="test med",
        active=True
    )
    db_session.add(dose_obj)
    db_session.commit()
    return dose_obj

@pytest.fixture
def take_event_record(db_session, dose_record):
    event_obj = Event(
        event_type="take",
        event_time=datetime(2012, 1, 1, 13, 23, 15),
        phone_number=dose_record.phone_number,
        description=dose_record.id
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj

@pytest.fixture
def reminder_delay_event_record(db_session, dose_record):
    event_obj = Event(
        event_type="reminder_delay",
        event_time=datetime(2012, 1, 1, 13, 23, 15),
        phone_number=dose_record.phone_number,
        description="delayed to 2021-04-25 09:26:20.045841-07:00"
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj


@pytest.fixture
def conversational_event_record(db_session, dose_record):
    event_obj = Event(
        event_type="conversational",
        event_time=datetime(2012, 1, 1, 13, 23, 15),
        phone_number=dose_record.phone_number
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj


@pytest.fixture
def initial_reminder_record(db_session, dose_record):
    reminder_obj = Reminder(
        dose_id=dose_record.id,
        send_time=datetime(2012, 1, 1, 11),
        reminder_type="initial"
    )
    db_session.add(reminder_obj)
    db_session.commit()


@pytest.fixture
def manual_takeover_number(db_session):
    manual_obj = ManualTakeover(phone_number="+113604508655")
    db_session.add(manual_obj)
    db_session.commit()
    return manual_obj

# @pytest.fixture
# def boundary_reminder_record(db_session, dose_record):
#     reminder_obj = Reminder(
#         dose_id=dose_record.id,
#         send_time=datetime(2012, 1, 1, 13),
#         reminder_type="boundary"
#     )
#     db_session.add(reminder_obj)
#     db_session.commit()

@mock.patch("bot.segment_message")
@mock.patch("bot.text_fallback")
def test_not_interpretable(text_fallback_mock, segment_message_mock, client, db_session):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508655"})
    assert text_fallback_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "not_interpretable"

@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_thanks_message")
def test_thanks(thanks_message_mock, segment_message_mock, create_messages_mock, client, db_session):
    segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert thanks_message_mock.called
    # assert dose_record.id == db_session.query(Online).all()[0].id
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "conversational"

@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_thanks_message")
@mock.patch("bot.text_fallback")
def test_thanks_with_manual_takeover(fallback_mock, thanks_message_mock, segment_message_mock, create_messages_mock, manual_takeover_number, client, db_session):
    segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert not thanks_message_mock.called
    assert fallback_mock.called

@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_without_dose(segment_message_mock, create_messages_mock, client, db_session):
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "out_of_range"

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_with_dose(take_message_mock, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].event_time == datetime(2012, 1, 1, 4, 0, 1)  # match freezegun time

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_with_dose_and_time(take_message_mock, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T", "payload": datetime(2012, 1, 1, 8, 0)}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].event_time == datetime(2012, 1, 1, 8, 0)  # match input time

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_with_dose(segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    segment_message_mock.return_value = [{'type': 'skip', 'modifiers': {'emotion': 'neutral'}, 'raw': "S"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "skip"
    assert all_events[0].event_time == datetime(2012, 1, 1, 4, 0, 1)  # match freezegun time

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_option_1(mock_get_current_end_date, segment_message_mock, create_messages_mock, scheduler, client, db_session, dose_record, initial_reminder_record):
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    mock_get_current_end_date.return_value = timezone("UTC").localize(datetime(2012, 1, 1, 13))
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=10)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == "delayed to 2012-01-01 04:10:01-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 12, 10, 1))


# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_option_3_near_boundary(mock_get_current_end_date, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'special', 'payload': '3', "raw": "1"}]
    mock_get_current_end_date.return_value = timezone("UTC").localize(datetime(2012, 1, 1, 13))
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=60)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == "delayed to 2012-01-01 04:50:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 12, 50))

# # within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay(mock_get_current_end_date, mock_followup_text, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': timezone("UTC").localize(datetime(2012, 1, 1, 13)), "raw": "1hr"}]
    mock_get_current_end_date.return_value = timezone("UTC").localize(datetime(2012, 1, 1, 14))
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 05:00:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 13, 0))

@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay_near_boundary(mock_get_current_end_date, mock_followup_text, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': timezone("UTC").localize(datetime(2012, 1, 1, 13)), "raw": "1hr"}]
    mock_get_current_end_date.return_value = timezone("UTC").localize(datetime(2012, 1, 1, 13))
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 04:50:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 12, 50))

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
@mock.patch("bot.random.randint")
def test_activity_delay(mock_randint, mock_get_current_end_date, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'activity', 'payload': {'type': 'short', 'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'concept': 'leisure'}, 'raw': 'walking'}]
    mock_get_current_end_date.return_value = timezone("UTC").localize(datetime(2012, 1, 1, 13))
    mock_randint.return_value = 23
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "activity"
    assert all_events[0].description == "walking"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == "delayed to 2012-01-01 04:23:01-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 12, 23, 1))


@freeze_time("2012-01-1 12:00:01")
def test_port_legacy_data(dose_record, take_event_record, reminder_delay_event_record, conversational_event_record, db_session):
    phone_numbers_to_port = ["3604508655"]
    names = {"+113604508655": "Peter"}
    patient_dose_map = {"+113604508655": {"morning": [dose_record.id]}}
    port_legacy_data(phone_numbers_to_port, names, patient_dose_map)
    users = db_session.query(User).all()
    assert len(users) == 1
    medications = db_session.query(Medication).all()
    assert len(medications) == 1
    dose_windows = db_session.query(DoseWindow).all()
    assert len(dose_windows) == 1
    event_logs = db_session.query(EventLog).all()
    assert len(event_logs) == 3
    assert UserSchema().dump(users[0]) == {
        'events': [
            {
                'event_type': 'take', 'id': 1, 'event_time': '2012-01-01T13:23:15', 'description': None
            },
            {
                'event_type': 'reminder_delay', 'id': 2, 'event_time': '2012-01-01T13:23:15', 'description': "delayed to 2021-04-25 09:26:20.045841-07:00"
            },
            {
                'event_type': 'conversational', 'id': 3, 'event_time': '2012-01-01T13:23:15', 'description': None
            },
        ],
        'phone_number': '3604508655',
        'paused': True,
        'id': 1,
        'manual_takeover': False,
        'name': 'Peter',
        'doses': [{
            'instructions': None, 'id': medications[0].id, 'active': True, 'medication_name': 'test med'
        }],
        'dose_windows': [{
            'start_minute': 0,
            'active': True,
            'id': dose_windows[0].id,
            'end_minute': 0,
            'start_hour': 11,
            'end_hour': 1
        }],
        'timezone': 'US/Pacific'
    }
    assert MedicationSchema().dump(medications[0]) == {
        'medication_name': 'test med',
        'user': {
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'id': users[0].id,
            'manual_takeover': False,
            'name': 'Peter',
            'paused': True
        },
        'instructions': None,
        'dose_windows': [{
            'start_minute': 0,
            'id': dose_windows[0].id,
            'start_hour': 11,
            'end_hour': 1,
            'end_minute': 0,
            'active': True
        }],
        'id': 1,
        'active': True,
        'events': [
            {
                'event_type': 'take', 'id': 1, 'event_time': '2012-01-01T13:23:15', 'description': None
            }
        ],
    }
    assert DoseWindowSchema().dump(dose_windows[0]) == {
        'start_minute': 0,
        'end_minute': 0,
        'medications': [{'active': True, 'id': medications[0].id, 'instructions': None, 'medication_name': 'test med'}],
        'end_hour': 1,
        'active': True,
        'user': {
            'paused': True,
            'name': 'Peter',
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'id': users[0].id
        },
        'events': [
            {
                'event_type': 'take', 'id': 1, 'event_time': '2012-01-01T13:23:15', 'description': None
            }
        ],
        'start_hour': 11,
        'id': 1
    }
    assert EventLogSchema().dump(event_logs[0]) == {
        'description': None,
        'dose_window': {
            'id': dose_windows[0].id,
            'end_minute': 0,
            'active': True,
            'start_minute': 0,
            'start_hour': 11,
            'end_hour': 1
        },
        'id': 1,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T13:23:15',
        'medication': {
            'medication_name': 'test med',
            'active': True,
            'id': medications[0].id,
            'instructions': None
        },
        'event_type': 'take'
    }
    assert EventLogSchema().dump(event_logs[1]) == {
        'description': "delayed to 2021-04-25 09:26:20.045841-07:00",
        'dose_window': None,
        'id': 2,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T13:23:15',
        'medication': None,
        'event_type': 'reminder_delay'
    }
    assert EventLogSchema().dump(event_logs[2]) == {
        'description': None,
        'dose_window': None,
        'id': 3,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T13:23:15',
        'medication': None,
        'event_type': 'conversational'
    }


def test_drop_all_new_tables(db_session, user_record, dose_window_record, medication_record):
    drop_all_new_tables()
    assert len(db_session.query(User).all()) == 0
