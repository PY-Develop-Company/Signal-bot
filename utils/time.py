from datetime import datetime, timedelta

import pytz


time_zone = pytz.timezone("Europe/Bucharest")
origin_date_time_zone = datetime(1900, 1, 1, tzinfo=time_zone)
origin_date = datetime(1900, 1, 1)

day_temp = datetime.now(time_zone)


def is_new_day():
    global day_temp
    if day_temp.day != datetime.now(time_zone).day:
        day_temp = now_time()
        return True

    return False


def now_time():
    return str_to_datetime(str(datetime.now(time_zone)).split(".")[0])


def str_to_datetime(time):
    return datetime.strptime(time, "%Y-%m-%d %H:%M:%S")


def datetime_to_str(time):
    return datetime.strftime(time, "%Y-%m-%d %H:%M:%S")


def datetime_to_secs(dt):
    return datetime.timestamp(dt)


def secs_to_date(end_date):
    res = datetime.fromtimestamp(end_date)  # .strftime("%A, %B %d, %Y %I:%M:%S")
    return res


def date_by_adding_business_days(from_date, add_days):
    business_days_to_add = add_days
    current_date = from_date
    additional_time = timedelta(days=0)

    if from_date.weekday() >= 5:
        additional_time = timedelta(hours=24-from_date.hour-1, minutes=60-from_date.minute)
    while business_days_to_add > 0:
        current_date += timedelta(days=1)
        weekday = current_date.weekday()
        if weekday >= 5:  # sunday = 6
            continue
        business_days_to_add -= 1
    current_date += additional_time
    return current_date
