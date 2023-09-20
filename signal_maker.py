import indicators_reader
import price_parser
from pandas import DataFrame
import time

import signal_maker

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

buy_signal = "Лонг"
sell_signal = "Шорт"
neutral_signal = "Neutral"


def get_signal_message(signal, symbol, interval, indicators=""):
    message = signal + " на " + symbol + " " + str(interval)
    if not indicators == "":
        message.join(indicators)

    return message


def close_position(interval):
    time.sleep()


def check_signal(prices: DataFrame, symbol, successful_indicators_count=4):
    indicators_signals = [indicators_reader.volume(prices.open, prices.close),
                          indicators_reader.ultimate_moving_average(prices.close),
                          indicators_reader.nadaraya_watson_envelope(prices.close),
                          indicators_reader.scalp_pro(prices.close),
                          indicators_reader.super_order_block(prices, prices.open, prices.close, prices.high,
                                                              prices.low, prices.datetime[0] - prices.datetime[1])]

    signal_counts = {buy_signal: [0, []], sell_signal: [0, []]}
    print(indicators_signals)
    for signal in indicators_signals:
        if not signal[0] == neutral_signal:
            signal_counts.get(signal[0])[0] += 1
            signal_counts.get(signal[0])[1].append(", " + signal[1])

    main_signal = (neutral_signal, [0, []])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0]:
            main_signal = signal_count

    if main_signal[1][0] >= successful_indicators_count:
        return (True, get_signal_message(main_signal[0], symbol, prices.datetime[0] - prices.datetime[1], main_signal[1][1]))

    return False, "None"


if __name__ == "__main__":
    print(check_signal(price_parser.get_price_data(), successful_indicators_count=2))
