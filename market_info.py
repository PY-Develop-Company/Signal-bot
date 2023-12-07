from my_time import date_by_adding_business_days, now_time
from datetime import datetime

min_time_zone_hours = 10
max_time_zone_hours = 23

trial_days = 1


def get_trial_end_date():
    time_now = now_time()
    end_trial_date = date_by_adding_business_days(time_now, trial_days)
    end_trial_date = datetime.timestamp(end_trial_date)
    return end_trial_date


def is_trial_ended(trial_end_date):
    time_now = now_time()
    return datetime.timestamp(time_now) > trial_end_date


def is_market_working():
    time_now = now_time()
    return min_time_zone_hours <= time_now.hour < max_time_zone_hours
