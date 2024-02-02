from enum import Enum


class Interval(Enum):
    in_1_minute = "1m"
    in_5_minute = "5m"
    in_15_minute = "15m"
    in_30_minute = "30m"
    in_1_hour = "1h"
    in_2_hour = "2h"
    in_daily = "1d"
    in_weekly = "7d"
    in_monthly = "30d"
