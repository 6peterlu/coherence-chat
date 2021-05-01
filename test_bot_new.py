from bot import maybe_schedule_absent_new, send_absent_text_new, send_followup_text_new, send_intro_text_new
import pytest
from unittest import mock
import os
from freezegun import freeze_time
from datetime import datetime
from pytz import utc, timezone
import tzlocal


from models import (
    EventLog,
    # schemas
    UserSchema,
)

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

def stub_fn(*_):
    pass


def test_get_all_data_for_user(
    user_record, dose_window_record, medication_record,
    medication_record_2, db_session, client
):
    response = client.get("/user/everything", query_string={"userId": user_record.id, "pw": "couchsurfing"})
    user_schema = UserSchema()
    assert response.get_json() == user_schema.dump(user_record)


@mock.patch("bot.segment_message")
@mock.patch("bot.text_fallback")
# @mock.patch("bot.client.messages.create")
def test_not_interpretable(text_fallback_mock, segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508655", "Body": "blah"})
    assert text_fallback_mock.called
    # assert create_messages_mock.called
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
@mock.patch("bot.get_take_message_new")
@mock.patch("bot.remove_jobs_helper")
def test_take(
    remove_jobs_mock, take_message_mock, segment_message_mock,
    create_messages_mock, client, db_session, user_record,
    dose_window_record, medication_record, scheduler
):
    # seed scheduler jobs to test removal
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn)
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn)
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn)
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
    assert remove_jobs_mock.called
    for job_type in ["followup", "absent", "boundary"]:
        assert scheduler.get_job(f"{dose_window_record.id}-{job_type}-new") is None


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_take_message_new")
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


# TODO: fix test
# @freeze_time("2012-01-01 17:00:00")
# @mock.patch("bot.client.messages.create")
# @mock.patch("bot.segment_message")
# def test_take_dose_out_of_range(
#     segment_message_mock, create_messages_mock,
#     client, db_session, user_record, dose_window_record_out_of_range
# ):
#     local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
#     segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
#     client.post("/bot", query_string={"From": "+13604508655"})
#     assert create_messages_mock.called
#     all_events = db_session.query(EventLog).all()
#     assert len(all_events) == 1  # first one is our inserted take record
#     # we expect it to record again since the record is outdated
#     assert all_events[0].event_type == "out_of_range"
#     assert all_events[0].user_id == user_record.id
#     assert all_events[0].dose_window_id is None
#     assert all_events[0].medication_id is None
#     assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
@mock.patch("bot.remove_jobs_helper")
def test_skip(remove_jobs_mock, segment_message_mock, create_messages_mock, client, db_session, user_record, dose_window_record, medication_record):
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
    assert remove_jobs_mock.called


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

@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
def test_error_report(create_messages_mock, segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': 'x', "raw": "x"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "user_reported_error"
    assert all_events[0].description is None
    assert all_events[0].user_id == user_record.id
    assert all_events[0].medication_id is None
    assert all_events[0].dose_window_id is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_canned_delay(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 10, tzinfo=utc)

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_canned_delay_near_boundary(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '3', "raw": "3"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)

@freeze_time("2012-01-01 17:55:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
def test_canned_delay_too_late(
    create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_canned_delay_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
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


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_delay_minutes(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 20, "raw": "20"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 20, tzinfo=utc)

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_delay_minutes_near_boundary(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 60, "raw": "60"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)

@freeze_time("2012-01-01 17:55:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
def test_delay_minutes_too_late(
    create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 60, "raw": "60"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_delay_minutes_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
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


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_requested_alarm_time(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 9, 30, tzinfo=user_tz), "raw": "30min"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 30, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
def test_requested_alarm_time_near_boundary(
    remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 10, tzinfo=user_tz), "raw": "1hr"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)


@freeze_time("2012-01-01 17:55:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
def test_requested_alarm_time_too_late(
    create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 10, tzinfo=user_tz), "raw": "1hr"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 0
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_requested_alarm_time_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': datetime(2012, 1, 1, 10, tzinfo=user_tz), "raw": "1hr"}]
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


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
@mock.patch("bot.random.randint")
def test_activity(
    randint_mock, remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    randint_mock.return_value = 25
    segment_message_mock.return_value = [{
        'type': 'activity',
        'payload': {
            'type': 'short',
            'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
            'concept': 'leisure'
        },
        'raw': 'walking'
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "activity"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 25, tzinfo=utc)

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.remove_jobs_helper")
@mock.patch("bot.random.randint")
def test_activity_near_boundary(
    randint_mock, remove_jobs_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    randint_mock.return_value = 60
    segment_message_mock.return_value = [{
        'type': 'activity',
        'payload': {
            'type': 'short',
            'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
            'concept': 'leisure'
        },
        'raw': 'walking'
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    assert remove_jobs_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "activity"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    assert all_events[1].event_type == "reminder_delay"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)

@freeze_time("2012-01-01 17:55:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.random.randint")
def test_activity_too_late(
    randint_mock, create_messages_mock, segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    randint_mock.return_value = 10
    segment_message_mock.return_value = [{
        'type': 'activity',
        'payload': {
            'type': 'short',
            'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
            'concept': 'leisure'
        },
        'raw': 'walking'
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert create_messages_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "activity"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.client.messages.create")
@mock.patch("bot.segment_message")
def test_activity_out_of_range(
    segment_message_mock, create_messages_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'activity',
        'payload': {
            'type': 'short',
            'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
            'concept': 'leisure'
        },
        'raw': 'walking'
    }]
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


@mock.patch("bot.remove_jobs_helper")
@mock.patch("bot.maybe_schedule_absent_new")
def test_send_followup_text_new(mock_remove_jobs, mock_maybe_schedule_absent, dose_window_record, db_session):
    send_followup_text_new(dose_window_record.id)
    assert mock_remove_jobs.called
    assert mock_maybe_schedule_absent.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "followup"

@mock.patch("bot.remove_jobs_helper")
@mock.patch("bot.client.messages.create")
def test_send_intro_text_new(mock_message_create, mock_remove_jobs, dose_window_record, db_session):
    send_intro_text_new(dose_window_record.id)
    assert mock_message_create.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "initial"

@mock.patch("bot.remove_jobs_helper")
@mock.patch("bot.maybe_schedule_absent_new")
@mock.patch("bot.client.messages.create")
def test_send_absent_text_new(
    mock_message_create, mock_maybe_schedule_absent,
    mock_remove_jobs, dose_window_record, db_session
):
    send_absent_text_new(dose_window_record.id)
    assert mock_message_create.called
    assert mock_maybe_schedule_absent.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "absent"

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.random.randint")
def test_maybe_schedule_absent_new(mock_randint, dose_window_record, db_session, scheduler):
    mock_randint.return_value = 45
    maybe_schedule_absent_new(dose_window_record)
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-absent-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 45, tzinfo=utc)


# /admin tests
# TODO: finish this
# @freeze_time("2012-01-01 17:00:00")
# def test_manual_send_reminder(dose_window_record, db_session, scheduler, client):
#     client.post("/admin/manual", body={
#         "doseWindowId": str(dose_window_record.id),
#         "reminderType": "initial",
#         "manual_time": datetime
#     })
