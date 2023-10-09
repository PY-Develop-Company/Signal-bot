from pandas import Timedelta
from tvDatafeed import Interval
import math
from datetime import timedelta


def timedelta_to_close_string(interval, bars_count=3):
    delay_days = int(interval / Timedelta(days=1) * bars_count)
    delay_hours = int(interval / Timedelta(hours=1) * bars_count - delay_days*24)
    delay_minutes = int(interval / Timedelta(minutes=1) * bars_count - delay_days*24*60 - delay_hours*60)

    if delay_days > 0:
        str(delay_days) + "Д"
    elif delay_hours > 0:
        return str(delay_hours) + "ч" + str(delay_minutes) + "м"
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
    else:
        return None


def datetime_to_interval(datetime):
    datetime = math.floor(datetime.total_seconds() / 60)
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
    else:
        return None

