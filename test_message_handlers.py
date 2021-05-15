from message_handlers import (
    active_state_message_handler,
    maybe_schedule_absent_new,
    send_absent_text_new,
    send_followup_text_new
)
from unittest import mock
from models import (
    EventLog
)
from freezegun import freeze_time
import tzlocal
from datetime import datetime
from pytz import utc, timezone

def stub_fn(*_):
    pass


@mock.patch("message_handlers.text_fallback")
@mock.patch("message_handlers.get_thanks_message")
def test_thanks_with_manual_takeover(
        get_thanks_message_mock,
        text_fallback_mock,
        db_session,
        user_record_with_manual_takeover
):
    active_state_message_handler(
        [{'modifiers': {'emotion': 'excited'}, 'type': 'thanks', "raw": "T. Thanks!"}],
        user_record_with_manual_takeover,
        None,
        f"+1{user_record_with_manual_takeover.phone_number}",
        "blah"
    )
    assert not get_thanks_message_mock.called
    assert text_fallback_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "manually_silenced"
    assert all_events[0].description == "T. Thanks!"
    assert all_events[0].user_id == user_record_with_manual_takeover.id
    assert all_events[0].dose_window_id is None


# NOTE: freezegun freezes UTC time
@freeze_time("2012-01-01 17:00:00")  # within range of dose_window_record
@mock.patch("message_handlers.get_take_message_new")
def test_take(
    take_message_mock,
    client, db_session, user_record,
    dose_window_record, medication_record, scheduler
):
    # seed scheduler jobs to test removal
    scheduler.add_job(f"{dose_window_record.id}-followup-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    scheduler.add_job(f"{dose_window_record.id}-absent-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    scheduler.add_job(f"{dose_window_record.id}-boundary-new", stub_fn, trigger="date", run_date=datetime(2012, 1, 1, 18, tzinfo=utc))
    local_tz = tzlocal.get_localzone()  # handles test machine in diff tz
    active_state_message_handler(
        [{'type': 'take', 'modifiers': {'emotion': 'neutral'}, "raw": "T"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "T"
    )
    assert take_message_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "take"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id == medication_record.id
    assert local_tz.localize(all_events[0].event_time) == datetime(2012, 1, 1, 17, tzinfo=utc)  # match freezegun time
    for job_type in ["followup", "absent", "boundary"]:
        assert scheduler.get_job(f"{dose_window_record.id}-{job_type}-new") is None


@freeze_time("2012-01-01 17:00:00")
@mock.patch("message_handlers.remove_jobs_helper")
def test_canned_delay_near_boundary(
    remove_jobs_helper_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    active_state_message_handler(
        [{'type': 'special', 'payload': '3', "raw": "3"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "3"
    )
    assert remove_jobs_helper_mock.called
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


@freeze_time("2012-01-01 17:00:00")
@mock.patch("message_handlers.remove_jobs_helper")
def test_delay_minutes(
    remove_jobs_helper_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    active_state_message_handler(
        [{'type': 'delay_minutes', 'payload': 20, "raw": "20"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "20"
    )
    assert remove_jobs_helper_mock.called
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
@mock.patch("message_handlers.remove_jobs_helper")
def test_delay_minutes_near_boundary(
    remove_jobs_helper_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    active_state_message_handler(
        [{'type': 'delay_minutes', 'payload': 60, "raw": "60"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "20"
    )
    assert remove_jobs_helper_mock.called
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


@freeze_time("2012-01-01 17:00:00")
@mock.patch("message_handlers.remove_jobs_helper")
def test_requested_alarm_time(
    remove_jobs_helper_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    active_state_message_handler(
        [{'type': 'requested_alarm_time', 'payload': {"time": user_tz.localize(datetime(2012, 1, 1, 9, 30, tzinfo=None)), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "30min"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "30min"
    )
    assert remove_jobs_helper_mock.called
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
@mock.patch("message_handlers.remove_jobs_helper")
def test_requested_alarm_time_near_boundary(
    remove_jobs_helper_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    user_tz = timezone(user_record.timezone)
    active_state_message_handler(
        [{'type': 'requested_alarm_time', 'payload': {"time": datetime(2012, 1, 1, 10, tzinfo=user_tz), "am_pm_defined": True, "needs_tz_convert": False}, "raw": "1hr"}],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        "1hr"
    )
    assert remove_jobs_helper_mock.called
    all_events = db_session.query(EventLog).all()
    assert len(all_events) == 1
    assert all_events[0].event_type == "reminder_delay"
    assert all_events[0].user_id == user_record.id
    assert all_events[0].dose_window_id == dose_window_record.id
    assert all_events[0].medication_id is None
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-followup-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 50, tzinfo=utc)


@freeze_time("2012-01-01 17:00:00")
@mock.patch("message_handlers.remove_jobs_helper")
@mock.patch("message_handlers.get_reminder_time_within_range")
def test_activity(
    get_reminder_time_mock, remove_jobs_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    get_reminder_time_mock.return_value = datetime(2012, 1, 1, 17, 25, tzinfo=utc)
    active_state_message_handler(
        [{
            'type': 'activity',
            'payload': {
                'type': 'short',
                'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
                'concept': 'leisure'
            },
            'raw': 'walking'
        }],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        'walking'
    )
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
@mock.patch("message_handlers.remove_jobs_helper")
@mock.patch("message_handlers.get_reminder_time_within_range")
def test_activity_near_boundary(
    get_reminder_time_mock, remove_jobs_mock,
    client, db_session, user_record, dose_window_record,
    medication_record, scheduler
):
    get_reminder_time_mock.return_value = datetime(2012, 1, 1, 18, 0, tzinfo=utc)
    active_state_message_handler(
        [{
            'type': 'activity',
            'payload': {
                'type': 'short',
                'response': "Computing ideal reminder time...done. Enjoy your walk! We'll check in later.",
                'concept': 'leisure'
            },
            'raw': 'walking'
        }],
        user_record,
        dose_window_record,
        f"+1{user_record.phone_number}",
        'walking'
    )
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


@mock.patch("message_handlers.remove_jobs_helper")
@mock.patch("message_handlers.maybe_schedule_absent_new")
def test_send_followup_text_new(maybe_schedule_absent_mock, remove_jobs_helper_mock, dose_window_record, db_session):
    send_followup_text_new(dose_window_record.id)
    assert remove_jobs_helper_mock.called
    assert maybe_schedule_absent_mock.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "followup"


@mock.patch("message_handlers.maybe_schedule_absent_new")
def test_send_absent_text_new(
    maybe_schedule_absent_mock, dose_window_record, db_session
):
    send_absent_text_new(dose_window_record.id)
    assert maybe_schedule_absent_mock.called
    all_event_logs = db_session.query(EventLog).all()
    assert len(all_event_logs) == 1
    assert all_event_logs[0].event_type == "absent"


@freeze_time("2012-01-01 17:00:00")
@mock.patch("message_handlers.get_reminder_time_within_range")
def test_maybe_schedule_absent_new(mock_get_reminder_time, dose_window_record, db_session, scheduler):
    mock_get_reminder_time.return_value = datetime(2012, 1, 1, 17, 45, tzinfo=utc)
    maybe_schedule_absent_new(dose_window_record)
    scheduled_job = scheduler.get_job(f"{dose_window_record.id}-absent-new")
    assert scheduled_job is not None
    assert scheduled_job.next_run_time == datetime(2012, 1, 1, 17, 45, tzinfo=utc)