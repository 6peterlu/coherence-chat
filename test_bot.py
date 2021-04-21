
import pytest
from bot import Online


@pytest.fixture
def dose_record(db_session):
    online_obj = Online(online=True)
    db_session.add(online_obj)
    db_session.commit()
    return online_obj


def test_bot(dose_record):
    print(dose_record)
    assert dose_record.id == Online.query.all()[0].id