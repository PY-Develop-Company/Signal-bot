from tvDatafeed import TvDatafeed, Interval
import json
import indicators_reader

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

    cur = get_currencies()[0]
    df = get_price_data(symbol="AUDCAD", exchange="OANDA", interval=Interval.in_5_minute, bars_count=100)
    print(indicators_reader.scalp_pro(df, df.close))