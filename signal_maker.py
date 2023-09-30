from pandas import DataFrame
from pandas import Timedelta
from datetime import timedelta, datetime
from tvDatafeed import Interval
import price_parser
import indicators_reader
import asyncio
from multiprocessing import Process, Array

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

photo_long_path = "img/long.jpg"
photo_short_path = "img/short.jpg"

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
        str(int(delay_days * 3)) + "Д"
    elif delay_hours > 0:
        return str(int(delay_hours * 3)) + "ч"
    return str(int(delay_minutes * 3)) + "мин"


def get_open_position_signal_message(signal, symbol, interval):
    message = get_smile(signal) + symbol + " " + signal + " " + timedelta_to_string(interval)

    photo_path = photo_long_path
    if signal == buy_signal:
        photo_path = photo_long_path
    elif signal == sell_signal:
        photo_path = photo_short_path

    return message, photo_path


def get_close_position_signal_message(open, close, signal, symbol, interval):
    is_profit = (True if close >= open else False) if (signal == buy_signal) else (
        True if (close <= open) else False)
    text = profit_message if is_profit else loss_message
    debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

    message = get_smile(signal) + "Сделка в " + text + symbol + " " + signal + " " + timedelta_to_string(
        interval) + debug_text
    return message, is_profit


async def close_position(position_open_price, signal, symbol, exchange, interval: timedelta, bars_count=3):
    delay_minutes = interval / Timedelta(minutes=1)
    await asyncio.sleep(delay_minutes * bars_count * 60)

    interval = indicators_reader.get_interval(interval)
    print(symbol, interval, exchange)
    price_data = price_parser.get_price_data(symbol.replace("/", ""), exchange, interval, bars_count=2)
    msg, is_profit = get_close_position_signal_message(position_open_price, price_data.close[0], signal, symbol,
                                             price_data.datetime[0] - price_data.datetime[1])
    return msg, is_profit


def check_signal(prices_df: DataFrame, interval: timedelta, successful_indicators_count=4):
    indicators_signals = [
        indicators_reader.get_super_order_block_signal(prices_df, prices_df.open, prices_df.close, prices_df.high,
                                                       prices_df.low, interval),
        indicators_reader.get_volume_signal(prices_df.open, prices_df.close),
        indicators_reader.get_ultimate_moving_average_signal(prices_df.close),
        indicators_reader.get_nadaraya_watson_envelope_signal(prices_df.close),
        indicators_reader.get_scalp_pro_signal(prices_df.close)]

    signal_counts = {buy_signal: [0, []], sell_signal: [0, []], neutral_signal: [0, []]}
    for signal in indicators_signals:
        signal_counts.get(signal[0])[0] += 1
        signal_counts.get(signal[0])[1].append(", " + signal[1])

    main_signal = (neutral_signal, [0, []])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0] and not(signal_count[0] == neutral_signal):
            main_signal = signal_count

    has_signal = main_signal[1][0] >= successful_indicators_count and indicators_signals[0][0] == main_signal[0]

    debug_text = f"""\n\nПроверка сигнала:
    \tВалютная пара: {prices_df.symbol[0]}" таймфрейм: {interval} время свечи: {prices_df.datetime[0]}
    \tЕсть ли сигнал: {has_signal}
    \tПоказания индикаторов: {signal_counts})
    """
    print(debug_text)
    # print("="*200, "\n")
    if has_signal:
        return True, main_signal[0], debug_text
    return False, neutral_signal, debug_text


#test


def signal_message_check_function(price_data_frame: DataFrame, profit_dict, bars_to_analyse=200):
    if len(price_data_frame) < bars_to_analyse:
        return

    interval = price_data_frame["datetime"][0] - price_data_frame["datetime"][1]

    loop_count = len(price_data_frame) - bars_to_analyse
    full_df = price_data_frame
    for i in range(loop_count):
        check_df = full_df.iloc[3:].reset_index(drop=True)
        start_check_time = datetime.now()

        has_signal, open_signal_type, debug_text = check_signal(check_df, interval, successful_indicators_count=4)
        # print("delay", datetime.now() - start_check_time)

        if has_signal:
            open_position_price = check_df.close[0]
            close_position_price = full_df.close[0]
            is_profit = (True if close_position_price >= open_position_price else False) if (
                        open_signal_type == buy_signal) else (True if (close_position_price <= open_position_price) else False)
            profit_dict[is_profit] += 1
        print("Profit data:", "\n\tprofit ---> ", profit_dict[1], "\n\tloss ---> ", profit_dict[0])

        full_df = price_data_frame[i+1:i+bars_to_analyse+4].reset_index(drop=True)
        full_df = full_df.iloc[1:].reset_index(drop=True)


if __name__ == "__main__":
    currencies = price_parser.get_currencies() #, [("BTCUSD", "COINBASE"), ("ETHUSD", "COINBASE")]  #
    intervals = [Interval.in_15_minute] #, Interval.in_5_minute, Interval.in_15_minute]

    profit_dict = Array('i', [0, 0])

    print("Profit data", profit_dict[:])
    for interval in intervals:
        for currency in currencies:
            df = price_parser.get_price_data(currency[0], currency[1], interval, 1000)
            Process(target=signal_message_check_function, args=(df, profit_dict,)).start()
            # signal_message_check_function(df, profit_dict)

    print("Profit data:", "\n\tprofit ---> ", profit_dict[1], "\n\tloss ---> ", profit_dict[0])
