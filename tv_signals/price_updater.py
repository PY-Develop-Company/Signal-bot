from tvDatafeed import TvDatafeedLive

from utils import time
from tv_signals.interval import Interval as MyInterval
from utils.interval_convertor import my_interval_to_tv_interval
from my_debuger import debug_error, debug_info

import json
import requests


class TVDatafeedPriceUpdater:
    def __init__(self):
        self.tvl = TvDatafeedLive()

    def download_price_data(self, symbol, exchange, interval: MyInterval, bars_count=5000):
        if self.tvl is None:
            debug_info("tvl recreation")
            self.tvl = TvDatafeedLive()
        try:
            debug_info(f"update price data {symbol, exchange, interval}")
            interval = my_interval_to_tv_interval(interval)
            return self.tvl.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars_count, timeout=180, extended_session=True)
        except Exception as e:
            debug_error(e, "Error get_price_data")
            return None


class FCSForexPriceUpdater:
    def __init__(self, token):
        self.base_url = "https://fcsapi.com/api-v3/forex/"
        self.token = token

    def download_price_data(self, symbols, period, level):
        res_url = f"{self.base_url}multi_url?"
        i = 0
        for symbol in symbols:
            i += 1
            res_url += f"url[{i}]={self.base_url}history?symbol={symbol}&period={period}&level={level}&"
        res_url += f"access_key={self.token}"

        res = requests.get(res_url)
        return res.text

    def show_all_currencies(self):
        res_url = f"{self.base_url}list?type=forex&access_key={self.token}"

        res = requests.get(res_url)
        return res.text

    def latest_price_and_date(self, symbol):
        res_url = f"{self.base_url}latest?symbol={symbol}&access_key={self.token}"

        res = requests.get(res_url)
        response = json.loads(res.text).get("response")[0]
        return float(response.get("c")), time.str_to_datetime(response.get("tm"))


class FCSCryptoPriceUpdater(FCSForexPriceUpdater):
    def __init__(self, token):
        super().__init__(token)
        self.base_url = "https://fcsapi.com/api-v3/crypto/"

    def download_price_data(self, symbols, period, level):
        i = 0
        res = ""
        for symbol in symbols:
            i += 1
            res_url = f"{self.base_url}history?symbol={symbol}&period={period}&level={level}&access_key={self.token}"

            res += ", " + requests.get(res_url).text
        return res

    def show_all_currencies(self):
        res_url = f"{self.base_url}list?type=crypto&access_key={self.token}"

        res = requests.get(res_url)
        return res.text
