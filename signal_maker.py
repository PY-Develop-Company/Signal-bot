from pandas import DataFrame, Timedelta, read_csv
from datetime import timedelta, datetime, time
from tvDatafeed import Interval
from analizer import MainAnalizer, SOBAnalizer, SPAnalizer, NWAnalizer, UMAAnalizer, VolumeAnalizer
import interval_convertor
import price_parser
from price_parser import PriceData
import indicators_reader
import asyncio
from multiprocessing import Process
import os
from signals import *
from interval_convertor import timedelta_to_close_string, datetime_to_interval

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_data_path = "signals/"
currency_check_ended = "currency_check_ended/"
signals_analysis_last_date = {}
signal_last_update = datetime.now()


def is_profit(open_price, close_price, signal):
    profit = (True if close_price >= open_price else False) if (signal.type == LongSignal.type) else (
        True if (close_price <= open_price) else False)
    # print("profit", profit, signal, open_price, close_price)
    return profit


def get_close_position_signal_message(open, close, signal, symbol, interval):
    is_profit_position = is_profit(open, close, signal)
    text = profit_smile if is_profit_position else loss_smile
    debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

    message = f"{signal.smile} Сделка в {text} {symbol} {signal.text} {timedelta_to_close_string(interval)}"
    return message, is_profit_position


async def close_position(position_open_price, signal, pd: PriceData, bars_count=3):
    symbol = pd.symbol[:3] + "/" + pd.symbol[3:]
    delay_minutes = interval_convertor.interval_to_datetime(pd.interval) / Timedelta(minutes=1)
    await asyncio.sleep(delay_minutes * bars_count * 60)

    price_data = pd.get_price_data(2)

    msg, is_profit_position = get_close_position_signal_message(position_open_price, price_data.close[0], signal,
                                                                symbol,
                                                                price_data.datetime[0] - price_data.datetime[1])
    return msg, is_profit_position


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


def analize_currency_data_controller(prices_data, main_pd: PriceData):
    def analize_currency_data_function(prices_data, main_pd: PriceData):
        try:
            main_is_file_changed, main_price_df = price_parser.is_currency_file_changed(main_pd.symbol, main_pd.interval)
            if main_is_file_changed:
                is_files_changed = {}
                prices_df = {}
                for pd in prices_data:
                    is_file_changed, price_df = price_parser.is_currency_file_changed(pd.symbol, pd.interval)
                    is_files_changed.update({pd.interval: is_file_changed})
                    if is_file_changed:
                        prices_df.update({pd.interval: price_df})

                symbol = pd.symbol[:3] + pd.symbol[3:]

                interval_td = main_price_df.datetime[0] - main_price_df.datetime[1]
                analizer = MainAnalizer(4)
                has_signal = False
                signal = NeutralSignal()
                main_has_signal, main_signal, main_indicators_count, main_debug_text = analizer.analize(main_price_df, main_pd.interval)

                sob_signals_count = 0
                if main_has_signal:
                    for p_df in prices_df.items():
                        sob_analizer = SOBAnalizer()
                        sob_has_signal, sob_signal, _ = sob_analizer.analize(p_df[1], p_df[0].interval)
                        if sob_has_signal and sob_signal.type == main_signal.type:
                            sob_signals_count += 1
                    if sob_signals_count >= 2:
                        has_signal = True
                        signal = main_signal
                    print("sob_signals_count", sob_signals_count)

                open_position_price = main_price_df.close[0]
                msg = signal.get_open_msg_text(symbol, interval_td)
                data = [[has_signal, signal.type, msg + main_debug_text, main_price_df.datetime[0], open_position_price,
                         interval_td, main_indicators_count, sob_signals_count, pd.symbol, pd.exchange]]
                df = DataFrame(data, columns=["has_signal", "signal_type", "msg", "date", "open_price", "interval",
                                              "indicators_count", "sob_signals_count", "symbol", "exchange"])
                save_signal_data(df, pd.symbol, pd.interval)

                with open(f"{currency_check_ended}{pd.symbol}{str(pd.interval).replace('.', '')}.txt", "w") as file:
                    pass
        except Exception as e:
            print(e)

    async def analize_currency_data_loop(prices_data, main_pd: PriceData):
        for pd in prices_data:
            price_parser.reset_currency_file(pd.symbol, pd.interval)
        while True:
            analize_currency_data_function(prices_data, main_pd)
            await asyncio.sleep(1)

    asyncio.run(analize_currency_data_loop(prices_data, main_pd))


# test


async def signal_message_check_function_child(pd, full_df, deal_times):
    check_df = full_df.iloc[deal_times[-1]:].reset_index(drop=True)

    sob_is_signal, sob_signal, sob_debug_text = SOBAnalizer().analize(check_df, pd.interval)
    sp_is_signal, sp_signal, sp_debug_text = SPAnalizer().analize(check_df)
    nw_is_signal, nw_signal, nw_debug_text = NWAnalizer().analize(check_df)
    uma_is_signal, uma_signal, uma_debug_text = UMAAnalizer().analize(check_df)
    volume_is_signal, volume_signal, volume_debug_text = VolumeAnalizer().analize(check_df)

    open_position_price = check_df.close[0]
    data_el = [check_df["datetime"][0], sob_signal.type, volume_signal.type, uma_signal.type, nw_signal.type, sp_signal.type]
    deal_results = []
    print(f"analize {check_df['datetime'][0]}: \n\t", "open:", open_position_price)

    for deal_time in deal_times:
        close_position_price = full_df.close[0+deal_times[-1]-deal_time]
        has_profit_long = is_profit(open_position_price, close_position_price, LongSignal())
        deal_results.append(has_profit_long)

    deal_results.reverse()
    for deal_result in deal_results:
        data_el.insert(0, deal_result)
    return data_el


def signal_message_check_controller(pd, price_data_frame: DataFrame, bars_to_analyse, successful_indicators_count,
                                    deal_times):
    async def signal_message_check_function(pd, price_data_frame: DataFrame, bars_to_analyse,
                                            successful_indicators_count, deal_times):
        if len(price_data_frame) < bars_to_analyse:
            return
        df_data = []
        symbol = price_data_frame["symbol"][0]

        loop_count = len(price_data_frame) - bars_to_analyse - deal_times[-1]
        full_df = price_data_frame
        tasks = []
        for i in range(loop_count):
            t = asyncio.create_task(
                coro=signal_message_check_function_child(pd, full_df, deal_times))
            tasks.append(t)
            full_df = price_data_frame[i + 1:i + bars_to_analyse + deal_times[-1] + 1].reset_index(drop=True)
            full_df = full_df.iloc[1:].reset_index(drop=True)

        data = await asyncio.gather(*tasks)
        for d in data:
            if d is None:
                continue
            df_data.append([*d])
        if len(df_data) > 0:
            path = "debug/" + price_data_frame.symbol[0].split(":")[1] + str(pd.interval).replace(
                ".", "") + "_indicators_count_" + str(successful_indicators_count) + ".csv"

            deal_time_profit_column_names = []
            for deal_time in deal_times:
                deal_time_profit_column_names.append("is_profit_after_bars_" + str(deal_time))
            df = DataFrame(df_data, columns=[*deal_time_profit_column_names, "datetime", "SuperOrderBlock", "Volume", "UMA", "NW", "ScalpPro"])
            print("save data with path:", path)
            df.to_csv(path)
        else:
            print("No signals")

    asyncio.run(
        signal_message_check_function(pd, price_data_frame, bars_to_analyse, successful_indicators_count, deal_times))


if __name__ == "__main__":
    currencies = [price_parser.get_currencies()[0]]  # [("BTCUSD", "COINBASE"), ("ETHUSD", "COINBASE")]
    intervals = [Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute]

    prices_data = []

    for interval in intervals:
        for currency in currencies:
            pd = PriceData(currency[0], currency[1], interval)
            prices_data.append(pd)
            deal_times = range(1, 11)

    for pd in prices_data:
        df = pd.get_price_data(5000)
        for ind_count in [4]:  # range(3, 5):
            Process(target=signal_message_check_controller, args=(pd, df, 500, ind_count, deal_times,)).start()
