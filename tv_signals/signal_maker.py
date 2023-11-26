from pandas import DataFrame, Timedelta, read_csv
from tvDatafeed import Interval
import asyncio

from datetime import datetime

from tv_signals.analizer import NewMultitimeframeAnalizer
from tv_signals.signal_types import *

from utils import file_manager, interval_convertor


username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_data_path = "./signals/"
signals_check_ended = "./signals/check_ended/"
signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: Interval, bars_count=3):
    delay_seconds = interval_convertor.interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price_original, signal: Signal, pd: PriceData, bars_count):
    position_open_price = pd.get_price_data(bars_count=2)
    await close_position_delay(Interval.in_1_minute, bars_count)

    price_data = pd.get_price_data(bars_count=2)
    if (price_data is None) or (position_open_price is None):
        msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price_original,
                                                                           position_open_price_original, bars_count)
    else:
        msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price.close[0],
                                                                           price_data.close[0], bars_count)
    return msg, is_profit_position


def save_signal_file(df, pd: PriceData):
    interval = str(pd.interval).replace(".", "")
    path = signals_data_path + pd.symbol + interval + ".csv"
    df.to_csv(path)
    with open(f"{signals_check_ended}{pd.symbol}{str(pd.interval).replace('.', '')}.txt", "w") as file:
        pass


def is_signal_analized(pd):
    path = signals_check_ended + pd.symbol + str(pd.interval).replace(".", "") + ".txt"
    return file_manager.is_file_exists(path)


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


def is_all_charts_collected(main_pd: PriceData, parent_pds: [PriceData]):
    expected_bars = []
    real_bars = []

    main_df = main_pd.get_chart_data_if_exists()
    if main_df is None:
        return False
    main_df_last_bar_checked = main_df["datetime"][0]

    expected_bars.append(main_df_last_bar_checked)
    real_bars.append(main_df_last_bar_checked)
    res = True
    for parent_pd in parent_pds:
        parent_df = parent_pd.get_chart_data_if_exists()
        if parent_df is None:
            res = False
            break
        parent_df_last_bar_checked = parent_df["datetime"][0]
        needed_bar = parent_pd.get_needed_chart_bar_to_analize(main_df_last_bar_checked, main_pd.interval)

        real_bars.append(parent_df_last_bar_checked)
        expected_bars.append(needed_bar)
        if not (parent_df_last_bar_checked == needed_bar):
            res = False
            break
    print("r", real_bars)
    print("e", expected_bars)
    return res


def analize_currency_data_controller(analize_pds, additional_pds):
    async def analize_currency_data_function(check_pds: [PriceData], additional_pds):
        main_pd = check_pds[0]
        start_analize_time = check_pds[0].get_chart_download_time()

        if not is_all_charts_collected(check_pds[0], check_pds[1:]):
            return

        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        prices_dfs = []
        for pd in check_pds:
            ch_data = pd.get_chart_data_if_exists()
            if ch_data is None:
                continue
            prices_dfs.append(ch_data)

        analizer = NewMultitimeframeAnalizer(1, 1)
        has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)

        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd, deal_time)

        data = [[has_signal, signal.type, msg, main_price_df.datetime[0], open_position_price, main_pd.interval,
                 main_pd.symbol, main_pd.exchange, deal_time, debug, start_analize_time]]
        columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval", "symbol", "exchange",
                   "deal_time", "debug", "start_analize_time"]
        df = DataFrame(data, columns=columns)
        save_signal_file(df, main_pd)

        print("Created signal file:", msg, main_price_df.datetime[0])

    async def analize_currency_data_loop(analize_pds, additional_pds):
        while True:
            print("analize_loop")
            tasks = []
            for i in range(len(analize_pds)):
                task = asyncio.create_task(analize_currency_data_function(analize_pds[i], additional_pds[i]))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(3)

    asyncio.run(analize_currency_data_loop(analize_pds, additional_pds))
