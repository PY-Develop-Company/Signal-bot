from pandas import Timedelta
from tvDatafeed import Interval

import math
from datetime import timedelta


def timedelta_to_close_string(interval, bars_count=3):
    delay_days = int(1 / Timedelta(days=1) * bars_count)
    delay_hours = int(interval / Timedelta(hours=1) * bars_count - delay_days * 24)
    delay_minutes = int(interval / Timedelta(minutes=1) * bars_count - delay_days * 24 * 60 - delay_hours * 60)

    if delay_days > 0:
        str(delay_days) + "Д"
    elif delay_hours > 0:
        res = str(delay_hours) + "ч"
        if delay_minutes > 0:
            res += " " + str(delay_minutes) + "мин"
        return res
    return str(delay_minutes) + "мин"


def interval_to_datetime(interval: Interval):
    if interval == Interval.in_1_minute:
        return timedelta(minutes=1)
    elif interval == Interval.in_3_minute:
        return timedelta(minutes=3)
    elif interval == Interval.in_5_minute:
        return timedelta(minutes=5)
    elif interval == Interval.in_15_minute:
        return timedelta(minutes=15)
    elif interval == Interval.in_30_minute:
        return timedelta(minutes=30)
    elif interval == Interval.in_45_minute:
        return timedelta(minutes=45)
    elif interval == Interval.in_1_hour:
        return timedelta(hours=1)
    elif interval == Interval.in_2_hour:
        return timedelta(hours=2)
    else:
        return None


def datetime_to_interval(datetime):
    datetime = math.floor(datetime.total_seconds() / 60)
    if datetime == 120:
        return Interval.in_2_hour
    if datetime == 60:
        return Interval.in_1_hour
    if datetime == 45:
        return Interval.in_45_minute
    if datetime == 30:
        return Interval.in_30_minute
    if datetime == 15:
        return Interval.in_15_minute
    elif datetime == 5:
        return Interval.in_5_minute
    elif datetime == 3:
        return Interval.in_3_minute
    elif datetime == 1:
        return Interval.in_1_minute
    else:
        return Interval.in_daily


def interval_to_string(interval):
    return str(interval).replace(".", "")


def str_to_interval(interval: str):
    if interval == str(Interval.in_1_minute):
        return Interval.in_1_minute
    elif interval == str(Interval.in_3_minute):
        return Interval.in_3_minute
    elif interval == str(Interval.in_5_minute):
        return Interval.in_5_minute
    elif interval == str(Interval.in_15_minute):
        return Interval.in_15_minute
    elif interval == str(Interval.in_30_minute):
        return Interval.in_30_minute
    elif interval == str(Interval.in_45_minute):
        return Interval.in_45_minute
    elif interval == str(Interval.in_1_hour):
        return Interval.in_1_hour
    elif interval == str(Interval.in_2_hour):
        return Interval.in_2_hour
    else:
        return None


def interval_to_int(interval: Interval):
    if interval == Interval.in_1_minute:
        return 1
    elif interval == Interval.in_3_minute:
        return 3
    elif interval == Interval.in_5_minute:
        return 5
    elif interval == Interval.in_15_minute:
        return 15
    elif interval == Interval.in_30_minute:
        return 30
    elif interval == Interval.in_45_minute:
        return 45
    elif interval == Interval.in_1_hour:
        return 60
    elif interval == Interval.in_2_hour:
        return 120
    elif interval == Interval.in_3_hour:
        return 180
    elif interval == Interval.in_4_hour:
        return 240
    elif interval == Interval.in_daily:
        return 1440
    elif interval == Interval.in_weekly:
        return 1440 * 7
    elif interval == Interval.in_monthly:
        return 1440 * 30
    else:
        return None


def int_to_interval(interval: int):
    if interval == 1:
        return Interval.in_1_minute
    elif interval == 3:
        return Interval.in_3_minute
    elif interval == 5:
        return Interval.in_5_minute
    elif interval == 15:
        return Interval.in_15_minute
    elif interval == 30:
        return Interval.in_30_minute
    elif interval == 45:
        return Interval.in_45_minute
    elif interval == 60:
        return Interval.in_1_hour
    elif interval == 120:
        return Interval.in_2_hour
    elif interval == 1440:
        return Interval.in_daily
    elif interval == 1440 * 7:
        return Interval.in_weekly
    elif interval == 1440 * 30:
        return Interval.in_monthly
    else:
        return None
