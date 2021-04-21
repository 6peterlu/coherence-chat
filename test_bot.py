from bot import get_take_message
import pytest
from unittest import mock
from datetime import datetime, timedelta
from pytz import timezone

from models import Event, Dose, Reminder, ManualTakeover

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

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
def test_1_hr_delay(mock_get_current_end_date, mock_followup_text, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record, scheduler):
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

# within time range of dose
@freeze_time("2012-01-1 12:00:01")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.scheduler.add_job")
@mock.patch("bot.send_followup_text")
@mock.patch("bot.get_current_end_date")
@mock.patch("bot.random.randint")
def test_20_min_delay(mock_randint, mock_get_current_end_date, mock_followup_text, add_job_mock, segment_message_mock, create_messages_mock, client, db_session, dose_record, initial_reminder_record):
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
    add_job_mock.assert_called_with(f"{dose_record.id}-followup", mock_followup_text, args=[dose_record.id], trigger="date", run_date=timezone("UTC").localize(datetime(2012, 1, 1, 12, 23, 1)), misfire_grace_time=5*60)