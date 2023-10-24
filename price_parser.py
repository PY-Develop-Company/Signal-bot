import time
from datetime import datetime, timedelta
from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
from tvDatafeed.seis import Seis
from pandas import DataFrame, read_csv
import file_manager
import interval_convertor

trade_pause_wait_time = 600

currencies_path = "users/currencies.txt"
currencies_data_path = "currencies_data/"
currency_check_ended = "currencies_data/check_ended/"

currencies_last_analize_date = {}
tv = TvDatafeed()
tvl = TvDatafeedLive()


class PriceData:
    def __init__(self, symbol: str, exchange: str, interval: Interval):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval

    def print(self):
        print("\t", self.symbol, self.interval)

    def save_chart_data(self, df: DataFrame):
        interval = str(self.interval).replace(".", "")
        df.to_csv(currencies_data_path + self.symbol + interval + ".csv")
        with open(f"{currency_check_ended}{self.symbol}{str(self.interval).replace('.', '')}.txt", "w") as file:
            pass

    def get_chart_data_if_exists(self):
        interval = str(self.interval).replace(".", "")
        path = currency_check_ended + self.symbol + interval + ".txt"
        if not file_manager.is_file_exists(path):
            print("1Error chart not exists")
            return None
        path = currencies_data_path + self.symbol + interval + ".csv"
        if not file_manager.is_file_exists(path):
            print("2Error chart not exists")
            return None

        try:
            df = read_csv(path)
        except Exception as e:
            print("3Error chart not exists", path, e)
            return None
        return df

    def get_chart_data_if_exists_if_can_analize(self):
        interval = str(self.interval).replace(".", "")
        df = self.get_chart_data_if_exists()

        last_check_date = currencies_last_analize_date.get(self.symbol + interval)
        if not(df is None):
            try:
                df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime"], '%Y-%m-%d %H:%M:%S'), axis=1)
            except Exception as e:
                print("Error date time is wrong formated", e, df.to_string())
                return None
            current_check_date = df.datetime[0]
            if current_check_date == last_check_date:
                return None
            currencies_last_analize_date.update({self.symbol + interval: current_check_date})
        return df

    def reset_chart_data(self):
        interval = str(self.interval).replace(".", "")

        df = self.get_price_data(500)
        if df is None:
            pass
        else:
            path = currency_check_ended + self.symbol + interval + ".txt"
            file_manager.delete_file_if_exists(path)
            path = currencies_data_path + self.symbol + interval + ".csv"
            file_manager.delete_file_if_exists(path)
            self.save_chart_data(df)

    def get_price_data(self, bars_count=500):
        try:
            priceData = tvl.get_hist(symbol=self.symbol, exchange=self.exchange, interval=self.interval, n_bars=bars_count+1)
            priceData = priceData.reindex(index=priceData.index[::-1]).iloc[1:].reset_index()
            return priceData
        except Exception as e:
            print("Error cant get price data", e)
            return None

    def is_analize_time(self, update_date: datetime, debug=False):
        minutes = interval_convertor.interval_to_datetime(self.interval) / timedelta(minutes=1)
        if debug:
            print("is_analize_time", (update_date.minute + 1), minutes, (update_date.minute + 1) % minutes)

        return (update_date.minute + 1) % minutes == 0


def get_currencies():
    currencies = []
    currencies_file_content = file_manager.read_file(currencies_path)
    for currency in currencies_file_content:
        symbol = currency['symbol']
        exchange = currency['exchange']
        currencies.append((symbol, exchange))
    return currencies


def get_price_data_frame_seis(seis, bars_count=500):
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
            print("update file", pd.symbol, pd.interval)
            pd.save_chart_data(price_df)
        except Exception as e:
            print("bbb", e)

    while True:
        print(f"creating new seis {datetime.now()}")
        consumers = []
        tvl = TvDatafeedLive()
        tv = TvDatafeed()
        try:
            for pd in pds:
                seis = tvl.new_seis(pd.symbol, pd.exchange, pd.interval)
                print("seis", seis)
                consumer = tvl.new_consumer(seis, update_currency_file_consumer)
                consumers.append(consumer)

            time.sleep(trade_pause_wait_time)
        except ValueError as e:
            print("Error1", e)
            time.sleep(trade_pause_wait_time)
        except Exception as e:
            print("Error3", e)
            time.sleep(trade_pause_wait_time)

        for consumer in consumers:
            print("try delete consumer")
            print("tvl", tvl)
            # try:
            print("delete consumer")
            tvl.del_consumer(consumer)
            # except Exception as e:
            #     print("Error2", e)
        print(f"created new seis {datetime.now()}")
