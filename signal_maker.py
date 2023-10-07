from pandas import DataFrame, Timedelta, read_csv
from datetime import timedelta, datetime, time
from tvDatafeed import Interval

import interval_convertor
import price_parser
from price_parser import PriceData
import indicators_reader
import asyncio
from multiprocessing import Process
import os
from signals import *
from interval_convertor import timedelta_to_string, datetime_to_interval

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_data_path = "signals/"
currency_check_ended = "currency_check_ended/"
signals_analysis_last_date = {}
signal_last_update = datetime.now()


def is_profit(open_price, close_price, signal):
    profit = (True if close_price >= open_price else False) if (signal.type == LongSignal.type) else (
        True if (close_price <= open_price) else False)
    print("profit", profit, signal, open_price, close_price)
    return profit


def get_close_position_signal_message(open, close, signal, symbol, interval):
    is_profit_position = is_profit(open, close, signal)
    text = profit_smile if is_profit_position else loss_smile
    debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

    message = f"{signal.smile} Сделка в {text} {symbol} {signal.text} {timedelta_to_string(interval)}"
    return message, is_profit_position


async def close_position(position_open_price, signal, symbol, exchange, interval: timedelta, bars_count=3):
    symbol = symbol[:3] + "/" + symbol[3:]
    delay_minutes = interval / Timedelta(minutes=1)
    await asyncio.sleep(delay_minutes * bars_count * 60)

    interval = datetime_to_interval(interval)
    print("close, simbol:", symbol)
    price_data = price_parser.get_price_data(symbol.replace("/", ""), exchange, interval, bars_count=2)

    msg, is_profit_position = get_close_position_signal_message(position_open_price, price_data.close[0], signal, symbol,
                                                       price_data.datetime[0] - price_data.datetime[1])
    print("signal mgs:", signal, msg, symbol, exchange, interval, position_open_price, "clsoe position price", price_data.close[0])
    return msg, is_profit_position


def check_signal(prices_df: DataFrame, interval: timedelta, successful_indicators_count=4):
    analize_block_delta = indicators_reader.sob_dict.get(prices_df["symbol"][0].split(":")[1]).get(interval_convertor.datetime_to_interval(interval))
    volume_ind = indicators_reader.VolumeIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    sp_ind = indicators_reader.ScalpProIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    uma_ind = indicators_reader.UMAIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    sob_ind = indicators_reader.SuperOrderBlockIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low, interval, analize_block_delta)
    nw_ind = indicators_reader.NadarayaWatsonIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)

    indicators_signals = [sob_ind.get_signal(), volume_ind.get_signal(), uma_ind.get_signal(), nw_ind.get_signal(), sp_ind.get_signal()]

    signal_counts = {LongSignal.type: [0, [], LongSignal()], ShortSignal.type: [0, [], ShortSignal()], NeutralSignal.type: [0, [], NeutralSignal()]}
    for ind_signal in indicators_signals:
        signal_counts.get(ind_signal[0].type)[0] += 1
        signal_counts.get(ind_signal[0].type)[1].append(", " + ind_signal[1])

    main_signal = (NeutralSignal.type, [0, [], NeutralSignal()])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0] and not(signal_count[0] == NeutralSignal.type):
            main_signal = signal_count

    has_signal = main_signal[1][0] >= successful_indicators_count and indicators_signals[0][0].type == main_signal[0]

    debug_dict = {}
    for sig in signal_counts.items():
        debug_dict[sig[1][2].text] = sig[1][:2]
    debug_text = f"""\n\nПроверка сигнала:
    \tВалютная пара: {prices_df.symbol[0]}" таймфрейм: {interval} время свечи: {prices_df.datetime[0]}
    \tЕсть ли сигнал: {has_signal}
    \tПоказания индикаторов: {debug_dict})\n
    """
    print(debug_text)
    # print("="*200, "\n")
    if has_signal:
        return True, main_signal[1][2], main_signal[1][0], debug_text
    return False, NeutralSignal(), 0, debug_text


def save_signal_data(df, currency, interval: Interval):
    interval = str(interval).replace(".", "")
    path = signals_data_path + currency + interval + ".csv"
    df.to_csv(path)


def is_signals_analized(prices_data):
    prev_path = None
    date = None
    for pd in prices_data:
        path = currency_check_ended + pd.symbol + str(pd.interval).replace(".", "") + ".txt"
        if not os.path.exists(path):
            return False, date

        path = signals_data_path + pd.symbol + str(pd.interval).replace(".", "") + ".csv"
        if not os.path.exists(path):
            if not (prev_path is None):
                df = read_csv(prev_path)
                print(df.date[0])
                date = datetime.strptime(df.date[0], '%Y-%m-%d %H:%M:%S')
            return False, date
        prev_path = path
    df = read_csv(prev_path)
    date = datetime.strptime(df.date[0], '%Y-%m-%d %H:%M:%S')
    return True, date


def read_signal_data(currency, interval):
    interval = str(interval).replace(".", "")
    path = currency_check_ended + currency + interval + ".txt"
    if not os.path.exists(path):
        return None
    path = signals_data_path + currency + interval + ".csv"
    if not os.path.exists(path):
        return None
    df = read_csv(path)
    return df


def reset_signals_files(prices_data: []):
    for pd in prices_data:
        interval = str(pd.interval).replace(".", "")
        path = currency_check_ended + pd.symbol + interval + ".txt"
        if os.path.exists(path):
            os.remove(path)
        path = signals_data_path + pd.symbol + interval + ".csv"
        if os.path.exists(path):
            os.remove(path)


def analize_currency_data_controller(price_data):
    def analize_currency_data_function(price_data: PriceData):
        try:
            is_file_changed, price_df = price_parser.is_currency_file_changed(price_data.symbol, price_data.interval)
        except Exception as e:
            print("handle", e)
            print(price_data.symbol, price_data.interval)
            return
        if is_file_changed:
            symbol = price_data.symbol + price_data.exchange

            interval_td = price_df.datetime[0] - price_df.datetime[1]
            has_signal, signal, indicators_count, debug_text = check_signal(price_df, interval_td, successful_indicators_count=4)

            open_position_price = price_df.close[0]
            msg = signal.get_open_msg_text(symbol, interval_td)
            data = [[has_signal, signal.type, msg + debug_text, price_df.datetime[0], open_position_price, interval_td, indicators_count, price_data.symbol, price_data.exchange]]
            df = DataFrame(data, columns=["has_signal", "signal_type", "msg", "date", "open_price", "interval", "indicators_count", "symbol", "exchange"])
            save_signal_data(df, price_data.symbol, price_data.interval)

            with open(f"{currency_check_ended}{price_data.symbol}{str(price_data.interval).replace('.', '')}.txt", "w") as file:
                pass
            # await handle_signal_msg(signal_type, msg + debug_text, currency[0], currency[1], interval_td, open_position_price, start_check_time)
            # price_parser.update_last_check_date(currency[0], interval_td)

    async def analize_currency_data_loop(price_data):
        price_parser.reset_currency_file(price_data.symbol, price_data.interval)
        while True:
            analize_currency_data_function(price_data)
            await asyncio.sleep(1)

    asyncio.run(analize_currency_data_loop(price_data))

#test


def check_signal_test(prices_df: DataFrame, interval: timedelta, successful_indicators_count=4):
    analize_block_delta = indicators_reader.sob_dict.get(prices_df["symbol"][0].split(":")[1]).get(interval_convertor.datetime_to_interval(interval))
    print(analize_block_delta)
    volume_ind_signal = indicators_reader.VolumeIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low).get_signal()
    sp_ind_signal = indicators_reader.ScalpProIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low).get_signal()
    uma_ind_signal = indicators_reader.UMAIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low).get_signal()
    sob_ind_signal = indicators_reader.SuperOrderBlockIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low, interval, analize_block_delta).get_signal()
    nw_ind_signal = indicators_reader.NadarayaWatsonIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low).get_signal()

    indicators_signals = [sob_ind_signal, volume_ind_signal, uma_ind_signal, nw_ind_signal, sp_ind_signal]

    signal_counts = {LongSignal.type: [0, [], LongSignal()], ShortSignal.type: [0, [], ShortSignal()], NeutralSignal.type: [0, [], NeutralSignal()]}
    for ind_signal in indicators_signals:
        signal_counts.get(ind_signal[0].type)[0] += 1
        signal_counts.get(ind_signal[0].type)[1].append(", " + ind_signal[1])

    main_signal = (NeutralSignal.type, [0, [], NeutralSignal()])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0] and not(signal_count[0] == NeutralSignal.type):
            main_signal = signal_count

    has_signal = main_signal[1][0] >= successful_indicators_count and indicators_signals[0][0].type == main_signal[0]

    debug_dict = {}
    for sig in signal_counts.items():
        debug_dict[sig[1][2].text] = sig[1][:2]
    debug_text = f"""\n\nПроверка сигнала:
    \tВалютная пара: {prices_df.symbol[0]}" таймфрейм: {interval} время свечи: {prices_df.datetime[0]}
    \tЕсть ли сигнал: {has_signal}
    \tПоказания индикаторов: {debug_dict})\n
    """
    print(debug_text)
    # print("="*200, "\n")
    if has_signal:
        return True, main_signal[1][2], main_signal[1][0], debug_text, indicators_signals
    return False, NeutralSignal(), 0, debug_text, indicators_signals


async def signal_message_check_function_child(symbol, deal_time, check_df, full_df, interval, successful_indicators_count):
    has_signal, open_signal, ind_count, debug_text, ind_data = check_signal_test(check_df, interval,
                                                                  successful_indicators_count=successful_indicators_count)
    # print("check signal")
    if has_signal:
        print("wehavesignal")
        open_position_price = check_df.close[0]
        close_position_price = full_df.close[0]
        has_profit = is_profit(open_position_price, close_position_price, open_signal)
        print("open_position_price", open_position_price)
        print("close_position_price", close_position_price)

        print(debug_text)
        data_el = [check_df["datetime"][0],
                   has_profit, open_signal.type, open_position_price, close_position_price,
                   ind_data[0][0].type, ind_data[1][0].type, ind_data[2][0].type, ind_data[3][0].type, ind_data[4][0].type]
        return data_el
    return None


def signal_message_check_controller(price_data_frame: DataFrame, bars_to_analyse=200, successful_indicators_count=4, deal_time=3):
    async def signal_message_check_function(price_data_frame: DataFrame, bars_to_analyse=200, successful_indicators_count=4, deal_time=3):
        if len(price_data_frame) < bars_to_analyse:
            return

        df_data = []
        interval = price_data_frame["datetime"][0] - price_data_frame["datetime"][1]
        symbol = price_data_frame["symbol"][0]

        loop_count = len(price_data_frame) - bars_to_analyse
        full_df = price_data_frame
        tasks = []
        for i in range(loop_count):
            check_df = full_df.iloc[deal_time:].reset_index(drop=True)
            t = asyncio.create_task(coro=signal_message_check_function_child(symbol, deal_time, check_df, full_df, interval, successful_indicators_count))
            tasks.append(t)
            full_df = price_data_frame[i + 1:i + bars_to_analyse + deal_time + 1].reset_index(drop=True)
            full_df = full_df.iloc[1:].reset_index(drop=True)

        data = await asyncio.gather(*tasks)
        for d in data:
            if d is None:
                continue
            df_data.append([*d])
        if len(df_data) > 0:
            path = "debug/" + price_data_frame.symbol[0].split(":")[1] + str(datetime_to_interval(interval)).replace(".", "") + "_indicators_count_" + str(successful_indicators_count) + "deal_time" + str(deal_time) + ".csv"
            df = DataFrame(df_data, columns=["datetime",
                "is_profit", "signal", "open_signal_price", "close_signal_price",
                "SuperOrderBlock", "Volume", "UMA", "NW", "ScalpPro"])
            df.to_csv(path)
        else:
            print("No signals")
    asyncio.run(signal_message_check_function(price_data_frame, bars_to_analyse, successful_indicators_count, deal_time))


if __name__ == "__main__":
    currencies = [price_parser.get_currencies()[1]]  # [("BTCUSD", "COINBASE"), ("ETHUSD", "COINBASE")]  #
    intervals = [Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute]

    # profit_dict = Array('i', [0, 0])

    # print("Profit data", profit_dict[:])
    for interval in intervals:
        for currency in currencies:
            for ind_count in [4]:  # range(3, 5):
                for deal_time in [3]:  # range(1, 6):
                    df = price_parser.get_price_data(currency[0], currency[1], interval, 1500)
                    Process(target=signal_message_check_controller, args=(df, 500, ind_count, deal_time,)).start()
                    # signal_message_check_function(df, profit_dict)

    # print("Profit data:", "\n\tprofit ---> ", profit_dict[1], "\n\tloss ---> ", profit_dict[0])