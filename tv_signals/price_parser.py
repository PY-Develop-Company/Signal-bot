from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
from tvDatafeed.seis import Seis
from pandas import DataFrame, read_csv
import pytz

from datetime import datetime, timedelta

from utils import file_manager, interval_convertor

trade_pause_wait_time = 600

currencies_path = "./users/currencies.txt"
currencies_data_path = "./currencies_data/"
currency_check_ended = "currencies_data/check_ended/"

currencies_last_analize_date = {}
tv = TvDatafeed()
tvl = TvDatafeedLive()

currencies_puncts = {
    "EURUSD": 0.00001,
    "AUDUSD": 0.00001,
    "AUDCAD": 0.00001,
    "EURJPY": 0.001,
    "EURCAD": 0.00001,
    "AUDCHF": 0.00001,
    "GBPUSD": 0.00001,
    "AUDJPY": 0.001,
    "GBPAUD": 0.00001,
    "BTCUSD": 0.01
}


class PriceData:
    def __init__(self, symbol: str, exchange: str, interval: Interval):
        self.symbol = symbol
        self.exchange = exchange
        self.interval = interval

    def print(self):
        print("\t", self.symbol, self.interval)

    def get_real_puncts(self, puncts):
        return currencies_puncts[self.symbol] * puncts

    def save_chart_data(self, df: DataFrame):
        interval = str(self.interval).replace(".", "")
        df.to_csv(currencies_data_path + self.symbol + interval + ".csv")
        with open(f"{currency_check_ended}{self.symbol}{str(self.interval).replace('.', '')}.txt", "w") as file:
            time = datetime.now(pytz.timezone("Europe/Bucharest"))
            file.write(str(time))

    def get_chart_download_time(self):
        try:
            with open(f"{currency_check_ended}{self.symbol}{str(self.interval).replace('.', '')}.txt", "r") as file:
                res = datetime.strptime(file.read().split(".")[0], '%Y-%m-%d %H:%M:%S')
        except Exception as e:
            return datetime.strptime(str(datetime.now(pytz.timezone("Europe/Bucharest"))).split(".")[0], '%Y-%m-%d %H:%M:%S')
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
            print("3Error chart not exists", path, e)
            return None
        try:
            df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime"], '%Y-%m-%d %H:%M:%S'), axis=1)
        except Exception as e:
            print("Error date time is wrong formated", e, df.to_string())
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

        df = self.get_price_data(1000)
        if df is None:
            print("ERROR: No df")
        else:
            try:
                print("updated pd")
                path = currency_check_ended + self.symbol + interval + ".txt"
                file_manager.delete_file_if_exists(path)
                path = currencies_data_path + self.symbol + interval + ".csv"
                file_manager.delete_file_if_exists(path)
                self.save_chart_data(df)
            except:
                pass
    def remove_chart_data(self):
        interval = str(self.interval).replace(".", "")

        path = currency_check_ended + self.symbol + interval + ".txt"
        file_manager.delete_file_if_exists(path)
        path = currencies_data_path + self.symbol + interval + ".csv"
        file_manager.delete_file_if_exists(path)

    def get_price_data(self, bars_count=1000):
        try:
            priceData = tvl.get_hist(symbol=self.symbol, exchange=self.exchange, interval=self.interval, n_bars=bars_count+1)
            priceData = priceData.reindex(index=priceData.index[::-1]).iloc[1:].reset_index()
            return priceData
        except Exception as e:
            print("Error cant get price data", e)
            return None

    def is_analize_time(self, update_date: datetime, debug=False):
        minutes = interval_convertor.interval_to_int(self.interval)
        if debug:
            print("is_analize_time", (update_date.minute + 1), minutes, (update_date.minute + 1) % minutes)

        return (update_date.minute + 1) % minutes == 0

    def get_needed_chart_bar_to_analize(self, chart_bar: datetime, main_signal_interval):
        minutes = interval_convertor.interval_to_int(self.interval)
        main_minutes = interval_convertor.interval_to_int(main_signal_interval)

        tmp = chart_bar + timedelta(minutes=main_minutes)
        # print("needed bar check", main_signal_interval, minutes, chart_bar, main_minutes, "\n",
        #       tmp, timedelta(minutes=(tmp.hour*60 + tmp.minute) % minutes), timedelta(minutes=minutes), "\n",
        #       tmp - timedelta(minutes=(tmp.hour*60 + tmp.minute) % minutes) - timedelta(minutes=minutes))

        chart_bar = chart_bar + timedelta(minutes=main_minutes)
        res = chart_bar - timedelta(minutes=(chart_bar.hour*60 + chart_bar.minute) % minutes) - timedelta(minutes=minutes)

        return res


def get_currencies():
    currencies = []
    currencies_file_content = file_manager.read_file(currencies_path)
    for currency in currencies_file_content:
        symbol = currency['symbol']
        exchange = currency['exchange']
        currencies.append((symbol, exchange))
    return currencies


def get_price_data_frame_seis(seis, bars_count=1000):
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

    print(f"creating new seis {datetime.now()}")

    try:
        tvl.del_tvdatafeed()
    except Exception as e:
        print("Error tvl", e)
    tvl = TvDatafeedLive()
    tv = TvDatafeed()
    try:
        for pd in pds:
            seis = tvl.new_seis(pd.symbol, pd.exchange, pd.interval)
            print("seis", seis)
            consumer = tvl.new_consumer(seis, update_currency_file_consumer)
    except ValueError as e:
        print("Error1", e)
    except Exception as e:
        print("Error3", e)

    print(f"created new seis {datetime.now()}")
