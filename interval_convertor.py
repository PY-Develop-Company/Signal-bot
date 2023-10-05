from pandas import Timedelta
from tvDatafeed import Interval
import math
from datetime import timedelta


def timedelta_to_string(interval):
    delay_days = interval / Timedelta(days=1)
    delay_hours = interval / Timedelta(hours=1)
    delay_minutes = interval / Timedelta(minutes=1)
    if delay_days > 0:
        str(int(delay_days * 3)) + "Д"
    elif delay_hours > 0:
        return str(int(delay_hours * 3)) + "ч"
    return str(int(delay_minutes * 3)) + "мин"


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
    else:
        return timedelta(days=1)


def datetime_to_interval(datetime):
    datetime = math.floor(datetime.total_seconds() / 60)
    if datetime == 15:
        return Interval.in_15_minute
    elif datetime == 5:
        return Interval.in_5_minute
    elif datetime == 1:
        return Interval.in_1_minute
    else:
        return Interval.in_daily


def interval_to_string(interval):
    return str(interval).replace(".", "")
