import parse
from pandas import DataFrame
from tvDatafeed import TvDatafeed, Interval

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'
symbol = 'NIFTY'
exchange = 'NSE'

buy_signal = "Buy"
sell_signal = "Sell"
neutral_signal = "Neutral"


def check_signal(price_data: DataFrame, successful_indicators_count=4):
    indicators_signals = [parse.volume(price_data.open, price_data.close),
                          parse.ultimate_moving_average(price_data.close),
                          parse.nadaraya_watson_envelope(price_data.close),
                          parse.scalp_pro(price_data.close)]

    signal_counts = [(indicators_signals.count(buy_signal), buy_signal),
                     (indicators_signals.count(sell_signal), sell_signal)]

    main_signal = max(signal_counts)
    if main_signal[0] >= successful_indicators_count:
        return main_signal[1], main_signal[0]

    return neutral_signal, 0


if __name__ == "__main__":
    print(check_signal(parse.get_price_data(), successful_indicators_count=2))
