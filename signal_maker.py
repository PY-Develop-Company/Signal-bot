import indicators_reader
import price_parser
from pandas import DataFrame
import time
from pandas import Timedelta
from datetime import timedelta
import signal_maker

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

buy_signal = "<b>Лонг</b>⬆️"
sell_signal = "<b>Шорт</b>⬇️"
neutral_signal = "Neutral"


def timedelta_to_string(interval):
    delay_days = interval / Timedelta(days=1)
    delay_hours = interval / Timedelta(hours=1)
    delay_minutes = interval / Timedelta(minutes=1)
    if delay_days > 0:
        str(int(delay_days)) + "D"
    elif delay_hours > 0:
        return str(int(delay_hours)) + "h"

    return str(int(delay_minutes)) + "m"


def get_open_position_signal_message(signal, symbol, interval, indicators=""):
    message = "🟢" + signal + "\n        " + symbol + " на " + timedelta_to_string(interval)
    return message


def get_close_position_signal_message(signal, symbol, interval):
    message = "🔴Закриваємо позицію: " + signal + "\n        " + symbol + " на " + timedelta_to_string(interval)
    return message


async def close_position(signal, symbol, interval: timedelta, bars_count=3):
    delay_minutes = interval / Timedelta(minutes=1)
    time.sleep(delay_minutes * bars_count * 60)
    return get_close_position_signal_message(signal, symbol, interval)



def check_signal(prices: DataFrame, successful_indicators_count=4):
    indicators_signals = [indicators_reader.volume(prices.open, prices.close),
                          indicators_reader.ultimate_moving_average(prices.close),
                          indicators_reader.nadaraya_watson_envelope(prices.close),
                          indicators_reader.scalp_pro(prices.close),
                          indicators_reader.super_order_block(prices, prices.open, prices.close, prices.high,
                                                              prices.low, prices.datetime[0] - prices.datetime[1])]

    signal_counts = {buy_signal: [0, []], sell_signal: [0, []]}
    print(prices.symbol[0], prices.datetime[0]-prices.datetime[1], indicators_signals)
    for signal in indicators_signals:
        if not signal[0] == neutral_signal:
            signal_counts.get(signal[0])[0] += 1
            signal_counts.get(signal[0])[1].append(", " + signal[1])

    main_signal = (neutral_signal, [0, []])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0]:
            main_signal = signal_count

    if main_signal[1][0] >= successful_indicators_count:
        return (True, main_signal[0])
    return False, neutral_signal


if __name__ == "__main__":
    print(check_signal(price_parser.get_price_data(), successful_indicators_count=2))
