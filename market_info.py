import pytz
from datetime import datetime, timedelta

min_time_zone_hours = 10
max_time_zone_hours = 23

trial_days = 3

time_zone = pytz.timezone("Europe/Bucharest")
origin_date = datetime(1900, 1, 1, tzinfo=time_zone)


def date_by_adding_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    additional_time = timedelta(days=0)
    print(from_date.weekday())
    print(from_date.weekday() >= 5)
    if from_date.weekday() >= 5:
        additional_time = timedelta(hours=24-from_date.hour-1, minutes=60-from_date.minute)
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5: # sunday = 6
            continue
        business_days_to_add -= 1
    current_date += additional_time
    return current_date


def get_trial_end_date():
    time_now = datetime.now(time_zone)
    end_trial_date = date_by_adding_business_days(time_now, trial_days)
    print(end_trial_date)
    return (end_trial_date - origin_date).total_seconds()


def is_trial_ended(trial_end_date):
    time_now = datetime.now(time_zone)
    time_now_secs = (time_now - origin_date).total_seconds()
    print(time_now_secs)
    print(trial_end_date)
    return (time_now - origin_date).total_seconds() > trial_end_date


def is_market_working():
    time_now = datetime.now(time_zone)
    return min_time_zone_hours <= time_now.hour < max_time_zone_hours


if __name__ == "__main__":
    pass