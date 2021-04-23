import pytest
import os
from flask import Flask
from flask_sqlalchemy import SQLAlchemy
import sqlalchemy as sa
from pytest_postgresql.janitor import DatabaseJanitor
from models import db

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
