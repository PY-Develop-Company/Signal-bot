from pandas import DataFrame, Timedelta, read_csv
from datetime import datetime
from tvDatafeed import Interval
import file_manager
from analizer import SOBAnalizer, SPAnalizer, NWAnalizer, UMAAnalizer, VolumeAnalizer, MultitimeframeAnalizer, NoDeltaSOBAnalizer
import interval_convertor
import price_parser
from price_parser import PriceData
import asyncio
from multiprocessing import Process
import os
from signals import *

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_data_path = "signals/"
signals_check_ended = "signals/check_ended/"
signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: Interval, bars_count=3):
    delay_seconds = interval_convertor.interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price, signal: Signal, pd: PriceData, bars_count=3):
    await close_position_delay(pd.interval, bars_count)

    price_data = pd.get_price_data(bars_count=2)

    msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price, price_data.close[0])
    return msg, is_profit_position


def save_signal_file(df, pd: PriceData):
    interval = str(pd.interval).replace(".", "")
    path = signals_data_path + pd.symbol + interval + ".csv"
    df.to_csv(path)
    with open(f"{signals_check_ended}{pd.symbol}{str(pd.interval).replace('.', '')}.txt", "w") as file:
        pass


def is_signals_analized(prices_data):
    prev_pd = None
    for pd in prices_data:
        prev_pd = pd
        path = signals_check_ended + pd.symbol + str(pd.interval).replace(".", "") + ".txt"
        if not file_manager.is_file_exists(path):
            # print("\tnot created ", path)
            return False, None

    path = signals_data_path + prev_pd.symbol + str(prev_pd.interval).replace(".", "") + ".csv"
    if file_manager.is_file_exists(path):
        df = read_csv(path)
        date = datetime.strptime(df.date[0], '%Y-%m-%d %H:%M:%S')
        return True, date
    return False, None


def read_signal_data(pd: PriceData):
    interval = str(pd.interval).replace(".", "")
    path = signals_check_ended + pd.symbol + interval + ".txt"
    if not file_manager.is_file_exists(path):
        return None
    path = signals_data_path + pd.symbol + interval + ".csv"
    if not file_manager.is_file_exists(path):
        return None

    df = read_csv(path)
    return df


def reset_signals_files(prices_data: [PriceData]):
    for pd in prices_data:
        interval = str(pd.interval).replace(".", "")
        path = signals_check_ended + pd.symbol + interval + ".txt"
        file_manager.delete_file_if_exists(path)


def analize_currency_data_controller(analize_pair):
    def analize_currency_data_function(main_pd: PriceData, sob_check_pds: [PriceData], unit_pd: PriceData):
        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        dt = main_price_df["datetime"][0]
        if not unit_pd.is_analize_time(dt):
            return

        prices_df = {}
        for pd in sob_check_pds:
            price_df = pd.get_chart_data_if_exists()
            is_price_df_exists = not (price_df is None)
            if is_price_df_exists:
                prices_df.update({pd: price_df})

        analizer = MultitimeframeAnalizer(4, 1)
        has_signal, signal, _, main_indicators_count, sob_signals_count = analizer.analize(main_price_df, main_pd.interval, prices_df)

        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd)

        data = [[has_signal, signal.type, msg, main_price_df.datetime[0], open_position_price, main_pd.interval,
                 main_indicators_count, sob_signals_count, main_pd.symbol, main_pd.exchange]]
        columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval",
                   "indicators_count", "sob_signals_count", "symbol", "exchange"]
        df = DataFrame(data, columns=columns)
        save_signal_file(df, main_pd)

        # if has_signal:
        print("Created signal file:", msg, main_indicators_count, sob_signals_count, main_price_df.datetime[0])

    async def analize_currency_data_loop(analize_pair):
        while True:
            analize_currency_data_function(analize_pair[0], analize_pair[1], analize_pair[2])
            await asyncio.sleep(1)

    asyncio.run(analize_currency_data_loop(analize_pair))


# test


async def signal_message_check_function_child(pd, full_df, deal_times):
    check_df = full_df.iloc[deal_times[-1]:].reset_index(drop=True)

    sob_start_time = datetime.now()
    sob_is_signal, sob_signal, sob_debug_text = NoDeltaSOBAnalizer().analize(check_df, pd.interval)
    sob_delta_time = datetime.now() - sob_start_time

    sp_start_time = datetime.now()
    sp_is_signal, sp_signal, sp_debug_text = SPAnalizer().analize(check_df)
    sp_delta_time = datetime.now() - sp_start_time

    nw_start_time = datetime.now()
    nw_is_signal, nw_signal, nw_debug_text = NWAnalizer().analize(check_df)
    nw_delta_time = datetime.now() - nw_start_time

    uma_start_time = datetime.now()
    uma_is_signal, uma_signal, uma_debug_text = UMAAnalizer().analize(check_df)
    uma_delta_time = datetime.now() - uma_start_time

    volume_start_time = datetime.now()
    volume_is_signal, volume_signal, volume_debug_text = VolumeAnalizer().analize(check_df)
    volume_delta_time = datetime.now() - volume_start_time

    open_position_price = check_df.close[0]
    data_el = [check_df["datetime"][0], sob_signal.type, volume_signal.type, uma_signal.type, nw_signal.type,
               sp_signal.type]
    deal_results = []
    print("loop")
    for deal_time in deal_times:
        close_position_price = full_df.close[0 + deal_times[-1] - deal_time]
        has_profit_long = LongSignal().is_profit(open_position_price, close_position_price)
        deal_results.append(has_profit_long)

    deal_results.reverse()
    for deal_result in deal_results:
        data_el.insert(0, deal_result)
    return data_el, sob_delta_time, sp_delta_time, nw_delta_time, uma_delta_time, volume_delta_time


def signal_message_check_controller(pd, price_data_frame: DataFrame, bars_to_analyse, successful_indicators_count, deal_times):
    async def signal_message_check_function(pd, price_data_frame: DataFrame, bars_to_analyse, successful_indicators_count, deal_times):
        if len(price_data_frame) < bars_to_analyse:
            return
        df_data = []

        loop_count = len(price_data_frame) - bars_to_analyse - deal_times[-1]
        full_df = price_data_frame
        tasks = []
        for i in range(loop_count):
            t = asyncio.create_task(coro=signal_message_check_function_child(pd, full_df, deal_times))
            tasks.append(t)
            full_df = price_data_frame[i + 1:i + bars_to_analyse + deal_times[-1] + 1].reset_index(drop=True)
            full_df = full_df.iloc[1:].reset_index(drop=True)

        datas = await asyncio.gather(*tasks)
        data = [data_el[0] for data_el in datas]
        print("sob wait time", sum([data_el[1] / Timedelta(seconds=1) for data_el in datas]))
        print("sp wait time", sum([data_el[2] / Timedelta(seconds=1) for data_el in datas]))
        print("nw wait time", sum([data_el[3] / Timedelta(seconds=1) for data_el in datas]))
        print("uma wait time", sum([data_el[4] / Timedelta(seconds=1) for data_el in datas]))
        print("volume wait time", sum([data_el[5] / Timedelta(seconds=1) for data_el in datas]))
        for d in data:
            if d is None:
                continue
            df_data.append([*d])
        if len(df_data) > 0:
            path = "debug/" + pd.symbol + "_" + str(pd.interval).replace(".", "") + ".csv"

            deal_time_profit_column_names = []
            for deal_time in deal_times:
                deal_time_profit_column_names.append("is_profit_after_bars_" + str(deal_time))
            df = DataFrame(df_data,
                           columns=[*deal_time_profit_column_names, "datetime", "SuperOrderBlock", "Volume", "UMA", "NW", "ScalpPro"])
            df.to_csv(path)
        else:
            print("No signals")

    asyncio.run(signal_message_check_function(pd, price_data_frame, bars_to_analyse, successful_indicators_count, deal_times))


if __name__ == "__main__":
    currencies = price_parser.get_currencies()[1:4]
    intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]

    prices_data = []

    for interval in intervals:
        for currency in currencies:
            pd = PriceData(currency[0], currency[1], interval)
            prices_data.append(pd)
            deal_times = range(1, 11)

    for pd in prices_data:
        # df = pd.get_price_data(5000)
        df = read_csv("currencies_data/debug/" + pd.symbol + str(pd.interval).replace(".", "") + ".csv")
        for ind_count in [4]:  # range(3, 5):
            Process(target=signal_message_check_controller, args=(pd, df, 500, ind_count, deal_times,)).start()
