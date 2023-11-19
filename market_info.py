import pytz
from datetime import datetime, timedelta

import user_module

min_time_zone_hours = 10
max_time_zone_hours = 23

trial_days = 3

time_zone = pytz.timezone("Europe/Bucharest")
origin_date = datetime(1900, 1, 1, tzinfo=time_zone)


def get_time():
    return datetime.now(time_zone)


def get_time_in_seconds():
    return datetime.timestamp(get_time())


def secs_to_date(end_date):
    res = datetime.fromtimestamp(end_date) #.strftime("%A, %B %d, %Y %I:%M:%S")
    return res


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
    end_trial_date = datetime.timestamp(end_trial_date)
    return end_trial_date


def is_trial_ended(trial_end_date):
    time_now = datetime.now(time_zone)
    return datetime.timestamp(time_now) > trial_end_date


def is_market_working():
    time_now = datetime.now(time_zone)
    return min_time_zone_hours <= time_now.hour < max_time_zone_hours


if __name__ == "__main__":
    # res = secs_to_date(get_trial_end_date())
    res = secs_to_date(user_module.get_user_trial_end_date(5359645780))
    print(res)