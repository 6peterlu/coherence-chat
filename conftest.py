import pytest
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from pytest_postgresql.janitor import DatabaseJanitor
from models import (
    db,
    # tables
    User,
    DoseWindow,
    Medication
)

from bot import app as prod_app, scheduler as prod_scheduler, scheduler_error_alert as prod_error_alert

# Retrieve a database connection string from the shell environment
try:
    DB_CONN = os.environ['TEST_DATABASE_URI']
except KeyError:
    raise KeyError('TEST_DATABASE_URI not found. You must export a database ' +
                   'connection string to the environmental variable ' +
                   'TEST_DATABASE_URI in order to run tests.')
else:
    DB_OPTS = sa.engine.url.make_url(DB_CONN).translate_connect_args()


@pytest.fixture(scope='session')
def database(request):
    '''
    Create a Postgres database for the tests, and drop it when the tests are done.
    '''
    pg_host = DB_OPTS.get("host")
    pg_port = DB_OPTS.get("port")
    pg_user = DB_OPTS.get("username")
    pg_db = DB_OPTS["database"]

    DatabaseJanitor(pg_user, pg_host, pg_port, pg_db, 12.4).init()  # PG version: 12.4
    @request.addfinalizer
    def drop_database():
        DatabaseJanitor(pg_user, pg_host, pg_port, pg_db, 12.4).drop()


@pytest.fixture(scope='session')
def app(database):
    '''
    Create a Flask app context for the tests.
    '''
    prod_app.config['SQLALCHEMY_DATABASE_URI'] = DB_CONN
    prod_app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    return prod_app


@pytest.fixture(scope='session')
def scheduler(app):
    prod_scheduler.remove_listener(prod_error_alert)  # prevent these from triggering
    prod_scheduler.remove_all_jobs()  # just clear the local db whatever
    return prod_scheduler

@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture(scope='session')
def _db(app):
    '''
    Provide the transactional fixtures with access to the database via a Flask-SQLAlchemy
    database connection.
    '''
    db.init_app(app)
    db.create_all()

    return db


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
        start_hour=13+7,
        start_minute=0,
        end_hour=15+7,
        end_minute=0,
        user_id=user_record.id
    )
    db_session.add(dose_window_obj)
    db_session.commit()
    return dose_window_obj

# lol
def test_scheduled_function(*_):
    pass

@pytest.fixture
def medication_record(db_session, dose_window_record, user_record, scheduler):
    medication_obj = Medication(
        user_id=user_record.id,
        medication_name="Zoloft",
        dose_windows=[dose_window_record],
        scheduler_tuple=(scheduler, test_scheduled_function)
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj

@pytest.fixture
def medication_record_2(db_session, dose_window_record, user_record, scheduler):
    medication_obj = Medication(
        user_id=user_record.id,
        medication_name="Lisinopril",
        dose_windows=[dose_window_record],
        scheduler_tuple=(scheduler, test_scheduled_function)
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj


@pytest.fixture
def medication_record_for_dose_window_out_of_range(db_session, dose_window_record_out_of_range, user_record, scheduler):
    medication_obj = Medication(
        user_id=user_record.id,
        medication_name="Zoloft",
        dose_windows=[dose_window_record_out_of_range],
        scheduler_tuple=(scheduler, test_scheduled_function)
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj


@pytest.fixture
def user_record_paused(db_session):
    user_obj = User(
        phone_number="3604508656",
        name="Peter",
        paused=True
    )
    db_session.add(user_obj)
    db_session.commit()
    return user_obj


@pytest.fixture
def dose_window_record_for_paused_user(db_session, user_record_paused):
    dose_window_obj = DoseWindow(
        start_hour=9+7,
        start_minute=0,
        end_hour=11+7,
        end_minute=0,
        user_id=user_record_paused.id
    )
    db_session.add(dose_window_obj)
    db_session.commit()
    return dose_window_obj

def test_scheduled_function(*_):
    pass

@pytest.fixture
def medication_record_for_paused_user(db_session, dose_window_record_for_paused_user, user_record_paused, scheduler):
    medication_obj = Medication(
        user_id=user_record_paused.id,
        medication_name="Zoloft",
        dose_windows=[dose_window_record_for_paused_user],
        scheduler_tuple=(scheduler, test_scheduled_function)
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj

@pytest.fixture
def medication_record_for_paused_user_2(db_session, dose_window_record_for_paused_user, user_record_paused, scheduler):
    medication_obj = Medication(
        user_id=user_record_paused.id,
        medication_name="Lisinopril",
        dose_windows=[dose_window_record_for_paused_user],
        scheduler_tuple=(scheduler, test_scheduled_function)
    )
    db_session.add(medication_obj)
    db_session.commit()
    return medication_obj