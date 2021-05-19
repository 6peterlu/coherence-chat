from bot import maybe_schedule_absent_new, send_absent_text_new, send_followup_text_new, send_intro_text_new
import pytest
from unittest import mock
import os
from freezegun import freeze_time
from datetime import datetime
from pytz import utc, timezone
import tzlocal
from requests.auth import _basic_auth_str


from models import (
    DoseWindow,
    EventLog,
    Medication,
    Online,
    User,
    # schemas
    UserSchema,
    # enums
    UserState
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


@pytest.fixture
def boundary_event_record(db_session, dose_window_record, user_record):
    boundary_time = datetime(2012, 1, 1, 18, 0, tzinfo=utc)
    event_obj = EventLog("boundary", user_record.id, dose_window_record.id, None, event_time=boundary_time)
    db_session.add(event_obj)
    db_session.commit()
    return event_obj

def stub_fn(*_):
    pass


@mock.patch("bot.segment_message")
def test_not_interpretable(segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = []
    client.post("/bot", query_string={"From": "+13604508655", "Body": "blah"})
    # assert text_fallback_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "not_interpretable"
    assert all_events[0].description == "blah"
    assert all_events[0].user_id == user_record.id


@mock.patch("bot.segment_message")
def test_thanks_with_manual_takeover(
        segment_message_mock,
        client,
        db_session,
        user_record_with_manual_takeover
):
    segment_message_mock.return_value = [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert not thanks_message_mock.called
    # assert fallback_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "manually_silenced"
    assert all_events[0].description == "T. Thanks!"
    assert all_events[0].user_id == user_record_with_manual_takeover.id
    assert all_events[0].dose_window_id is None

# NOTE: freezegun freezes UTC time
@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.segment_message")
def test_take(
    segment_message_mock,
    client, db_session, user_record,
    dose_window_record, medication_record, scheduler
):
    # seed scheduler jobs to test removal
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert take_message_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)  # match freezegun time
    for job_type in ["followup", "absent", "boundary"]:
        assert scheduler.get_job(f"{dose_window_record.id}-{job_type}-new") is None


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.segment_message")
def test_take_multiple_medications(
    segment_message_mock,
    client, db_session, user_record, dose_window_record, medication_record,
    medication_record_2
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert take_message_mock.called
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
@mock.patch("bot.segment_message")
def test_take_dose_already_recorded(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, medication_take_event_record_in_dose_window
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2  # first one is our inserted take record
    assert all_events[1].event_type == "attempted_rerecord"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 20:00:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_cancel_boundary(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, boundary_event_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 20, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range,
    medication_record_for_dose_window_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record_out_of_range.id
    assert all_events[0].medication_id is medication_record_for_dose_window_out_of_range.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 15:00:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_multi_dose_window(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range, dose_window_record,  # 16-18
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id  # match the second one
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 15, tzinfo=utc)

@freeze_time("2012-01-01 15:00:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_multi_dose_window_rerecord(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range, dose_window_record,  # 16-18
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    client.post("/bot", query_string={"From": "+13604508655"}) # rerecord
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id  # match the second one
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 15, tzinfo=utc)
    assert all_events[1].event_type == "attempted_rerecord"


@freeze_time("2012-01-01 23:00:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_multi_dose_window_2(
    segment_message_mock, client, db_session, user_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range, dose_window_record,  # 16-18
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record_out_of_range.id  # match the second one
    assert all_events[0].medication_id is medication_record_for_dose_window_out_of_range.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 23, tzinfo=utc)


@freeze_time("2012-01-01 19:30:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_multi_dose_window_3(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range, dose_window_record,  # 16-18
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record_out_of_range.id  # match the second one
    assert all_events[0].medication_id is medication_record_for_dose_window_out_of_range.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 19, 30, tzinfo=utc)


@freeze_time("2012-01-01 6:30:00")
@mock.patch("bot.segment_message")
def test_take_dose_out_of_range_multi_dose_window_4(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range, dose_window_record,  # 16-18
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record_out_of_range.id  # match the second one
    assert all_events[0].medication_id is medication_record_for_dose_window_out_of_range.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 6, 30, tzinfo=utc)


@freeze_time("2012-01-02 4:30:00")
@mock.patch("bot.segment_message")
def test_take_with_input_time(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time":  datetime(2012, 1, 2, 16, 50, tzinfo=utc).astimezone(local_tz), "am_pm_defined": False, "needs_tz_convert": False}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 16, 50, tzinfo=utc)

@freeze_time("2012-01-02 4:30:00")
@mock.patch("bot.segment_message")
def test_take_with_input_time_rerecord(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time":  datetime(2012, 1, 2, 16, 50, tzinfo=utc).astimezone(local_tz), "am_pm_defined": False, "needs_tz_convert": False}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 16, 50, tzinfo=utc)
    assert all_events[1].event_type == "attempted_rerecord"


@freeze_time("2012-01-02 7:30:00")
@mock.patch("bot.segment_message")
def test_take_with_input_time_am_pm_defined(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time": datetime(2012, 1, 2, 16, 50, tzinfo=utc).astimezone(local_tz), "am_pm_defined": True, "needs_tz_convert": False}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 16, 50, tzinfo=utc)


@freeze_time("2012-01-02 7:30:00")
@mock.patch("bot.segment_message")
def test_take_with_input_time_am_pm_defined_fuzzy(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,  # 16-18
    medication_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time": datetime(2012, 1, 2, 15, 0, tzinfo=utc).astimezone(local_tz), "am_pm_defined": True, "needs_tz_convert": False}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 15, 0, tzinfo=utc)


@freeze_time("2012-01-02 7:30:00")
@mock.patch("bot.segment_message")
def test_take_with_input_time_am_pm_defined_fuzzy_rerecord(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,  # 16-18
    medication_record, dose_window_record_out_of_range,  # 20-22
    medication_record_for_dose_window_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time": datetime(2012, 1, 2, 15, 0, tzinfo=utc).astimezone(local_tz), "am_pm_defined": True, "needs_tz_convert": False}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    client.post("/bot", query_string={"From": "+13604508655"})  # rerecord
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is dose_window_record.id
    assert all_events[0].medication_id is medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 15, 0, tzinfo=utc)
    assert all_events[1].event_type == "attempted_rerecord"

@freeze_time("2012-01-02 8:30:00")  # 12:30am
@mock.patch("bot.segment_message")
def test_take_after_midnight(segment_message_mock, client, db_session, user_record, past_midnight_dose_window_record, scheduler, past_midnight_medication_record):
    scheduler.add_job(f"{past_midnight_dose_window_record.id}-absent-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 2, 9, tzinfo=utc))
    scheduler.add_job(f"{past_midnight_dose_window_record.id}-followup-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 2, 9, tzinfo=utc))
    scheduler.add_job(f"{past_midnight_dose_window_record.id}-boundary-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 2, 9, tzinfo=utc))
    segment_message_mock.return_value = [{
        'type': 'take',
        'modifiers': {'emotion': 'neutral'},
        "raw": "T", 'payload': {"time": datetime(2012, 1, 2, 0, 5, tzinfo=utc), "am_pm_defined": True, "needs_tz_convert": True}
    }]
    client.post("/bot", query_string={"From": "+13604508655"})
    assert scheduler.get_job(f"{past_midnight_dose_window_record.id}-boundary-new") is None




@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.segment_message")
def test_skip(segment_message_mock,  client, db_session, user_record, dose_window_record, medication_record):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "skip"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)
    # assert remove_jobs_mock.called


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.segment_message")
def test_skip_dose_already_recorded(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, medication_take_event_record_in_dose_window
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 2  # first one is our inserted take record
    assert all_events[1].event_type == "attempted_rerecord"
    assert all_events[1].user_id == user_record.id
    assert all_events[1].dose_window_id == dose_window_record.id
    assert all_events[1].medication_id == medication_record.id
    assert local_tz.localize(all_events[1].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("bot.segment_message")
def test_skip_multiple_medications(
    segment_message_mock,
    client, db_session, user_record, dose_window_record, medication_record,
    medication_record_2
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
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
@mock.patch("bot.segment_message")
def test_skip_dose_out_of_range(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'skip', "raw": "S :)"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1  # first one is our inserted take record
    # we expect it to record again since the record is outdated
    assert all_events[0].event_type == "out_of_range"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is None
    assert all_events[0].medication_id is None
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)

@mock.patch("bot.segment_message")
def test_error_report( segment_message_mock, client, db_session, user_record):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': 'x', "raw": "x"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "user_reported_error"
    assert all_events[0].description is None
    assert all_events[0].user_id == user_record.id
    assert all_events[0].medication_id is None
    assert all_events[0].dose_window_id is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_canned_delay(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_canned_delay_near_boundary(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '3', "raw": "3"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_canned_delay_too_late(
     segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_canned_delay_out_of_range(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
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
def test_delay_minutes(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 20, "raw": "20"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_delay_minutes_near_boundary(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 60, "raw": "60"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_delay_minutes_too_late(
     segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    segment_message_mock.return_value = [{'type': 'delay_minutes', 'payload': 60, "raw": "60"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "requested_time_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_delay_minutes_out_of_range(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    segment_message_mock.return_value = [{'type': 'special', 'payload': '1', "raw": "1"}]
    client.post("/bot", query_string={"From": "+13604508655"})
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
def test_requested_alarm_time(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': {"time": user_tz.localize(datetime(2012, 1, 1, 9, 30, tzinfo=None)), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "30min"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_requested_alarm_time_near_boundary(
    segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': {"time": datetime(2012, 1, 1, 10, tzinfo=user_tz), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "1hr"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    # assert remove_jobs_mock.called
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
def test_requested_alarm_time_too_late(
     segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': {"time": datetime(2012, 1, 1, 10, tzinfo=user_tz), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "1hr"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 0
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_requested_alarm_time_out_of_range(
    segment_message_mock,
    client, db_session, user_record, dose_window_record_out_of_range
):
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    user_tz = timezone(user_record.timezone)
    segment_message_mock.return_value = [{'type': 'requested_alarm_time', 'payload': {"time": datetime(2012, 1, 1, 10, tzinfo=user_tz), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "1hr"}]
    client.post("/bot", query_string={"From": "+13604508655"})
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1  # first one is our inserted take record
    # we expect it to record again since the record is outdated
    assert all_events[0].event_type == "out_of_range"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is None
    assert all_events[0].medication_id is None
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:55:00")
@mock.patch("bot.segment_message")
@mock.patch("bot.get_reminder_time_within_range")
def test_activity_too_late(
    get_reminder_time_mock,  segment_message_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    get_reminder_time_mock.return_value = datetime(2012, 1, 1, 18, 5, tzinfo=utc)
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
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "activity"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is None

@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.segment_message")
def test_activity_out_of_range(
    segment_message_mock,
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
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1  # first one is our inserted take record
    # we expect it to record again since the record is outdated
    assert all_events[0].event_type == "out_of_range"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id is None
    assert all_events[0].medication_id is None
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")
@mock.patch("bot.maybe_schedule_absent_new")
def test_send_intro_text_new(mock_schedule_absent_new, dose_window_record, medication_record, db_session):
    send_intro_text_new(dose_window_record.id)
    assert mock_schedule_absent_new.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "initial"

@freeze_time("2012-01-01 17:00:00")
def test_intro_text_not_sent_if_already_recorded(
    dose_window_record, medication_record, medication_take_event_record_in_dose_window, db_session):
    send_intro_text_new(dose_window_record.id)
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1


# /admin tests
# TODO: finish this
# @freeze_time("2012-01-01 17:00:00")
# def test_manual_send_reminder(dose_window_record, db_session, scheduler, client):
#     client.post("/admin/manual", body={
#         "doseWindowId": str(dose_window_record.id),
#         "reminderType": "initial",
#         "manual_time": datetime
#     })


@mock.patch("bot.send_pause_message")
def test_admin_pause(mock_send_pause_message, user_record, dose_window_record, medication_record, scheduler, client):
    client.post("/admin/pauseUser", json={
        "userId": user_record.id
    }, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    assert not mock_send_pause_message.called

@mock.patch("bot.send_upcoming_dose_message")
@mock.patch("bot.send_intro_text_new")
def test_admin_resume(
    mock_send_intro_text, mock_send_upcoming_dose_message, user_record,
    dose_window_record, medication_record, scheduler, client
):
    client.post("/admin/resumeUser", json={
        "userId": user_record.id
    }, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    assert not mock_send_intro_text.called
    assert not mock_send_upcoming_dose_message.called


def test_admin_create_user(client, db_session, user_record):
    client.post("/admin/createUser", json={
        "phoneNumber": "3604508656",
        "name": "Peter"
    }, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    users = db_session.query(User).all()
    assert len(users) == 2

def test_admin_create_dose_window(client, db_session, user_record):
    client.post("/admin/createDoseWindow", json={
        "userId": user_record.id
    }, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    assert len(user_record.dose_windows) == 1
    assert len(user_record.doses) == 1

def test_admin_deactivate_dose_window(client, db_session, user_record, medication_record, dose_window_record):
    client.post("/admin/deactivateDoseWindow", json={
        "doseWindowId": dose_window_record.id
    }, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    assert len(user_record.active_dose_windows) == 0
    assert len(user_record.dose_windows) == 1


def test_admin_manual_takeover(client, db_session, user_record):
    # print(online_record)
    # print(online_record.id)
    client.post("/admin/manualTakeover", json={"userId": user_record.id}, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    online_obj = Online.query.first()
    # assert False
    assert online_obj.online is True
    assert user_record.manual_takeover is True


def test_announcement(client, db_session, user_record):
    client.post("/admin/setPendingAnnouncement", json={"announcement": "announce!"}, headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)})
    announcement_events = db_session.query(EventLog).filter(EventLog.event_type == "feature_announcement", EventLog.user_id == user_record.id).all()
    assert len(announcement_events) == 0
    assert user_record.pending_announcement == "announce!"
    client.post("/bot", query_string={"From": "+13604508655"})
    announcement_events = db_session.query(EventLog).filter(EventLog.event_type == "feature_announcement", EventLog.user_id == user_record.id).all()
    assert len(announcement_events) == 1


def test_user_create_dose_window(client, db_session, user_record):
    client.post(
        "/doseWindow/update/new",
        headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)},
        json={"updatedDoseWindow": {"start_hour": 0, "start_minute":0, "end_hour": 0, "end_minute": 0}}
    )
    assert len(db_session.query(DoseWindow).all()) == 1
    assert len(db_session.query(Medication).all()) == 1


@freeze_time("2012-01-01 17:00:00")
def test_user_subscription_expire_bot_endpoint(client, db_session, user_record):
    user_record.end_of_service = datetime(2011, 1, 1)
    db_session.add(user_record)  # add needed only for mock db_session
    db_session.commit()
    assert user_record.state == UserState.ACTIVE
    client.post("/bot", query_string={"From": "+13604508655"})
    assert user_record.state == UserState.SUBSCRIPTION_EXPIRED


@freeze_time("2012-01-01 17:00:00")
def test_user_subscription_expire_other_endpoint(client, db_session, user_record):
    user_record.end_of_service = datetime(2011, 1, 1)
    db_session.add(user_record)  # add needed only for mock db_session
    db_session.commit()
    assert user_record.state == UserState.ACTIVE
    client.get(
        "/patientData/new",
        query_string={"calendarMonth": "5"},
        headers = {'Authorization': _basic_auth_str(user_record.generate_auth_token(), None)}
    )
    assert user_record.state == UserState.SUBSCRIPTION_EXPIRED