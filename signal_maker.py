import pandas
from pandas import DataFrame, Timedelta, read_csv
from datetime import datetime
from tvDatafeed import Interval, TvDatafeed

import analizer
import file_manager
from analizer import MultitimeframeAnalizer
import interval_convertor
from price_parser import PriceData
import asyncio
from signals import *
import multiprocessing
import price_parser

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
        msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price_original, position_open_price_original, bars_count)
    else:
        msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price.close[0],price_data.close[0], bars_count)
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


def analize_funcc(main_price_df, prices_dfs, check_pds: [PriceData]):
    main_pd = check_pds[0]

    analizer = MultitimeframeAnalizer(2, 2)
    has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)

    open_position_price = main_price_df.close[0]
    msg = signal.get_open_msg_text(main_pd, deal_time)

    data = [[has_signal, signal.type, msg, main_price_df.datetime[0], open_position_price, main_pd.interval,
             main_pd.symbol, main_pd.exchange, deal_time]]
    columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval", "symbol", "exchange", "deal_time"]
    df = DataFrame(data, columns=columns)
    save_signal_file(df, main_pd)

    print("Created signal file:", msg, main_price_df.datetime[0])


def analize_currency_data_controller(analize_pairs):
    async def analize_currency_data_function(check_pds: [PriceData], unit_pd: PriceData):
        main_pd = check_pds[0]
        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        dt = main_price_df["datetime"][0]
        if not unit_pd.is_analize_time(dt):
            return

        prices_dfs = []
        for pd in check_pds:
            ch_data = pd.get_chart_data_if_exists()
            if ch_data is None:
                continue
            prices_dfs.append(ch_data)

        analizer = MultitimeframeAnalizer(0, 2)
        has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)

        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd, deal_time)

        data = [[has_signal, signal.type, msg, main_price_df.datetime[0], open_position_price, main_pd.interval,
                 main_pd.symbol, main_pd.exchange, deal_time]]
        columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval", "symbol", "exchange", "deal_time"]
        df = DataFrame(data, columns=columns)
        save_signal_file(df, main_pd)

        print("Created signal file:", msg, main_price_df.datetime[0])

    async def analize_currency_data_loop(analize_pairs):
        while True:
            tasks = []
            for analize_pair in analize_pairs:
                task = asyncio.create_task(analize_currency_data_function([analize_pair[0], *analize_pair[1]], analize_pair[2]))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(5)

    asyncio.run(analize_currency_data_loop(analize_pairs))
# def analize_currency_data_controller(analize_pair):
#     def analize_currency_data_function(check_pds: [PriceData], unit_pd: PriceData):
#         main_pd = check_pds[0]
#         main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
#         if main_price_df is None:
#             return
#
#         dt = main_price_df["datetime"][0]
#         if not unit_pd.is_analize_time(dt):
#             return
#
#         prices_dfs = []
#         for pd in check_pds:
#             ch_data = pd.get_chart_data_if_exists()
#             if ch_data is None:
#                 continue
#             prices_dfs.append(ch_data)
#
#         analizer = MultitimeframeAnalizer(2, 2)
#         has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)
#
#         open_position_price = main_price_df.close[0]
#         msg = signal.get_open_msg_text(main_pd, deal_time)
#
#         data = [[has_signal, signal.type, msg, main_price_df.datetime[0], open_position_price, main_pd.interval,
#                  main_pd.symbol, main_pd.exchange, deal_time]]
#         columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval", "symbol", "exchange", "deal_time"]
#         df = DataFrame(data, columns=columns)
#         save_signal_file(df, main_pd)
#
#         print("Created signal file:", msg, main_price_df.datetime[0])
#
#     async def analize_currency_data_loop(analize_pair):
#         while True:
#             analize_currency_data_function([analize_pair[0], *analize_pair[1]], analize_pair[2])
#             await asyncio.sleep(1)
#
#     asyncio.run(analize_currency_data_loop(analize_pair))


#test

def get_df_with_date(df: DataFrame, date, datetime):
    for df_row in range(1, len(df.index)):
        if df.loc[df_row, "datetime_sec"] > date:
            continue
        elif df.loc[df_row, "datetime_sec"] <= date < df.loc[df_row-1, "datetime_sec"]:
            # print("true", df.loc[df_row+1, "datetime"], datetime, df.interval[0])
            return df.loc[df_row-1:].reset_index(drop=True)
        else:
            return None
    return df


def analize_controller(pds, dfs, bars_to_analize):
    def calculate_profit(deal_time, signal, full_df, i):
        deal_time_bars_count = int(
            deal_time / interval_convertor.interval_to_int(interval_convertor.str_to_interval(full_df.loc[0, "interval"])))
        if i - deal_time_bars_count < 0:
            return None, 0, 0
        open = float(full_df.loc[i, "close"])
        close = float(full_df.loc[i - deal_time_bars_count, "close"])
        is_profit = signal.is_profit(open, close)
        return is_profit, open, close

    async def analize_func(pds, dfs, bars_to_analize):
        analize_count = len(dfs[0].index) - bars_to_analize
        analizer = MultitimeframeAnalizer(2, 2)
        analzie_dfs = []
        analzie_dfs_i = []
        profit_dict = {True: 0, False: 0}
        for i in range(analize_count):
            analzie_dfs_child = []
            df_0 = dfs[0].loc[i:i + bars_to_analize].reset_index(drop=True)
            analzie_dfs_child.append(df_0)
            main_datetime = analzie_dfs_child[0].datetime_sec[0]
            is_full_data = True
            for a in range(1, len(dfs)):
                df_1 = get_df_with_date(dfs[a], main_datetime, analzie_dfs_child[0].datetime[0])
                if df_1 is None:
                    is_full_data = False
                    continue
                dfs[a] = df_1
                analzie_dfs_child.append(df_1.loc[2:2+bars_to_analize].reset_index(drop=True))
            if not is_full_data:
                continue
            analzie_dfs.append(analzie_dfs_child)
            analzie_dfs_i.append(i)

        tasks = []
        for analzie_dfs_child in analzie_dfs:
            t = asyncio.create_task(analizer.analize(analzie_dfs_child, pds))
            tasks.append(t)
        results = await asyncio.gather(*tasks)
        for ind in range(len(results)):
            has_signal = results[ind][0]
            if has_signal:
                signal = results[ind][1]
                debug = results[ind][2]
                deal_time = results[ind][3]
                i = analzie_dfs_i[ind]
                profit, open, close = calculate_profit(deal_time, signal, dfs[0], i)
                if profit is None:
                    continue
                print(has_signal, signal.type, deal_time, open, close, debug)
                profit_dict.update({profit: profit_dict.get(profit)+1})
        print(profit_dict, "profit_dict")
    asyncio.run(analize_func(pds, dfs, bars_to_analize))


def calculate_indicators_data(pd, df, bars_to_analize):
    async def calculate_func(pd, df: DataFrame, bars_to_analize):
        path = f"debug/NW_{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
        analize_count = len(df.index) - bars_to_analize
        # for j in range(2, 5):
        #     print(j, datetime.now())
        tasks = []
        i_s = []
        for i in range(analize_count):
            df_part = df.loc[i:i + bars_to_analize].reset_index(drop=True)
            sob_analizer = analizer.NWAnalizer(2)
            t = asyncio.create_task(sob_analizer.analize(df_part, pd))
            tasks.append(t)
            i_s.append(i)
        results = await asyncio.gather(*tasks)

        df = read_csv(path)
        df.loc[:, f"nw2"] = "None"
        for i, result in enumerate(results):
            df.loc[i, f"nw2"] = result[1].type

        df.to_csv(path)

    asyncio.run(calculate_func(pd, df, bars_to_analize))


def calculate_profit(pd, df, start_bars, end_bars):
    path = f"debug/profit_{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
    ва = read_csv(path)
    for i in range(start_bars, end_bars):
        df.loc[:, f"profit_in_bars_{i}"] = "None"
        for j in df.index:
            if j-i < 0:
                continue

            open_price = df.loc[j, "close"]
            close_price = df.loc[j-i, "close"]
            prof = "long" if close_price >= open_price else "short"
            df.loc[j, f"profit_in_bars_{i}"] = prof
    df.to_csv(path)


if __name__ == "__main__":
    curs = price_parser.get_currencies()
    intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute, Interval.in_45_minute, Interval.in_1_hour, Interval.in_2_hour]

    intervals_group = [
        [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute, Interval.in_45_minute, Interval.in_1_hour, Interval.in_2_hour]

        # [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute],
        # [Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute],
        # [Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]
    ]
    dfs = None
    for cur in curs:
        for interval in intervals[0:3]:
            pd = PriceData(cur[0], cur[1], interval)
            save_path = f"debug/full_data/{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
            df = read_csv(save_path).drop("Unnamed: 0", axis=1)
            df.replace("", float("NaN"), inplace=True)
            df.dropna(subset=["sob_delta"], inplace=True)
            df = df[df.sob_delta != "neutral"]
            df = df[df.sob_delta == df["volume4"]]
            df = df[df.sob_delta == df["sp8/10/8"]]
            # df = df[df.sob_delta == df["NW3"]]
            df = df[df.sob_delta == df["uma5"]]
            if dfs is None:
                dfs = df
            else:
                dfs = pandas.concat([dfs, df], ignore_index=True)
    # print(dfs.to_string())
    deals_count = len(dfs.index)

    dfs = dfs[dfs.sob_delta == dfs.profit_in_bars_1]
    profit_deals_count = len(dfs.index)
    print(profit_deals_count / deals_count)

    dfs = dfs[dfs.sob_delta == dfs.profit_in_bars_3]
    profit_deals_count = len(dfs.index)
    print(profit_deals_count / deals_count)

    dfs = dfs[dfs.sob_delta == dfs.profit_in_bars_6]
    profit_deals_count = len(dfs.index)
    print(profit_deals_count / deals_count)

    dfs = dfs[dfs.sob_delta == dfs.profit_in_bars_12]
    profit_deals_count = len(dfs.index)
    print(profit_deals_count / deals_count)



    pds_group = []
    tv = TvDatafeed()
    # CALCULATE INDICATORS
    # pds = []
    # for cur in curs:
    #     for interval in intervals:
    #         pd = PriceData(cur[0], cur[1], interval)
    #         path = f"{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
    #         df = read_csv(path)[::-1].reset_index(drop=True).drop("Unnamed: 0", axis=1)
    #         multiprocessing.Process(target=calculate_indicators_data, args=(pd, df, 500, )).start()

    # CALCULATE PROFIT
    # for cur in curs:
    #     for interval in intervals:
    #         pd = PriceData(cur[0], cur[1], interval)
    #         path = f"{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
    #         df = read_csv(path)[::-1].reset_index(drop=True).drop("Unnamed: 0", axis=1)
    #         multiprocessing.Process(target=calculate_profit, args=(pd, df, 1, 31)).start()

    # GET DATA
    # pds = []
    # for cur in curs:
    #     for interval in intervals:
    #         pd = PriceData(cur[0], cur[1], interval)
    #         path = f"{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
    #         pds.append(pd)
    #         # df = tv.get_hist(cur[0], cur[1], interval, n_bars=5000)
    #         # df["interval"] = pd.interval
    #         # df.to_csv(path)
    #         df = read_csv(path)
    #         df["datetime_sec"] = df.apply(lambda x: (datetime.strptime(x["datetime"], '%Y-%m-%d %H:%M:%S')-datetime(2022, 1, 1)).total_seconds(), axis=1)
    #         print(df)
    #         df.to_csv(path)

    # ANALIZE WITH ANALIZER
    # for interval_group in intervals_group:
    #     for cur in curs:
    #         pd_group = []
    #         for interval in interval_group:
    #             pd = PriceData(cur[0], cur[1], interval)
    #             pd_group.append(pd)
    #
    # for pd_group in pds_group:
    #     analize_dfs = []
    #     for pd in pd_group:
    #         path = f"{pd.symbol}{str(pd.interval).replace('.', '')}.csv"
    #         analize_dfs.append(read_csv(path)[::-1].reset_index(drop=True))
    #     multiprocessing.Process(target=analize_controller, args=(pd_group, analize_dfs, 500, )).start()
