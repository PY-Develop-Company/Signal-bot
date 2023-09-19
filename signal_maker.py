import parse
from tvDatafeed import TvDatafeed, Interval

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'
symbol = 'NIFTY'
exchange = 'NSE'

buy_signal = "Buy"
sell_signal = "Sell"
neutral_signal = "Neutral"

def check_signal(successful_indicators_count=2, interval=Interval.in_5_minute):
    tv = TvDatafeed()
    priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=1000)
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()

    indicators_signals = []
    indicators_signals.append(parse.volume(priceData.open, priceData.close))
    indicators_signals.append(parse.ultimate_moving_average(priceData.close))
    indicators_signals.append(parse.nadaraya_watson_envelope(priceData.close))
    indicators_signals.append(parse.scalp_pro(priceData.close))

    signal_counts = []
    signal_counts.append((indicators_signals.count(buy_signal), buy_signal))
    signal_counts.append((indicators_signals.count(sell_signal), sell_signal))

    main_signal = max(signal_counts)

    if main_signal[0] >= successful_indicators_count:
        return main_signal[1], main_signal[0]

    return neutral_signal, 0

if __name__ == "__main__":
    print(check_signal())

