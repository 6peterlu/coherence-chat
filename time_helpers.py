from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta
from pytz import utc, timezone
import tzlocal

DAY_BOUNDARY = 4  # 4AM

def get_time_now(tzaware=True):
    return datetime.now(utc) if tzaware else datetime.utcnow()

# the long awaited helper...
def get_start_of_day(tz_string, days_delta=0, months_delta=0, local=False):
    tz_info = timezone(tz_string)
    time_now = get_time_now()
    local_time_now = time_now.astimezone(tz_info)
    if local_time_now.hour < DAY_BOUNDARY:
        local_time_now -= timedelta(days=1)
    local_time_now = local_time_now.replace(hour=4, minute=0, second=0, microsecond=0)
    local_time_now += relativedelta(days=days_delta, months=months_delta)
    if local:
        return local_time_now
    else:
        return local_time_now.astimezone(utc)

# dt is expected to be naive
def convert_naive_to_local_machine_time(dt):
    return tzlocal.get_localzone().localize(dt)