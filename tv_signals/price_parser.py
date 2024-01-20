from datetime import datetime, timedelta

from utils import file_manager, interval_convertor
from utils.time import now_time

from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
from tvDatafeed.seis import Seis
from pandas import DataFrame, read_csv, read_sql_query

import sqlite3
from db_modul import db_connection

from my_debuger import debug_error, debug_info, debug_tv_data_feed

trade_pause_wait_time = 600

currencies_table_name = "currencies"

currencies_data_path = "./currencies_data/"
currency_check_ended = "./currencies_data/check_ended/"

currencies_last_analize_date = {}
tv = TvDatafeed()
tvl = TvDatafeedLive()

timeout_secs = 60


class PriceData:
    def __init__(self, symbol: str, exchange: str, interval: Interval):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval
        try:
            cursor = db_connection.cursor()
            sql_query = f"""SELECT puncts FROM {currencies_table_name}
                            WHERE symbol = "{self.symbol}" AND exchange = "{self.exchange}";"""
            cursor.execute(sql_query)
            puncts = cursor.fetchone()
            self.puncts = puncts[0]
        except sqlite3.Error as e:
            debug_error(str(e), f"Error PriceData creation")
            self.puncts = None

    def print(self):
        debug_info(f"\t {self.symbol} seis {self.interval}")

    def get_real_puncts(self, pucts):
        return self.puncts * pucts

    def save_chart_data(self, df: DataFrame):
        interval = str(self.interval).replace(".", "")
        df.to_csv(currencies_data_path + self.symbol + interval + ".csv")
        with open(f"{currency_check_ended}{self.symbol}{str(self.interval).replace('.', '')}.txt", "w") as file:
            file.write(str(now_time()))

    def get_chart_download_time(self):
        try:
            with open(f"{currency_check_ended}{self.symbol}{str(self.interval).replace('.', '')}.txt", "r") as file:
                res = datetime.strptime(file.read(), '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return now_time()
        return res

    def get_chart_data_if_exists(self):
        interval = str(self.interval).replace(".", "")
        path = currency_check_ended + self.symbol + interval + ".txt"
        if not file_manager.is_file_exists(path):
            # print("1Error chart not exists")
            return None
        path = currencies_data_path + self.symbol + interval + ".csv"
        if not file_manager.is_file_exists(path):
            # print("2Error chart not exists")
            return None

        try:
            df = read_csv(path)
        except Exception as e:
            debug_error(str(e), f"Error get_chart_data_if_exists with path ({path})")
            return None
        try:
            df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime"], '%Y-%m-%d %H:%M:%S'), axis=1)
        except Exception as e:
            debug_error(str(e) + " " + str(df.to_string()), f"Error get_chart_data_if_exists date time is wrong formatted")
            return None
        return df

    def get_chart_data_if_exists_if_can_analize(self):
        interval = str(self.interval).replace(".", "")
        df = self.get_chart_data_if_exists()

        last_check_date = currencies_last_analize_date.get(self.symbol + interval)
        if not(df is None):
            current_check_date = df.datetime[0]
            if current_check_date == last_check_date:
                return None
            currencies_last_analize_date.update({self.symbol + interval: current_check_date})
        return df

    def reset_chart_data(self):
        interval = str(self.interval).replace(".", "")

        df = self.get_price_data(5000)
        if df is None:
            pass
        else:
            path = currency_check_ended + self.symbol + interval + ".txt"
            file_manager.delete_file_if_exists(path)
            path = currencies_data_path + self.symbol + interval + ".csv"
            file_manager.delete_file_if_exists(path)
            self.save_chart_data(df)

    def remove_chart_data(self):
        interval = str(self.interval).replace(".", "")

        path = currency_check_ended + self.symbol + interval + ".txt"
        file_manager.delete_file_if_exists(path)
        path = currencies_data_path + self.symbol + interval + ".csv"
        file_manager.delete_file_if_exists(path)

    def get_price_data(self, bars_count=5000):
        try:
            priceData = tvl.get_hist(symbol=self.symbol, exchange=self.exchange, interval=self.interval, n_bars=bars_count+1)
            priceData = priceData.reindex(index=priceData.index[::-1]).iloc[1:].reset_index()
            return priceData
        except Exception as e:
            debug_error(str(e), "Error cant get price data")
            return None

    def is_analize_time(self, update_date: datetime, debug=False):
        minutes = interval_convertor.interval_to_int(self.interval)

        return (update_date.minute + 1) % minutes == 0

    def get_needed_chart_bar_to_analize(self, chart_bar: datetime, main_signal_interval):
        minutes = interval_convertor.interval_to_int(self.interval)
        main_minutes = interval_convertor.interval_to_int(main_signal_interval)

        tmp = chart_bar + timedelta(minutes=main_minutes)
        # print("needed bar check", main_signal_interval, minutes, chart_bar, main_minutes, "\n",
        #       tmp, timedelta(minutes=(tmp.hour*60 + tmp.minute) % minutes), timedelta(minutes=minutes), "\n",
        #       tmp - timedelta(minutes=(tmp.hour*60 + tmp.minute) % minutes) - timedelta(minutes=minutes))

        chart_bar = chart_bar + timedelta(minutes=main_minutes)
        res = chart_bar - timedelta(minutes=(chart_bar.hour * 60 + chart_bar.minute) % minutes) - timedelta(
            minutes=minutes)

        return res


def get_currencies():
    currencies = []
    # currencies_file_content = file_manager.read_file(currencies_path)

    try:
        sql_query = f"""SELECT * FROM {currencies_table_name};"""
        df = read_sql_query(sql_query, db_connection)

        for currency in df.index:
            if df["is_in_use"][currency] == 1:
                symbol = df['symbol'][currency]
                exchange = df['exchange'][currency]
                currencies.append((symbol, exchange))
    except sqlite3.Error as e:
        debug_error(str(e), "Error get_currencies")

    return currencies


def get_price_data_frame_seis(seis, bars_count=5000):
    price_df = seis.get_hist(n_bars=bars_count)
    price_df = price_df.drop(price_df.index[len(price_df) - 1])
    price_df = price_df.reindex(index=price_df.index[::-1]).reset_index()
    return price_df


def create_parce_currencies_with_intervals_callbacks(pds: [PriceData]):
    global tvl, tv

    def update_currency_file_consumer(seis: Seis, data):
        try:
            price_df = get_price_data_frame_seis(seis)

            pd = PriceData(seis.symbol, seis.exchange, seis.interval)
            # debug_tv_data_feed("update file" + pd.symbol + str(pd.interval))
            pd.save_chart_data(price_df)
        except Exception as e:
            debug_error(str(e), "Error update_currency_file_consumer")

    debug_tv_data_feed(f"creating new seis")

    try:
        tvl.del_tvdatafeed()
        tvl = TvDatafeedLive()
        tv = TvDatafeed()
    except Exception as e:
        debug_error(str(e), "Error tvl.del_tvdatafeed()")

    try:
        for pd in pds:
            seis = tvl.new_seis(pd.symbol, pd.exchange, pd.interval, timeout=timeout_secs)
            # debug_tv_data_feed("seis" + str(seis))
            consumer = tvl.new_consumer(seis, update_currency_file_consumer, timeout=timeout_secs)
    except ValueError as e:
        debug_error(str(e), "ValueError creating seis")
    except Exception as e:
        debug_error(str(e), "Error creating seis")

    debug_tv_data_feed(f"created new seis")
