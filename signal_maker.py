import indicators_reader
from pandas import DataFrame
import time
from pandas import Timedelta
from datetime import timedelta, datetime
import price_parser
import indicators_reader

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

buy_signal_smile = "🟢 "
sell_signal_smile = "🔴 "
buy_signal = "LONG ⬆"
sell_signal = "SHORT ⬇"
neutral_signal = "Нет сигнала"
profit_message = " ✅ "
loss_message = " ❌ "

def get_smile(signal):
    return buy_signal_smile if signal == buy_signal else (sell_signal_smile if signal == sell_signal else "")


def timedelta_to_string(interval):
    delay_days = interval / Timedelta(days=1)
    delay_hours = interval / Timedelta(hours=1)
    delay_minutes = interval / Timedelta(minutes=1)
    if delay_days > 0:
        str(int(delay_days)) + "Д"
    elif delay_hours > 0:
        return str(int(delay_hours)) + "ч"
    return str(int(delay_minutes*3)) + "мин"


def get_open_position_signal_message(signal, symbol, interval, indicators=""):
    message = get_smile(signal) + symbol + " " + signal + " " + timedelta_to_string(interval)
    return message


def get_close_position_signal_message(open, close, signal, symbol, interval):
    profit_percent = 100 - 100*close/open

    # print("closing:", "profit", profit_percent, "close", close, "open", open)
    # print()

    text = (profit_message if close >= open else loss_message) if (signal == buy_signal) else (profit_message if (close <= open) else loss_message)
    print(text)
    message = get_smile(signal) + "Сделка в " + text + symbol + " " + signal + " " + timedelta_to_string(interval)
    return message


async def close_position(position_open_price, signal, symbol, interval: timedelta, bars_count=3, exchange="OANDA"):
    delay_minutes = interval / Timedelta(minutes=1)
    time.sleep(delay_minutes * bars_count * 60)
    print("symbol, interval:", symbol, interval)
    interval = indicators_reader.get_interval(interval)
    price_data = price_parser.get_price_data(symbol.replace("/", ""), exchange, interval, bars_count=10)
    # has_signal, price_data = price_parser.is_currency_file_changed(symbol.replace("/", ""),
    #                                                    indicators_reader.get_interval_string(interval).replace(".", ""))
    return get_close_position_signal_message(position_open_price, price_data.close[0], signal, symbol, price_data.datetime[0]-price_data.datetime[1])


def check_signal(prices: DataFrame, interval: timedelta, successful_indicators_count=4):
    indicators_signals = [indicators_reader.super_order_block(prices, prices.open, prices.close, prices.high,
                                                              prices.low, interval),
                          indicators_reader.volume(prices.open, prices.close),
                          indicators_reader.ultimate_moving_average(prices.close),
                          indicators_reader.nadaraya_watson_envelope(prices.close),
                          indicators_reader.scalp_pro(prices, prices.close)]

    signal_counts = {buy_signal: [0, []], sell_signal: [0, []], neutral_signal:[0, []]}
    for signal in indicators_signals:
        signal_counts.get(signal[0])[0] += 1
        signal_counts.get(signal[0])[1].append(", " + signal[1])

    main_signal = (neutral_signal, [0, []])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0]:
            main_signal = signal_count

    has_signal = main_signal[1][0] >= successful_indicators_count and indicators_signals[0][0] == main_signal[0]
    print("Проверка сигнала", "(время пероверки", datetime.now(), "):")
    print("\tВалютная пара:", prices.symbol[0], "таймфрейм:", interval, "время свечи:", prices.datetime[0])
    print("\tЕсть ли сигнал:", has_signal)
    print("\tПоказания индикаторов:", signal_counts)
    print("="*200, "\n")

    if has_signal:
        return True, main_signal[0]
    return False, neutral_signal
