from datetime import datetime
from pytz import utc

def get_time_now(tzaware=True):
    return datetime.now(utc) if tzaware else datetime.utcnow()