import pytest
from unittest import mock
import os
from freezegun import freeze_time
from datetime import datetime
from pytz import utc, timezone
import tzlocal


from models import (
    DoseWindow,
    EventLog,
    User,
    Medication
)

# turn on new bot
os.environ["NEW_DATA_MODEL"] = "blah"

@pytest.fixture
def user_record(db_session):
    user_obj = User(
        phone_number="3604508655",
        name="Peter"
    )
    db_session.add(user_obj)
    db_session.commit()
    return user_obj

@pytest.fixture
def user_record_with_manual_takeover(db_session):
    user_obj = User(
        phone_number="3604508655",
        name="Peter",
        manual_takeover=True
    )
    db_session.add(user_obj)
    db_session.commit()
    return user_obj

@pytest.fixture
def dose_window_record(db_session, user_record):
    dose_window_obj = DoseWindow(
        day_of_week=2,  # wednesday
        start_hour=9+7,
        start_minute=0,
        end_hour=11+7,
        end_minute=0,
        user_id=user_record.id
    )
    db_session.add(dose_window_obj)
    db_session.commit()
    return dose_window_obj

@pytest.fixture
def dose_window_record_out_of_range(db_session, user_record):
    dose_window_obj = DoseWindow(
        day_of_week=2,  # wednesday
        start_hour=13+7,
        start_minute=0,
        end_hour=15+7,
        end_minute=0,
        user_id=user_record.id
    )
    db_session.add(dose_window_obj)
    db_session.commit()
    return dose_window_obj

@pytest.fixture
def medication_record(db_session, dose_window_record, user_record):
    medication_obj = Medication(
        user_id=user_record.id,
        medication_name="Zoloft",
        dose_windows = [dose_window_record]
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj

@pytest.fixture
def medication_record_2(db_session, dose_window_record, user_record):
    medication_obj = Medication(
        user_id=user_record.id,
        medication_name="Lisinopril",
        dose_windows = [dose_window_record]
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj


@pytest.fixture
def medication_take_event_record_in_dose_window(db_session, medication_record, dose_window_record, user_record):
    take_time = datetime(2012, 1, 1, 16, 30, tzinfo=utc)
    event_obj = EventLog("take", user_record.id, dose_window_record.id, medication_record.id, event_time=take_time)
    db_session.add(event_obj)
    db_session.commit()
    return event_obj

@pytest.fixture
def medication_take_event_record_not_in_dose_window(db_session, medication_record, dose_window_record, user_record):
    take_time = datetime(2011, 12, 31, 16, 30, tzinfo=utc)  # the day before
    event_obj = EventLog("take", user_record.id, dose_window_record.id, medication_record.id, event_time=take_time)
    db_session.add(event_obj)
    db_session.commit()
    return event_obj


@mock.patch("bot.segment_message")
def test_unexpected_phone_number(segment_message_mock, client, db_session):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "unexpected_phone_number"
    assert all_events[0].description == "3604508655"


@mock.patch("bot.segment_message")
@mock.patch("bot.text_fallback")
def test_not_interpretable(text_fallback_mock, segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508655", "Body": "blah"})
    assert text_fallback_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "not_interpretable"
    assert all_events[0].description == "blah"
    assert all_events[0].user_id == user_record.id

@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.get_thanks_message")
def test_thanks(thanks_message_mock, create_messages_mock, segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert thanks_message_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "conversational"
    assert all_events[0].description == "T. Thanks!"
    assert all_events[0].user_id == user_record.id

@mock.patch("bot.segment_message")
@mock.patch("bot.get_thanks_message")
@mock.patch("bot.text_fallback")
def test_thanks_with_manual_takeover(
        fallback_mock,
        thanks_message_mock,
        segment_message_mock,
        client,
        db_session,
        user_record_with_manual_takeover
):
    segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert not thanks_message_mock.called
    assert fallback_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "manually_silenced"
    assert all_events[0].description == "T. Thanks!"
    assert all_events[0].user_id == user_record_with_manual_takeover.id
    assert all_events[0].dose_window_id is None

# NOTE: freezegun freezes UTC time
@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take(take_message_mock, segment_message_mock, create_messages_mock, client, db_session, user_record, dose_window_record, medication_record):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)  # match freezegun time


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message")
def test_take_multiple_medications(
    take_message_mock, segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record, medication_record,
    medication_record_2
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert take_message_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)
    assert all_events[1].event_type == "take"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record_2.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_dose_already_recorded(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, medication_take_event_record_in_dose_window
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2  # first one is our inserted take record
    assert all_events[1].event_type == "attempted_rerecord"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1  # first one is our inserted take record
    # we expect it to record again since the record is outdated
    assert all_events[0].event_type == "out_of_range"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is None
    assert all_events[0].medication_id is None
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_skip(segment_message_mock, create_messages_mock, client, db_session, user_record, dose_window_record, medication_record):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "skip"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_skip_dose_already_recorded(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, medication_take_event_record_in_dose_window
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2  # first one is our inserted take record
    assert all_events[1].event_type == "attempted_rerecord"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_skip_multiple_medications(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record, medication_record,
    medication_record_2
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "skip"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)
    assert all_events[1].event_type == "skip"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record_2.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_skip_dose_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1  # first one is our inserted take record
    # we expect it to record again since the record is outdated
    assert all_events[0].event_type == "out_of_range"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is None
    assert all_events[0].medication_id is None
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)