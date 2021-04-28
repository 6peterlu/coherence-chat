from bot import drop_all_new_tables, port_legacy_data, send_followup_text
import pytest
from unittest import mock
from datetime import datetime, timedelta
from pytz import timezone, utc
import os
import tzlocal

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
        start_hour=9+7,
        end_hour=11+7,
        start_minute=0,
        end_minute=0,
        patient_name="Peter",
        phone_number="+113604508655",
        medication_name="Keppra, Glipizide",
        active=True
    )
    db_session.add(dose_obj)
    db_session.commit()
    return dose_obj

@pytest.fixture
def dose_record_for_paused_user(db_session):
    dose_obj = Dose(
        start_hour=9+7,
        end_hour=11+7,
        start_minute=0,
        end_minute=0,
        patient_name="Peter",
        phone_number="+113604508656",
        medication_name="Keppra, Glipizide",
        active=True
    )
    db_session.add(dose_obj)
    db_session.commit()
    return dose_obj

@pytest.fixture
def inactive_dose_record(db_session):
    dose_obj = Dose(
        start_hour=9+7,
        end_hour=11+7,
        start_minute=0,
        end_minute=0,
        patient_name="Peter",
        phone_number="+113604508655",
        medication_name="Keppra, Glipizide",
        active=False
    )
    db_session.add(dose_obj)
    db_session.commit()
    return dose_obj

@pytest.fixture
def take_event_record(db_session, dose_record):
    event_obj = Event(
        event_type="take",
        event_time=datetime(2012, 1, 1, 10+7, 23, 15),
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
        event_time=datetime(2012, 1, 1, 10+7, 23, 15),
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
        event_time=datetime(2012, 1, 1, 10+7, 23, 15),
        phone_number=dose_record.phone_number
    )
    db_session.add(event_obj)
    db_session.commit()
    return event_obj


@pytest.fixture
def initial_reminder_record(db_session, dose_record):
    reminder_obj = Reminder(
        dose_id=dose_record.id,
        send_time=datetime(2012, 1, 1, 9+7),
        reminder_type="initial"
    )
    db_session.add(reminder_obj)
    db_session.commit()

@pytest.fixture
def initial_reminder_record_for_paused_user(db_session, dose_record_for_paused_user):
    reminder_obj = Reminder(
        dose_id=dose_record_for_paused_user.id,
        send_time=datetime(2012, 1, 1, 9+7),
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

@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.maybe_schedule_absent")
@mock.patch("bot.remove_jobs_helper")
def test_send_followup_text_live_port(
    remove_jobs_mock, schedule_absent_mock, create_messages_mock,
    dose_record_for_paused_user, user_record_paused, dose_window_record_for_paused_user, medication_record_for_paused_user,
    medication_record_for_paused_user_2, db_session
):
    send_followup_text(dose_record_for_paused_user.id)
    assert remove_jobs_mock.called
    assert schedule_absent_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 2


# /bot tests
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
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_with_dose(take_message_mock, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    local_tz = tzlocal.get_localzone()
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, 0, 1)  # match freezegun time

# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_with_dose_and_time(take_message_mock, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    local_tz = tzlocal.get_localzone()
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T", "payload": datetime(2012, 1, 1, 8, 0, tzinfo=utc)}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 8, 0, tzinfo=utc)  # match input time

# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_with_dose(segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
    local_tz = tzlocal.get_localzone()
    segment_message_mock.return_value = [{'type': 'skip', 'modifiers': {'emotion': 'neutral'}, 'raw': "S"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "skip"
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, 0, 1, tzinfo=utc)  # match freezegun time

# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_option_1(mock_get_current_end_date, segment_message_mock, create_messages_mock, scheduler, client, db_session, dose_record, initial_reminder_record):
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=10)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == 'delayed to 2012-01-01 09:10:01-08:00'
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 10, 1, tzinfo=utc)


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_option_3_near_boundary(mock_get_current_end_date, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'special', 'payload': '3', "raw": "1"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=60)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == 'delayed to 2012-01-01 09:50:00-08:00'
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay(mock_get_current_end_date, mock_followup_text, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 18, 0, 1, tzinfo=utc), "raw": "1hr"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 19, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 10:00:01-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 18, 0, 1, tzinfo=utc)

@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay_near_boundary(mock_get_current_end_date, mock_followup_text, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 18, 0, 1, tzinfo=utc), "raw": "1hr"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 09:50:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)

# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
@mock.patch("bot.random.randint")
def test_activity_delay(
    mock_randint, mock_get_current_end_date, segment_message_mock,
    create_messages_mock, client, db_session, dose_record,
    initial_reminder_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'activity', 'payload': {'type': 'short', 'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'concept': 'leisure'}, 'raw': 'walking'}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    mock_randint.return_value = 23
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "activity"
    assert all_events[0].description == "walking"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == "delayed to 2012-01-01 09:23:01-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 23, 1, tzinfo=utc)


# test live data porting
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.segment_message")
@mock.patch("bot.text_fallback")
def test_not_interpretable_live_port(text_fallback_mock, segment_message_mock, client, db_session, user_record_paused, dose_window_record_for_paused_user):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508656"})
    assert text_fallback_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "not_interpretable"
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "not_interpretable"
    assert all_event_logs[0].dose_window.id is dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication is None


@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_thanks_message")
def test_thanks_live_port(thanks_message_mock, segment_message_mock, create_messages_mock, client, db_session, user_record_paused, dose_window_record_for_paused_user):
    segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    assert thanks_message_mock.called
    # assert dose_record.id == db_session.query(Online).all()[0].id
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "conversational"
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "conversational"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication is None


@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_without_dose_live_port(
    segment_message_mock, create_messages_mock, client,
    db_session, user_record_paused
):
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "out_of_range"
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "out_of_range"
    assert all_event_logs[0].dose_window is None
    assert all_event_logs[0].medication is None


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_with_dose_live_port(
    take_message_mock, segment_message_mock, create_messages_mock,
    client, db_session, dose_record_for_paused_user, initial_reminder_record_for_paused_user,
    user_record_paused, dose_window_record_for_paused_user, medication_record_for_paused_user,
    medication_record_for_paused_user_2
):
    local_tz = tzlocal.get_localzone()
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, 0, 1, tzinfo=utc)  # match freezegun time
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 2
    assert all_event_logs[0].event_type == "take"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication.id == medication_record_for_paused_user.id
    assert all_event_logs[1].event_type == "take"
    assert all_event_logs[1].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[1].medication.id == medication_record_for_paused_user_2.id


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_option_3_near_boundary_live_port(
    mock_get_current_end_date, segment_message_mock, create_messages_mock,
    client, db_session, dose_record_for_paused_user, initial_reminder_record_for_paused_user, scheduler,
    user_record_paused, dose_window_record_for_paused_user, medication_record_for_paused_user
):
    segment_message_mock.return_value = [{'type': 'special', 'payload': '3', "raw": "1"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=60)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == 'delayed to 2012-01-01 09:50:00-08:00'
    scheduled_job = scheduler.get_job(f"{dose_record_for_paused_user.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 2
    assert all_event_logs[0].event_type == "requested_time_delay"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication == None
    assert all_event_logs[1].event_type == "reminder_delay"
    assert all_event_logs[1].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[1].medication == None

# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay_live_port(
    mock_get_current_end_date, mock_followup_text, segment_message_mock,
    create_messages_mock, client, db_session, dose_record_for_paused_user, initial_reminder_record_for_paused_user,
    initial_reminder_record, scheduler, user_record_paused, dose_window_record_for_paused_user,
    medication_record_for_paused_user
):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 18, tzinfo=utc), "raw": "1hr"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 19, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 10:00:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record_for_paused_user.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 18, 0, tzinfo=utc)
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "reminder_delay"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication == None


@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay_near_boundary_live_port(
    mock_get_current_end_date, mock_followup_text, segment_message_mock,
    create_messages_mock, client, db_session, dose_record_for_paused_user,
    initial_reminder_record_for_paused_user, scheduler, user_record_paused,
    dose_window_record_for_paused_user, medication_record_for_paused_user
):
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 18, 0, 1, tzinfo=utc), "raw": "1hr"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].description == "delayed to 2012-01-01 09:50:00-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record_for_paused_user.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "reminder_delay"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication == None


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
@mock.patch("bot.random.randint")
def test_activity_delay_live_port(
    mock_randint, mock_get_current_end_date, segment_message_mock,
    create_messages_mock, client, db_session, dose_record_for_paused_user,
    initial_reminder_record_for_paused_user, scheduler, user_record_paused,
    dose_window_record_for_paused_user, medication_record_for_paused_user
):
    segment_message_mock.return_value = [{'type': 'activity', 'payload': {'type': 'short', 'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.", 'concept': 'leisure'}, 'raw': 'walking'}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    mock_randint.return_value = 23
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "activity"
    assert all_events[0].description == "walking"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == "delayed to 2012-01-01 09:23:01-08:00"
    scheduled_job = scheduler.get_job(f"{dose_record_for_paused_user.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == timezone("UTC").localize(datetime(2012, 1, 1, 17, 23, 1))
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 2
    assert all_event_logs[0].event_type == "activity"
    assert all_events[0].description == "walking"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication == None
    assert all_event_logs[1].event_type == "reminder_delay"
    assert all_event_logs[1].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[1].medication == None


# within time range of dose
@freeze_time("2012-01-1 17:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_current_end_date")
def test_delay_minutes_live_port(
    mock_get_current_end_date, segment_message_mock, create_messages_mock,
    client, db_session, dose_record_for_paused_user, initial_reminder_record_for_paused_user, scheduler,
    user_record_paused, dose_window_record_for_paused_user, medication_record_for_paused_user
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 20, "raw": "20"}]
    mock_get_current_end_date.return_value = datetime(2012, 1, 1, 18, tzinfo=utc)
    client.post("/bot", query_string={"From": "+13604508656"})
    assert create_messages_mock.called
    all_events = db_session.query(Event).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].description == f"{timedelta(minutes=20)}"
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].description == 'delayed to 2012-01-01 09:20:01-08:00'
    scheduled_job = scheduler.get_job(f"{dose_record_for_paused_user.id}-followup")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 20, 1, tzinfo=utc)
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 2
    assert all_event_logs[0].event_type == "requested_time_delay"
    assert all_event_logs[0].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[0].medication == None
    assert all_event_logs[1].event_type == "reminder_delay"
    assert all_event_logs[1].dose_window.id == dose_window_record_for_paused_user.id
    assert all_event_logs[1].medication == None


@freeze_time("2012-01-1 17:00:01")
def test_port_legacy_data(
    dose_record, inactive_dose_record, take_event_record,
    reminder_delay_event_record, conversational_event_record, db_session
):
    phone_numbers_to_port = ["3604508655"]
    names = {"+113604508655": "Peter"}
    patient_dose_map = {"+113604508655": {"morning": [dose_record.id, inactive_dose_record.id]}}
    port_legacy_data(phone_numbers_to_port, names, patient_dose_map)
    users = db_session.query(User).all()
    assert len(users) == 1
    medications = db_session.query(Medication).all()
    assert len(medications) == 2
    dose_windows = db_session.query(DoseWindow).all()
    assert len(dose_windows) == 1
    event_logs = db_session.query(EventLog).all()
    assert len(event_logs) == 4
    assert UserSchema().dump(users[0]) == {
        'events': [
            {
                'event_type': 'take', 'id': event_logs[0].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            },
            {
                'event_type': 'take', 'id': event_logs[1].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            },
            {
                'event_type': 'reminder_delay', 'id': event_logs[2].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': "delayed to 2021-04-25 09:26:20.045841-07:00"
            },
            {
                'event_type': 'conversational', 'id': event_logs[3].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            },
        ],
        'phone_number': '3604508655',
        'paused': True,
        'id': users[0].id,
        'manual_takeover': False,
        'name': 'Peter',
        'doses': [
            {
                'instructions': None, 'id': medications[0].id, 'active': True, 'medication_name': 'Keppra'
            },
            {
                'instructions': None, 'id': medications[1].id, 'active': True, 'medication_name': 'Glipizide'
            }
        ],
        'dose_windows': [{
            'start_minute': 0,
            'active': True,
            'id': dose_windows[0].id,
            'end_minute': 0,
            'start_hour': 16,
            'end_hour': 18
        }],
        'timezone': 'US/Pacific'
    }
    assert MedicationSchema().dump(medications[0]) == {
        'medication_name': 'Keppra',
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
            'start_hour': 16,
            'end_hour': 18,
            'end_minute': 0,
            'active': True
        }],
        'id': medications[0].id,
        'active': True,
        'events': [
            {
                'event_type': 'take', 'id': event_logs[0].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            }
        ],
    }
    assert MedicationSchema().dump(medications[1]) == {
        'medication_name': 'Glipizide',
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
            'start_hour': 16,
            'end_hour': 18,
            'end_minute': 0,
            'active': True
        }],
        'id': medications[1].id,
        'active': True,
        'events': [
            {
                'event_type': 'take', 'id': event_logs[1].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            }
        ],
    }
    assert DoseWindowSchema().dump(dose_windows[0]) == {
        'start_minute': 0,
        'end_minute': 0,
        'medications': [
            {'active': True, 'id': medications[0].id, 'instructions': None, 'medication_name': 'Keppra'},
            {'active': True, 'id': medications[1].id, 'instructions': None, 'medication_name': 'Glipizide'}
        ],
        'end_hour': 18,
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
                'event_type': 'take', 'id': event_logs[0].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            },
            {
                'event_type': 'take', 'id': event_logs[1].id, 'event_time': '2012-01-01T17:23:15+00:00', 'description': None
            }
        ],
        'start_hour': 16,
        'id': dose_windows[0].id
    }
    assert EventLogSchema().dump(event_logs[0]) == {
        'description': None,
        'dose_window': {
            'id': dose_windows[0].id,
            'end_minute': 0,
            'active': True,
            'start_minute': 0,
            'start_hour': 16,
            'end_hour': 18
        },
        'id': event_logs[0].id,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T17:23:15+00:00',
        'medication': {
            'medication_name': 'Keppra',
            'active': True,
            'id': medications[0].id,
            'instructions': None
        },
        'event_type': 'take'
    }
    assert EventLogSchema().dump(event_logs[1]) == {
        'description': None,
        'dose_window': {
            'id': dose_windows[0].id,
            'end_minute': 0,
            'active': True,
            'start_minute': 0,
            'start_hour': 16,
            'end_hour': 18
        },
        'id': event_logs[1].id,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T17:23:15+00:00',
        'medication': {
            'medication_name': 'Glipizide',
            'active': True,
            'id': medications[1].id,
            'instructions': None
        },
        'event_type': 'take'
    }
    assert EventLogSchema().dump(event_logs[2]) == {
        'description': "delayed to 2021-04-25 09:26:20.045841-07:00",
        'dose_window': None,
        'id': event_logs[2].id,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T17:23:15+00:00',
        'medication': None,
        'event_type': 'reminder_delay'
    }
    assert EventLogSchema().dump(event_logs[3]) == {
        'description': None,
        'dose_window': None,
        'id': event_logs[3].id,
        'user': {
            'id': users[0].id,
            'manual_takeover': False,
            'phone_number': '3604508655',
            'timezone': 'US/Pacific',
            'paused': True,
            'name': 'Peter'
        },
        'event_time': '2012-01-01T17:23:15+00:00',
        'medication': None,
        'event_type': 'conversational'
    }



def test_drop_all_new_tables(db_session, user_record_paused, dose_window_record_for_paused_user, medication_record_for_paused_user):
    drop_all_new_tables()
    assert len(db_session.query(User).all()) == 0
    assert len(db_session.query(DoseWindow).all()) == 0
    assert len(db_session.query(Medication).all()) == 0


def test_drop_all_new_tables_with_user(
    db_session, user_record_paused, dose_window_record_for_paused_user,
    medication_record_for_paused_user, user_record
):
    drop_all_new_tables(user_record_paused)
    assert len(db_session.query(User).all()) == 1  # other user still remains
    assert len(db_session.query(DoseWindow).all()) == 0
    assert len(db_session.query(Medication).all()) == 0
