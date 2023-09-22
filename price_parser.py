from tvDatafeed import TvDatafeed, Interval
import json
import os
from pandas import DataFrame, read_csv

currencies_path = "users/currencies.txt"
currencies_data_path = "currencies_data/"

currencies_requests_last_check_date = {}


def create_save_currencies_files(currencies, intervals):
    for cur in currencies:
        for interval in intervals:
            path = currencies_data_path+cur[0]+str(interval).replace(".", "")+".csv"
            with open(path, "a", encoding="utf-8") as file:
                file.write(" ")


def save_currency_file(df: DataFrame, currency, interval):
    # print("Save currency", currency)
    df.to_csv(currencies_data_path + currency + interval + ".csv")


def is_currency_file_changed(currency, interval):
    path = currencies_data_path + currency + interval + ".csv"
    if os.path.exists(path):
        last_check_date = currencies_requests_last_check_date.get(currency)
        df = read_csv(path)

        current_check_date = df.datetime[0]
        if not (current_check_date == last_check_date):
            currencies_requests_last_check_date.update({currency: current_check_date})
            return True, df
        return False, df
    return False, None


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


def get_price_data(symbol='EURUSD', exchange='OANDA', interval=Interval.in_5_minute, bars_count=500):
    tv = TvDatafeed()
    priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars_count)
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    return priceData
