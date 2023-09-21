from tvDatafeed import TvDatafeedLive, TvDatafeed, Interval
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


def get_price_data_seis(seis):
    priceData = seis.get_hist(n_bars=1000)
    priceData = priceData.drop(priceData.index[len(priceData) - 1])
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    return priceData


def get_price_data(symbol='EURUSD', exchange='OANDA', interval=Interval.in_5_minute, bars_count=1000, username='t4331662@gmail.com', password='Pxp626AmH7_'):
    tv = TvDatafeed()
    # tv = TvDatafeed(username=username, password=password)
    priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=bars_count)
    # seis = tv.new_seis(symbol, exchange, interval)
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    return priceData


if __name__ == '__main__':
    username = 't4331662@gmail.com'
    password = 'Pxp626AmH7_'

    tv = TvDatafeedLive()

    def consumer_func1(seis, data):
        print(
            "Open price for " + seis.symbol + " on " + seis.exchange + " exchange with " + seis.interval.name + " interval was " + str(
                data.open[0]))

        print(data.to_string())
        full_data = seis.get_hist(n_bars=100)
        full_data = full_data.drop(full_data.index[len(full_data)-1])

        print(full_data.to_string())

    seis = tv.new_seis("AUDCAD", "OANDA", Interval.in_1_minute)
    consumer1 = tv.new_consumer(seis, consumer_func1)
    cur = get_currencies()[0]