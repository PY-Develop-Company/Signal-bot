import parse
from pandas import DataFrame
import time
from tvDatafeed import TvDatafeed, Interval

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'
symbol = 'NIFTY'
exchange = 'NSE'

buy_signal = "Лонг"
sell_signal = "Шорт"
neutral_signal = "Neutral"


def get_signal_message(signal, symbol, interval):
    return signal + " на " + symbol + " " + str(interval)


def close_position(interval):
    time.sleep()


def check_signal(price_data: DataFrame, successful_indicators_count=4):
    indicators_signals = [parse.volume(price_data.open, price_data.close),
                          parse.ultimate_moving_average(price_data.close),
                          parse.nadaraya_watson_envelope(price_data.close),
                          parse.scalp_pro(price_data.close)]

    signal_counts = [(indicators_signals.count(buy_signal), buy_signal),
                     (indicators_signals.count(sell_signal), sell_signal)]

    main_signal = max(signal_counts)
    if main_signal[0] >= successful_indicators_count:
        return (True, get_signal_message(main_signal[1], symbol, price_data.datetime[0]-price_data.datetime[1]))

    return False, "None"


if __name__ == "__main__":
    print(check_signal(parse.get_price_data(), successful_indicators_count=2))
