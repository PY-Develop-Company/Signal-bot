from tvDatafeed import TvDatafeed, Interval
import json

import signal_maker

currencies_path = "users/currencies.txt"


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


def get_price_data(symbol='EURUSD', exchange='OANDA', interval=Interval.in_5_minute, bars_count=1000, username='t4331662@gmail.com', password='Pxp626AmH7_'):
    tv = TvDatafeed()
    # tv = TvDatafeed(username=username, password=password)
    priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars_count)
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    return priceData


if __name__ == '__main__':
    username = 't4331662@gmail.com'
    password = 'Pxp626AmH7_'

    tv = TvDatafeed()
    # tv = TvDatafeed(username=username, password=password)
    for currency in get_currencies():
        data = get_price_data(symbol=currency[0], exchange=currency[1])

        symbol = data.symbol[0].split(":")[1]
        print(signal_maker.check_signal(data, symbol, successful_indicators_count=2))
        print(data.sample())