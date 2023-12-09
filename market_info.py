from utils.time import date_by_adding_business_days, now_time, datetime_to_secs


min_time_zone_hours = 10
max_time_zone_hours = 23

trial_days = 1


def get_trial_end_date():
    end_trial_date = date_by_adding_business_days(now_time(), trial_days)
    end_trial_date = datetime_to_secs(end_trial_date)
    return end_trial_date


def is_trial_ended(trial_end_date):
    return datetime_to_secs(now_time()) > trial_end_date


def is_market_working():
    time = now_time()
    return min_time_zone_hours <= time.hour < max_time_zone_hours and time.weekday() < 5