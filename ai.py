import numpy as np
from datetime import datetime, timedelta
from pytz import utc, timezone
from models import User


raw_csv_data = np.genfromtxt("density.csv", delimiter=",", dtype=None, encoding="utf8")

activity_by_user = {}
for row in raw_csv_data:
    activity_by_user[row[0]] = np.array(list(row)[1:])

print(activity_by_user)

TEMPERATURE = 0.05

def convert_utc_dt_to_minute(utc_dt, user):
    local_time = utc_dt.astimezone(timezone(user.timezone))
    start_of_day = local_time.replace(hour=4, minute=0, second=0, microsecond=0)
    timedelta_since_start_of_day = local_time - start_of_day
    minutes_elapsed = (timedelta_since_start_of_day.total_seconds() / 60 + 1440) % 1440
    return int(minutes_elapsed)

def convert_minute_to_current_day_time(minute, user):
    local_now = datetime.now(utc).astimezone(timezone(user.timezone))
    local_start_of_day = local_now.replace(hour=4, minute=0, second=0, microsecond=0)
    add_minutes = local_start_of_day + timedelta(minutes=minute)
    return add_minutes

def get_reminder_time_within_range(start_time, end_time, user):
    print(start_time)
    print(end_time)
    start_minute = convert_utc_dt_to_minute(start_time, user)
    end_minute = convert_utc_dt_to_minute(end_time, user)
    print(start_minute)
    print(end_minute)
    activity_density = activity_by_user.get(user.name, np.zeros(end_minute - start_minute))
    minute_range = activity_density[start_minute:end_minute]
    non_zero = minute_range[np.nonzero(minute_range)]
    minute_range += np.min(non_zero) * TEMPERATURE if len(non_zero) > 0 else 1 / len(minute_range)  # some smoothing
    probability_norm = minute_range / np.sum(minute_range)
    chosen_minute = int(np.random.choice(range(start_minute, end_minute), p=probability_norm))
    chosen_time = convert_minute_to_current_day_time(chosen_minute, user)
    return chosen_time


