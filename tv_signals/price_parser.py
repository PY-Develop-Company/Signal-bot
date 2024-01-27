import time
from datetime import datetime, timedelta

from utils import interval_convertor
from utils.time import now_time

from tvDatafeed import TvDatafeedLive, Interval, Seis
from pandas import DataFrame, read_sql_query

import sqlite3
from db_modul import db_connection

from my_debuger import debug_error, debug_info
from utils.interval_convertor import interval_to_string

trade_pause_wait_time = 600

currencies_table_name = "currencies"

currencies_last_analize_date = {}
tvl = TvDatafeedLive()


class PriceData:
    def __init__(self, symbol: str, exchange: str, interval: Interval):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        self.table_name = f"chart_data_{symbol}_{exchange}_{interval_to_string(interval)}"

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
                     f"(datetime TEXT UNIQUE PRIMARY KEY, symbol TEXT, open REAL, high REAL, low REAL, close REAL, "
                     f"volume REAL, download_time TEXT)")
        cursor.execute(sql_query)
        db_connection.commit()

    def print(self):
        debug_info(f"\t {self.symbol} seis {self.interval}")

    def get_real_puncts(self, pucts):
        return self.puncts * pucts

    def save_chart_data(self, data: DataFrame):
        while True:
            try:
                cursor = db_connection.cursor()

                data["download_time"] = str(now_time())

                data_strs = []
                for row in data.iterrows():
                    data_strs.append(f'("{row[0]}", "{str(row[1]["symbol"])}", {str(row[1]["open"])}, {str(row[1]["high"])}, '
                                     f'{str(row[1]["low"])}, {str(row[1]["close"])}, {str(row[1]["volume"])}, "{str(row[1]["download_time"])}")')

                joined_data_str = ",".join(data_strs)

                query = f'''
                        INSERT OR IGNORE INTO {self.table_name} (
                            datetime, symbol, open, high, low, close, volume, download_time
                        ) VALUES {joined_data_str};
                    '''
                cursor.execute(query)
                db_connection.commit()
                break
            except sqlite3.OperationalError:
                time.sleep(1)
                print("continue loop")
                continue

    def get_chart_download_time(self):
        df = read_sql_query(f"SELECT * FROM {self.table_name} LIMIT 1", db_connection)
        try:
            df["datetime"] = df.apply(lambda row: datetime.strptime(row["download_time"], '%Y-%m-%d %H:%M:%S'), axis=1)
        except Exception as e:
            return now_time()
        return df["datetime"][0]

    def get_chart_data(self, bars_count=5000):
        df = read_sql_query(f"SELECT * FROM {self.table_name} order by datetime desc limit {bars_count};", db_connection)
        df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime"], '%Y-%m-%d %H:%M:%S'), axis=1)
        return df

    def get_chart_data_if_can_analize(self):
        interval = str(self.interval).replace(".", "")
        df = self.get_chart_data()

        last_check_date = currencies_last_analize_date.get(self.symbol + interval)
        if not(df is None):
            current_check_date = df.datetime[0]
            if current_check_date == last_check_date:
                return None
            currencies_last_analize_date.update({self.symbol + interval: current_check_date})
        return df

    def reset_chart_data(self):
        df = self.get_price_data(5000)
        self.save_chart_data(df.tail(-1).copy())

    def get_price_data(self, bars_count=5000):
        global tvl
        if tvl is None:
            debug_info("tvl recreation")
            tvl = TvDatafeedLive()
        try:
            debug_info(f"update price data {self.symbol, self.exchange, self.interval}")
            return tvl.get_hist(symbol=self.symbol, exchange=self.exchange, interval=self.interval, n_bars=bars_count, timeout=180, extended_session=True)
        except Exception as e:
            debug_error(e, "Error get_price_data")
            return None

    def get_needed_chart_bar_to_analize(self, chart_bar: datetime, main_signal_interval):
        minutes = interval_convertor.interval_to_int(self.interval)
        main_minutes = interval_convertor.interval_to_int(main_signal_interval)

        tmp = chart_bar + timedelta(minutes=main_minutes)

        chart_bar = chart_bar + timedelta(minutes=main_minutes)
        res = chart_bar - timedelta(minutes=(chart_bar.hour * 60 + chart_bar.minute) % minutes) - timedelta(
            minutes=minutes)

        return res


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


def update_prices(pds, bars_count=5000):
    result = True
    for pd in pds:
        data = pd.get_price_data(bars_count)
        if data is None:
            result = False
            debug_error(Exception("data is None"))
            continue
        if data is bool:
            debug_error(Exception(f"data is bool {data}"))
            continue
        pd.save_chart_data(data.tail(-1).copy())

    return result


def create_consumers(pds: [PriceData]):
    for pd in pds:
        try:
            print("update seis", pd.symbol, pd.exchange, pd.interval)
            seis: Seis = tvl.new_seis(pd.symbol, pd.exchange, pd.interval)
            seis.new_consumer(update_price_consumer)
            time.sleep(1)
        except Exception as e:
            print("update seis", pd.symbol, pd.exchange, pd.interval, e)


def update_price_consumer(seis: Seis, data):
    pd = PriceData(seis.symbol, seis.exchange, seis.interval)
    pd.print()
    df = seis.get_hist(5000)
    pd.save_chart_data(df)
