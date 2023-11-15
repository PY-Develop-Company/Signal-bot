from pandas import DataFrame, Timedelta, read_csv
from datetime import datetime
from tvDatafeed import Interval
import file_manager
from analizer import MultitimeframeAnalizer
import interval_convertor
from price_parser import PriceData
import asyncio
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
    if not file_manager.is_file_exists(path):
        return False

    return True


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
    main_df = main_pd.get_chart_data_if_exists()
    if main_df is None:
        return False
    main_df_last_bar_checked = main_df["datetime"][0]
    expected_bars.append(main_df_last_bar_checked)
    for parent_pd in parent_pds:
        parent_df = parent_pd.get_chart_data_if_exists()
        if parent_df is None:
            return False
        parent_df_last_bar_checked = parent_df["datetime"][0]
        needed_bar = parent_pd.get_needed_chart_bar_to_analize(main_df_last_bar_checked, main_pd.interval)

        expected_bars.append(needed_bar)
        if not (parent_df_last_bar_checked == needed_bar):
            return False

    return True


def analize_currency_data_controller(analize_pairs):
    async def analize_currency_data_function(check_pds: [PriceData], unit_pd: PriceData):
        main_pd = check_pds[0]
        start_analize_time = check_pds[0].get_chart_download_time()

        if not is_all_charts_collected(check_pds[0], check_pds[1:]):
            return

        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        # dt = main_price_df["datetime"][0]
        # if not unit_pd.is_analize_time(dt):
        #     return

        prices_dfs = []
        for pd in check_pds:
            ch_data = pd.get_chart_data_if_exists()
            if ch_data is None:
                continue
            prices_dfs.append(ch_data)

        analizer = MultitimeframeAnalizer(2, 2)
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

    async def analize_currency_data_loop(analize_pairs):
        while True:
            print("analize_loop")
            tasks = []
            for analize_pair in analize_pairs:
                task = asyncio.create_task(
                    analize_currency_data_function([analize_pair[0], *analize_pair[1]], analize_pair[2]))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(3)

    asyncio.run(analize_currency_data_loop(analize_pairs))


# test


# def analize_controller(pds, dfs, bars_to_analize):
#     async def analize_func(pds, dfs, bars_to_analize):
#         analize_count = len(dfs[0].index) - bars_to_analize
#         analizer = MultitimeframeAnalizer(2, 2)
#         analzie_dfs = []
#         for i in range(analize_count):
#             analzie_dfs[0] = dfs[0].loc[i + 1:i + bars_to_analize].reset_index(drop=True)
#             #other dfs selection
#             has_signal, signal, debug, deal_time = analizer.analize(dfs, pds)
#     asyncio.run(analize_func(pds, dfs, bars_to_analize))
#
#
# if __name__ == "__main__":
#     curs = price_parser.get_currencies()
#     intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]
#
#     intervals_group = [
#         [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute],
#         [Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute],
#         [Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]
#     ]
#
#     pds_group = []
#     tv = TvDatafeed()
#     # for cur in curs:
#     #     for interval in intervals:
#     #         pds.append(PriceData(cur[0], cur[1], interval))
#     for interval_group in intervals_group:
#         for cur in curs:
#             pd_group = []
#             for interval in interval_group:
#                 pd_group.append(PriceData(cur[0], cur[1], interval))
#             pds_group.append(pd_group)
#
#     for pd_group in pds_group:
#         analize_dfs = []
#         for pd in pd_group:
#             path = f"{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
#             analize_dfs.append(read_csv(path))
#         multiprocessing.Process(target=analize_controller, args=(pd_group, analize_dfs, bars_to_analize, )).start()
#         # df = tv.get_hist(pd.symbol, pd.exchange, pd.interval, n_bars=5000)
#         # df.to_csv(path)
