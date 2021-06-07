from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import EventLog, User, UserState
from pytz import timezone, utc
import csv

import numpy as np
import matplotlib.pyplot as plt
from sklearn.neighbors import KernelDensity
from sklearn.model_selection import GridSearchCV

from math import floor, sqrt
from statistics import stdev

DATABASE_URI = 'postgres+psycopg2://peterlu:hello@localhost:5432/analysis_db'

engine = create_engine(DATABASE_URI)
Session = sessionmaker(bind=engine)

def compute_activity_densities():
    s = Session()

    user_driven_events = [
        "take",
        "skip",
        "paused",
        "resumed",
        "user_reported_error",
        "out_of_range",
        "not_interpretable",
        "requested_time_delay",
        "activity"
    ]

    qualifying_users = [
        "Steven",
        "Cheryl",
        "Jeanette",
        "Charles",
        "Hadara",
        "Karrie",
        "Leann",
        "Tao"
    ]

    with open('density.csv', 'w') as csvfile:
        csvwriter = csv.writer(csvfile)
        for user in qualifying_users:
            # get events for user
            user_obj = s.query(User).filter_by(name=user).one_or_none()
            events = s.query(EventLog).filter(EventLog.user == user_obj, EventLog.event_type.in_(user_driven_events)).all()

            # translate to minutes since beginning of day
            def minutes_since_start_of_local_day(utc_dt):
                local_time = utc_dt.replace(tzinfo=utc).astimezone(timezone(user_obj.timezone))
                start_of_day = local_time.replace(hour=4, minute=0, second=0, microsecond=0)
                print(f"{utc_dt} -> {local_time} -> {start_of_day}")
                timedelta_since_start_of_day = local_time - start_of_day
                minutes_elapsed = (timedelta_since_start_of_day.total_seconds() / 60 + 1440) % 1440
                return minutes_elapsed

            x_train = np.expand_dims([minutes_since_start_of_local_day(event.event_time) for event in events], axis=1)

            # even samples across minutes
            x_test = np.linspace(0, 1440, 1440)[:, np.newaxis]

            kde_model = KernelDensity(kernel='tophat', bandwidth=15)  # heuristically discovered
            kde_model.fit(x_train)
            scores = kde_model.score_samples(x_test)
            csvwriter.writerow([user] + list(np.exp(scores)))


    # close the session to free resources
    s.close()


def compute_adherence_metrics():
    s = Session()
    active_user_list = s.query(User).filter(User.state.in_([UserState.ACTIVE, UserState.PAUSED, UserState.SUBSCRIPTION_EXPIRED])).all()
    adherent_user_count = 0
    nonadherent_user_count = 0
    global_adherence_by_day = []
    for user in active_user_list:
        if user.phone_number == "3604508655":
            continue
        dose_history_events = s.query(EventLog).filter(
            EventLog.user_id == user.id,
            EventLog.event_type.in_(["take", "boundary", "skip"]
        )).order_by(EventLog.event_time.asc()).all()
        first_event_time = dose_history_events[0].event_time
        adherence_fraction_by_day = []
        take_count = 0
        miss_count = 0
        skip_count = 0
        for event in dose_history_events:
            if event.event_type == "take":
                take_count += 1
            elif event.event_type == "boundary":
                miss_count += 1
            elif event.event_type == "skip":
                skip_count += 1
            days_since_start = floor((event.event_time - first_event_time).days)
            while days_since_start >= len(global_adherence_by_day):
                global_adherence_by_day.append([0, 0, 0])
            while days_since_start >= len(adherence_fraction_by_day):
                adherence_fraction_by_day.append(None)
                global_adherence_by_day[days_since_start][2] += 1

            adherence_fraction_to_date = (take_count + skip_count) / (take_count + skip_count + miss_count)
            adherence_fraction_by_day[days_since_start] = adherence_fraction_to_date
            if adherence_fraction_to_date >= 0.8:
                global_adherence_by_day[days_since_start][0] += 1
            else:
                global_adherence_by_day[days_since_start][1] += 1

        adherence_fraction = (take_count + skip_count) / (take_count + skip_count + miss_count)
        print(f"{user.name} {adherence_fraction}")
        print(adherence_fraction_by_day)
        if adherence_fraction < 0.8:
            nonadherent_user_count += 1
        else:
            adherent_user_count += 1
    print(f"adherent user fraction = {adherent_user_count}/{adherent_user_count + nonadherent_user_count} = {adherent_user_count/(adherent_user_count + nonadherent_user_count)}")
    print([(x[0] / (x[0] + x[1]), x[2]) for x in global_adherence_by_day])
    adherence_by_day = [x[0] / (x[0] + x[1]) if x[2] > 1 else float("NaN") for x in global_adherence_by_day]
    std_errors = [stdev([1] * x[0] + [0] * x[1]) / sqrt(x[2]) if x[2] > 1 else float("NaN") for x in global_adherence_by_day]
    print(std_errors)
    plt.plot(adherence_by_day)
    plt.errorbar(
        range(len(adherence_by_day)),
        adherence_by_day,
        yerr=std_errors,
        ecolor=(0.5, 0.5, 0.5, 0.3),
        capsize=3,
        elinewidth=1,
        linewidth=4
    )
    plt.ylim(0, 1)
    plt.xlabel("days since starting Coherence")
    plt.ylabel("Percent of users taking >= 80% of medications")
    plt.grid(axis='y', linestyle='--', linewidth=1)
    plt.show()
    # close the session to free resources
    s.close()


compute_adherence_metrics()