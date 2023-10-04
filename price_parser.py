import time
from datetime import datetime
from tvDatafeed import TvDatafeed, TvDatafeedLive, Interval
from tvDatafeed.seis import Seis
import json
import os
from pandas import DataFrame, read_csv

trade_pause_wait_time = 60 # 1 hour

currencies_path = "users/currencies.txt"
currencies_data_path = "currencies_data/"

currencies_requests_last_check_date = {}
tv = TvDatafeed()
tvl = TvDatafeedLive()


def create_save_currencies_files(currencies, intervals):
    for cur in currencies:
        for interval in intervals:
            path = currencies_data_path+cur[0]+str(interval).replace(".", "")+".csv"
            with open(path, "a", encoding="utf-8") as file:
                file.write(" ")


def save_currency_file(df: DataFrame, currency, interval: Interval):
    interval = str(interval).replace(".", "")
    df.to_csv(currencies_data_path + currency + interval + ".csv")


def update_last_check_date(currency, interval: Interval):
    interval = str(interval).replace(".", "")
    path = currencies_data_path + currency + interval + ".csv"
    if not os.path.exists(path):
        return False, None

    df = read_csv(path)
    current_check_date = df.datetime[0]
    currencies_requests_last_check_date.update({currency+interval: current_check_date})


def is_currency_file_changed(currency, interval: Interval):
    interval = str(interval).replace(".", "")
    path = currencies_data_path + currency + interval + ".csv"
    if not os.path.exists(path):
        return False, None

    last_check_date = currencies_requests_last_check_date.get(currency+interval)
    # print(path)
    df = read_csv(path)
    df["datetime"] = df.apply(lambda row: datetime.strptime(row["datetime"], '%Y-%m-%d %H:%M:%S'), axis=1)
    current_check_date = df.datetime[0]
    # print("currency", currency, "interval", interval, "current date:", current_check_date, "last date:", last_check_date)
    if current_check_date == last_check_date:
        return False, df

    currencies_requests_last_check_date.update({currency+interval: current_check_date})
    return True, df


def reset_currency_file(currency, interval):
    path = currencies_data_path + currency[0] + str(interval).replace(".", "") + ".csv"
    if os.path.exists(path):
        os.remove(path)


def read_currencies_file():
    with open(currencies_path, 'r', encoding="utf-8") as file:
        data = json.loads(file.read())

    return data


def get_currencies():
    currencies = []
    for currency in read_currencies_file():
        symbol = currency['symbol']
        exchange = currency['exchange']
        currencies.append((symbol, exchange))
    return currencies


def get_price_data_seis(seis, bars_count=500):
    priceData = seis.get_hist(n_bars=bars_count)
    priceData = priceData.drop(priceData.index[len(priceData) - 1])
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    return priceData


def get_price_data(symbol, exchange, interval, bars_count=500):
    try:
        priceData = tvl.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars_count)
        priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
        return priceData
    except Exception as e:
        print("cccc", e)


def update_currency_file_consumer(seis: Seis, data):
    try:
        # print("update:", seis.symbol, seis.interval, datetime.now())
        price_data = get_price_data_seis(seis)

        interval = seis.interval
        symbol = seis.symbol
        save_currency_file(price_data, symbol, interval)
    except Exception as e:
        print("bbb", e)


def create_parce_currencies_with_intervals_callbacks(currencies, intervals: [Interval]):
    while True:
        tvl = TvDatafeedLive()
        tv = TvDatafeed()
        try:
            for currency in currencies:
                for interval in intervals:
                    seis = tvl.new_seis(currency[0], currency[1], interval)
                    print("seis", seis)
                    consumer = tvl.new_consumer(seis, update_currency_file_consumer)
                    tvl.session
            break
        except ValueError as e:
            print("Error", e)
            time.sleep(trade_pause_wait_time)
            print("waited")


if __name__ == "__main__":
    print(tv.search_symbol("BTCUSD", "COINBASE"))
