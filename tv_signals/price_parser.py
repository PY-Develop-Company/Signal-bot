import time
import json
from datetime import datetime, timedelta

from utils import interval_convertor
from utils.time import now_time

from tv_signals.interval import Interval
from pandas import DataFrame, read_sql_query

import sqlite3
from db_modul import db_connection
from tv_signals.price_updater import TVDatafeedPriceUpdater, FCSForexPriceUpdater

from my_debuger import debug_error, debug_info
from utils.interval_convertor import my_interval_to_string

trade_pause_wait_time = 600

currencies_table_name = "currencies"

price_updater = TVDatafeedPriceUpdater()


class PriceData:
    def __init__(self, symbol: str, exchange: str, interval: Interval):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        self.table_name = f"chart_data_{symbol.replace('/', '_')}_{exchange}_{interval.value}"

        self.create_table()

        cursor = db_connection.cursor()

        sql_query = f"""SELECT puncts FROM {currencies_table_name}
                        WHERE symbol = "{self.symbol}" AND exchange = "{self.exchange}";"""
        cursor.execute(sql_query)
        puncts = cursor.fetchone()
        self.puncts = puncts[0]

    def create_table(self):
        cursor = db_connection.cursor()
        sql_query = (f"CREATE TABLE IF NOT EXISTS {self.table_name} "
                     f"(datetime INT UNIQUE PRIMARY KEY, symbol TEXT, open REAL, high REAL, low REAL, close REAL, "
                     f"volume REAL, datetime_str TEXT, download_time TEXT)")
        cursor.execute(sql_query)
        db_connection.commit()

    def print(self):
        debug_info(f"\t {self.symbol} {self.interval}")

    def get_real_puncts(self, pucts):
        return self.puncts * pucts

    def save_chart_data(self, data: DataFrame):
        # while True:
        # try:
        download_time = now_time()
        cursor = db_connection.cursor()

        data_strs = []
        for key in data.keys():
            pd_timestamp_data = data.get(key)
            volume_str = pd_timestamp_data.get("v")
            volume_str = pd_timestamp_data.get("v")
            high = float(pd_timestamp_data.get("h"))
            low = float(pd_timestamp_data.get("l"))
            interval_mult = interval_convertor.my_interval_to_int(self.interval)
            v = (high - low)/self.get_real_puncts(1) * interval_mult
            if interval_mult >= 60:
                v *= 0.5
            volume = float(volume_str) if volume_str.isnumeric() else round(v)
            data_strs.append(f'({pd_timestamp_data.get("t")}, "{self.symbol}", {pd_timestamp_data.get("o")}, {high}, '
                             f'{low}, {pd_timestamp_data.get("c")}, {volume}, "{pd_timestamp_data.get("tm")}", "{download_time}")')

        joined_data_str = ",".join(data_strs)

        query = f'''
                INSERT OR IGNORE INTO {self.table_name} (
                    datetime, symbol, open, high, low, close, volume, datetime_str, download_time
                ) VALUES {joined_data_str};
            '''
        cursor.execute(query)
        db_connection.commit()
        print(f"saved {self.symbol} {self.interval}")
            # break
        # except sqlite3.OperationalError:
        #     time.sleep(1)
        #     print("continue loop")
        #     continue

    def get_saved_chart_data(self, bars_count=5000):
        df = read_sql_query(f"SELECT * FROM {self.table_name} order by datetime desc limit {bars_count};", db_connection)
        df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime_str"], '%Y-%m-%d %H:%M:%S'), axis=1)
        return df

    def download_price_data(self, bars_count=5000):
        return price_updater.download_price_data(self.symbol, self.exchange, self.interval, bars_count)


def get_currencies():
    currencies = []

    try:
        sql_query = f"""SELECT * FROM {currencies_table_name};"""
        df = read_sql_query(sql_query, db_connection)

        for currency in df.index:
            if df["is_in_use"][currency] == 1:
                symbol = df['symbol'][currency]
                exchange = df['exchange'][currency]
                currencies.append((symbol, exchange))
    except sqlite3.Error as e:
        debug_error(e, "Error get_currencies")

    return currencies


def update_prices(symbols: [str], exchanges: [str], periods: [str], price_updater: FCSForexPriceUpdater):
    result = True
    my_dict = {}
    for period in periods:
        res = price_updater.download_price_data(symbols, period, 1)
        res = json.loads(res)
        for key in res.keys():
            data = res.get(key)
            s = data.get("info").get("symbol")
            p = data.get("info").get("period")
            d = data.get("response")
            my_dict.update({f"{s}_{p}": d})

    for i, symbol in enumerate(symbols):
        for period in periods:
            pd = PriceData(symbol, exchanges[i], interval_convertor.str_to_my_interval(period))
            pd.save_chart_data(my_dict.get(f"{symbol}_{period}"))

    return result

