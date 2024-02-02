from datetime import timedelta

from my_debuger import debug_error
from tvDatafeed import Interval as TVInterval
from tv_signals.interval import Interval as MyInterval

my_interval_to_tv_interval_dict = {
    MyInterval.in_1_minute: TVInterval.in_1_minute,
    MyInterval.in_5_minute: TVInterval.in_5_minute,
    MyInterval.in_15_minute: TVInterval.in_15_minute,
    MyInterval.in_30_minute: TVInterval.in_30_minute,
    MyInterval.in_1_hour: TVInterval.in_1_hour,
    MyInterval.in_2_hour: TVInterval.in_2_hour,
    MyInterval.in_daily: TVInterval.in_daily,
    MyInterval.in_weekly: TVInterval.in_weekly,
    MyInterval.in_monthly: TVInterval.in_monthly
}
my_interval_to_datetime_dict = {
    MyInterval.in_1_minute: timedelta(minutes=1),
    MyInterval.in_5_minute: timedelta(minutes=5),
    MyInterval.in_15_minute: timedelta(minutes=15),
    MyInterval.in_30_minute: timedelta(minutes=30),
    MyInterval.in_1_hour: timedelta(hours=1),
    MyInterval.in_2_hour: timedelta(hours=2),
    MyInterval.in_daily: timedelta(days=1),
    MyInterval.in_weekly: timedelta(days=7),
    MyInterval.in_monthly: timedelta(days=30)
}
my_interval_to_int_dict = {
    MyInterval.in_1_minute: 1,
    MyInterval.in_5_minute: 5,
    MyInterval.in_15_minute: 15,
    MyInterval.in_30_minute: 30,
    MyInterval.in_1_hour: 60,
    MyInterval.in_2_hour: 120,
    MyInterval.in_daily: 1440,
    MyInterval.in_weekly: 1440*7,
    MyInterval.in_monthly: 1440*30
}


def my_interval_to_tv_interval(my_interval: MyInterval):
    if my_interval in my_interval_to_tv_interval_dict.keys():
        return my_interval_to_tv_interval_dict.get(my_interval)
    else:
        debug_error(Exception(), "my_interval_to_tv_interval error")
        return None


def my_interval_to_datetime(my_interval: MyInterval):
    if my_interval in my_interval_to_datetime_dict.keys():
        return my_interval_to_datetime_dict.get(my_interval)
    else:
        debug_error(Exception(), "my_interval_to_datetime error")
        return None


def my_interval_to_string(interval: MyInterval):
    return str(interval)


def str_to_my_interval(interval: str):
    if interval == MyInterval.in_1_minute.value:
        return MyInterval.in_1_minute
    elif interval == MyInterval.in_5_minute.value:
        return MyInterval.in_5_minute
    elif interval == MyInterval.in_15_minute.value:
        return MyInterval.in_15_minute
    elif interval == MyInterval.in_30_minute.value:
        return MyInterval.in_30_minute
    elif interval == MyInterval.in_1_hour.value:
        return MyInterval.in_1_hour
    elif interval == MyInterval.in_2_hour.value:
        return MyInterval.in_2_hour
    elif interval == MyInterval.in_daily.value:
        return MyInterval.in_daily
    elif interval == MyInterval.in_weekly.value:
        return MyInterval.in_weekly
    elif interval == MyInterval.in_monthly.value:
        return MyInterval.in_monthly
    else:
        return None


def my_interval_to_int(my_interval: MyInterval):
    if my_interval in my_interval_to_int_dict.keys():
        return my_interval_to_int_dict.get(my_interval)
    else:
        debug_error(Exception(), "my_interval_to_int error")
        return None
