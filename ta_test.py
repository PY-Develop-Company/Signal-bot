import time
from _operator import index

# import tradingview_ta
# from tradingview_ta import TA_Handler, Interval, Exchange
import pandas as pd
from pandas import Timedelta
from signals import *
from datetime import timedelta, datetime
from tvDatafeed import Interval
from interval_convertor import interval_to_int, str_to_interval, interval_to_string
from signals import get_signal_by_type
import price_parser


def income_percent_diff(df1, df2):
    if len(df1) > 0 and len(df2) > 0:
        print("Кількість угод в новій стратегії:", len(df1.index))
        print("Кількість угод в старій стратегії:", len(df2.index))
        for i in range(1, 11):
            print()
            profit_data_1 = df1["is_profit_after_bars_" + str(i)].value_counts()
            profit_data_2 = df2["is_profit_after_bars_" + str(i)].value_counts()
            try:
                los1 = profit_data_1[False]
            except Exception:
                los1 = 1
            try:
                los2 = profit_data_2[False]
            except Exception:
                los2 = 1
            try:
                prof1 = profit_data_1[True]
            except Exception:
                prof1 = 0
            try:
                prof2 = profit_data_2[True]
            except Exception:
                prof2 = 0
            profit_percent_1 = prof1 / los1
            profit_percent_2 = prof2 / los2
            print(f" Час угоди {i} свічок \n\tРізниця профіту:", profit_percent_1 - profit_percent_2)
            print(f" Профіт новий:", profit_percent_1)
            print(f" Профіт старий:", profit_percent_2, "\n")
    else:
        print("no data")


def income_percent(df, column):
    if len(df) > 0:
        print("Кількість угод в новій стратегії:", len(df.index), 5000/len(df.index))
        profit_data = df[column].value_counts()
        try:
            los1 = profit_data[False]
        except Exception:
            los1 = 1
        try:
            prof1 = profit_data[True]
        except Exception:
            prof1 = 0
        profit_percent = prof1 / los1
        print(f"Профіт: \n", profit_percent)
    else:
        print("no data")


def reverse_results(df):
    if len(df) > 0:
        for i in range(1, 11):
            new_profit = df.loc[df.index, "is_profit_after_bars_" + str(i)].apply(lambda el: not (bool(el)))
            df.loc[df.index, "is_profit_after_bars_" + str(i)] = new_profit
        return df


def import_dfs(paths, elements_count=-1):
    if elements_count > 0:
        df = pd.read_csv(paths[0]).loc[:elements_count]
    else:
        df = pd.read_csv(paths[0])
    df = df.drop(columns=["Unnamed: 0"])
    for path in paths[1:]:
        if elements_count > 0:
            df = pd.concat([df, pd.read_csv(path).loc[:elements_count]]).reset_index(drop=True)
        else:
            df = pd.concat([df, pd.read_csv(path)]).reset_index(drop=True)
    return df


def get_analzied_df(df):
    def multicolumn_analize(df: pd.DataFrame):
        return_df = pd.DataFrame()

        main_column = "SuperOrderBlock"
        one_of_columns = ["Volume", "UMA", "ScalpPro"]  # "Volume", "UMA", "ScalpPro" "ScalpPro8108", "Volume2", "UMA20", "NW"
        for ind in df.index:
            columns_long_count = 0
            columns_short_count = 0
            for col in one_of_columns:
                df_el = df.loc[ind, col]
                if df_el == LongSignal().type:
                    columns_long_count += 1
                elif df_el == ShortSignal().type:
                    columns_short_count += 1

            counts = [columns_long_count, columns_short_count]
            cols_count = max(counts)
            if cols_count >= 2:
                index = counts.index(cols_count)
                df_el = df.loc[ind, main_column]
                if df_el == ShortSignal().type and index == 1 or df_el == LongSignal().type and index == 0:
                    return_df = pd.concat([return_df, df.loc[ind:ind]])

        # print("проводимо аналіз для індикаторів:", one_of_columns, main_column)
        return return_df

    col = "SuperOrderBlock"
    df_long_old = df[df[col] == LongSignal().type]
    df_short_old = df[df[col] == ShortSignal().type]

    # reverse_results(df_short_old)

    return_df = pd.concat([df_long_old, df_short_old]).reset_index(drop=True)

    return_df = multicolumn_analize(return_df).reset_index(drop=True)

    return return_df


def get_analzied_df_multitimeframe(df, sob_dfs, successful_sob_counts):
    indexes_to_delete = []
    for row_index in df.index:
        sob_count = 0
        _date = datetime.strptime(df.loc[row_index, "datetime"], '%Y-%m-%d %H:%M:%S')
        _date = timedelta(days=_date.day, hours=_date.hour, minutes=_date.minute)
        _date = _date / Timedelta(minutes=1)
        for sob_df_index in range(len(sob_dfs)):
            sob_indexes_to_delete = []
            prev_date_date = None
            prev_date = None
            prev_index = None
            next_date = False
            for sob_df_row_index in sob_dfs[sob_df_index].index:
                if next_date:
                    if sob_dfs[sob_df_index].loc[sob_df_row_index, "SOB_No_Delta"] == df.loc[row_index, "SOB_No_Delta"]:
                        sob_count += 1
                    break
                sob_date = datetime.strptime(sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"],
                                             '%Y-%m-%d %H:%M:%S')
                sob_date = timedelta(days=sob_date.day, hours=sob_date.hour, minutes=sob_date.minute)
                sob_date = sob_date / Timedelta(minutes=1)
                if prev_date is None:
                    prev_date = sob_date
                    prev_date_date = sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"]
                    prev_index = sob_df_row_index
                    continue

                if _date >= prev_date:
                    break

                is_needed_date = sob_date <= _date < prev_date
                if is_needed_date:
                    next_date = True
                else:
                    sob_indexes_to_delete.append(prev_index)
                    prev_index = sob_df_row_index
                    prev_date_date = sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"]
                    prev_date = sob_date

            if len(sob_indexes_to_delete) > 0:
                sob_dfs[sob_df_index] = sob_dfs[sob_df_index].drop(index=sob_indexes_to_delete)

        if sob_count < successful_sob_counts:
            indexes_to_delete.append(row_index)

    print("old ind to del", indexes_to_delete)
    if len(indexes_to_delete) > 0:
        df = df.drop(index=indexes_to_delete)
    return df


def get_analzied_df_multitimeframe_with_dealtime(df, sob_dfs, successful_sob_counts):
    df["dealtime"] = None

    indexes_to_delete = []
    # print(df.to_string())
    for row_index in df.index:
        sob_count = 0
        intervals = []
        _date = datetime.strptime(df.loc[row_index, "datetime"], '%Y-%m-%d %H:%M:%S')
        _date = timedelta(days=_date.day, hours=_date.hour, minutes=_date.minute)
        _date = _date / Timedelta(minutes=1)
        for sob_df_index in range(len(sob_dfs)):
            sob_indexes_to_delete = []
            prev_date_date = None
            prev_date = None
            prev_index = None
            next_date = False
            for sob_df_row_index in sob_dfs[sob_df_index].index:
                if next_date:
                    if sob_dfs[sob_df_index].loc[sob_df_row_index, "SOB_No_Delta"] == df.loc[row_index, "SOB_No_Delta"]:
                        intervals.append(sob_dfs[sob_df_index].loc[sob_df_row_index, "interval"])
                        sob_count += 1
                    break
                sob_date = datetime.strptime(sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"],
                                             '%Y-%m-%d %H:%M:%S')
                sob_date = timedelta(days=sob_date.day, hours=sob_date.hour, minutes=sob_date.minute)
                sob_date = sob_date / Timedelta(minutes=1)
                if prev_date is None:
                    prev_date = sob_date
                    prev_date_date = sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"]
                    prev_index = sob_df_row_index
                    continue

                if _date >= prev_date:
                    break

                is_needed_date = sob_date <= _date < prev_date
                if is_needed_date:
                    next_date = True
                else:
                    sob_indexes_to_delete.append(prev_index)
                    prev_index = sob_df_row_index
                    prev_date_date = sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"]
                    prev_date = sob_date

            if len(sob_indexes_to_delete) > 0:
                sob_dfs[sob_df_index] = sob_dfs[sob_df_index].drop(index=sob_indexes_to_delete)

        if sob_count < successful_sob_counts:
            indexes_to_delete.append(row_index)
            continue
        else:
            # print()
            # print(df.loc[row_index, "symbol"], df.loc[row_index, "interval"], df.loc[row_index, "datetime"])
            # print(intervals)
            interval_minutes = interval_to_int(str_to_interval(df.loc[row_index, "interval"]))
            sum = interval_minutes
            for interval in intervals:
                sum += interval_to_int(str_to_interval(interval))
            sum /= len(intervals)+1
            sum = round(sum/interval_minutes, 0)
            df.loc[row_index, "dealtime"] = int(sum)

    if len(indexes_to_delete) > 0:
        df = df.drop(index=indexes_to_delete)

    return df


paths = [

    ["debug/updated_EURUSD_Intervalin_1_minute.csv",
     "debug/updated_EURUSD_Intervalin_3_minute.csv",
     "debug/updated_EURUSD_Intervalin_5_minute.csv",
     "debug/updated_EURUSD_Intervalin_15_minute.csv",
     "debug/updated_EURUSD_Intervalin_30_minute.csv",
     "debug/updated_EURUSD_Intervalin_45_minute.csv",
     "debug/updated_EURUSD_Intervalin_1_hour.csv",
     "debug/updated_EURUSD_Intervalin_2_hour.csv"],

    ["debug/updated_AUDCAD_Intervalin_1_minute.csv",
     "debug/updated_AUDCAD_Intervalin_3_minute.csv",
     "debug/updated_AUDCAD_Intervalin_5_minute.csv",
     "debug/updated_AUDCAD_Intervalin_15_minute.csv",
     "debug/updated_AUDCAD_Intervalin_30_minute.csv",
     "debug/updated_AUDCAD_Intervalin_45_minute.csv",
     "debug/updated_AUDCAD_Intervalin_1_hour.csv",
     "debug/updated_AUDCAD_Intervalin_2_hour.csv"],

    ["debug/updated_AUDUSD_Intervalin_1_minute.csv",
     "debug/updated_AUDUSD_Intervalin_3_minute.csv",
     "debug/updated_AUDUSD_Intervalin_5_minute.csv",
     "debug/updated_AUDUSD_Intervalin_15_minute.csv",
     "debug/updated_AUDUSD_Intervalin_30_minute.csv",
     "debug/updated_AUDUSD_Intervalin_45_minute.csv",
     "debug/updated_AUDUSD_Intervalin_1_hour.csv",
     "debug/updated_AUDUSD_Intervalin_2_hour.csv"],

    ["debug/updated_EURJPY_Intervalin_1_minute.csv",
     "debug/updated_EURJPY_Intervalin_3_minute.csv",
     "debug/updated_EURJPY_Intervalin_5_minute.csv",
     "debug/updated_EURJPY_Intervalin_15_minute.csv",
     "debug/updated_EURJPY_Intervalin_30_minute.csv",
     "debug/updated_EURJPY_Intervalin_45_minute.csv",
     "debug/updated_EURJPY_Intervalin_1_hour.csv",
     "debug/updated_EURJPY_Intervalin_2_hour.csv"],

    ["debug/updated_EURCAD_Intervalin_1_minute.csv",
     "debug/updated_EURCAD_Intervalin_3_minute.csv",
     "debug/updated_EURCAD_Intervalin_5_minute.csv",
     "debug/updated_EURCAD_Intervalin_15_minute.csv",
     "debug/updated_EURCAD_Intervalin_30_minute.csv",
     "debug/updated_EURCAD_Intervalin_45_minute.csv",
     "debug/updated_EURCAD_Intervalin_1_hour.csv",
     "debug/updated_EURCAD_Intervalin_2_hour.csv"],

    ["debug/updated_AUDCHF_Intervalin_1_minute.csv",
     "debug/updated_AUDCHF_Intervalin_3_minute.csv",
     "debug/updated_AUDCHF_Intervalin_5_minute.csv",
     "debug/updated_AUDCHF_Intervalin_15_minute.csv",
     "debug/updated_AUDCHF_Intervalin_30_minute.csv",
     "debug/updated_AUDCHF_Intervalin_45_minute.csv",
     "debug/updated_AUDCHF_Intervalin_1_hour.csv",
     "debug/updated_AUDCHF_Intervalin_2_hour.csv"],

    ["debug/updated_GBPUSD_Intervalin_1_minute.csv",
     "debug/updated_GBPUSD_Intervalin_3_minute.csv",
     "debug/updated_GBPUSD_Intervalin_5_minute.csv",
     "debug/updated_GBPUSD_Intervalin_15_minute.csv",
     "debug/updated_GBPUSD_Intervalin_30_minute.csv",
     "debug/updated_GBPUSD_Intervalin_45_minute.csv",
     "debug/updated_GBPUSD_Intervalin_1_hour.csv",
     "debug/updated_GBPUSD_Intervalin_2_hour.csv"],

    ["debug/updated_AUDJPY_Intervalin_1_minute.csv",
     "debug/updated_AUDJPY_Intervalin_3_minute.csv",
     "debug/updated_AUDJPY_Intervalin_5_minute.csv",
     "debug/updated_AUDJPY_Intervalin_15_minute.csv",
     "debug/updated_AUDJPY_Intervalin_30_minute.csv",
     "debug/updated_AUDJPY_Intervalin_45_minute.csv",
     "debug/updated_AUDJPY_Intervalin_1_hour.csv",
     "debug/updated_AUDJPY_Intervalin_2_hour.csv"],

    ["debug/updated_GBPAUD_Intervalin_1_minute.csv",
     "debug/updated_GBPAUD_Intervalin_3_minute.csv",
     "debug/updated_GBPAUD_Intervalin_5_minute.csv",
     "debug/updated_GBPAUD_Intervalin_15_minute.csv",
     "debug/updated_GBPAUD_Intervalin_30_minute.csv",
     "debug/updated_GBPAUD_Intervalin_45_minute.csv",
     "debug/updated_GBPAUD_Intervalin_1_hour.csv",
     "debug/updated_GBPAUD_Intervalin_2_hour.csv"]
]
# currencies = price_parser.get_currencies()
# intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute,
#              Interval.in_30_minute, Interval.in_45_minute, Interval.in_1_hour, Interval.in_2_hour]
#
# for path_arr_ind in range(len(paths)):
#     curr = currencies[path_arr_ind]
#     for ind in range(len(paths[path_arr_ind])):
#         interval = intervals[ind]
#         path_save = paths[path_arr_ind][ind]
#         df_save = import_dfs([path_save])
#
#         df_save["interval"] = interval
#         df_save["symbol"] = curr[0]
#         df_save.to_csv(path_save)


result_dfs_old = pd.DataFrame()
result_dfs_new = []
for path_arr in paths:
    for ind in range(len(path_arr)-5):
        df = import_dfs([path_arr[ind]])
        sob_dfs = []
        df_analized = get_analzied_df(df)
        df_analized = df_analized.sort_values("datetime", ascending=False).reset_index(drop=True)
        for sob_count in range(5):
            result_dfs_new.append(pd.DataFrame())
            for k in range(ind+1, len(path_arr)-3):
                sob_dfs.append(import_dfs(path_arr[k:k+1]))
            df_analized_mtf = get_analzied_df_multitimeframe_with_dealtime(df_analized, sob_dfs, sob_count)
            result_dfs_new[sob_count] = pd.concat([result_dfs_new[sob_count], df_analized_mtf]).reset_index(drop=True)

for sob_count in range(5):
    result_dfs_new[sob_count] = result_dfs_new[sob_count].sort_values("datetime").reset_index(drop=True)
    result_dfs_new[sob_count]["profit_dealtime"] = None
    result_dfs_new[sob_count]["profit_dealtime_6"] = None
    for el_index in result_dfs_new[sob_count].index:
        path = f"debug/updated_{result_dfs_new[sob_count].loc[el_index, 'symbol']}_{interval_to_string(str_to_interval(result_dfs_new[sob_count].loc[el_index, 'interval']))}.csv"
        df_new_analize_half = import_dfs([path])
        deal_time = int(result_dfs_new[sob_count].loc[el_index, "dealtime"])

        index = df_new_analize_half.index[result_dfs_new[sob_count].loc[el_index, "datetime"] == df_new_analize_half["datetime"]].values[0] - deal_time
        index_6 = df_new_analize_half.index[result_dfs_new[sob_count].loc[el_index, "datetime"] == df_new_analize_half["datetime"]].values[0] - 6

        signal = get_signal_by_type(result_dfs_new[sob_count].loc[el_index, "SuperOrderBlock"])
        open_price = result_dfs_new[sob_count].loc[el_index, "close_price"]

        if index >= 0:
            close_price = df_new_analize_half.loc[index, "close_price"]
            result_dfs_new[sob_count].loc[el_index, "profit_dealtime"] = signal.is_profit(open_price, close_price)
        if index_6 >= 0:
            close_price_6 = df_new_analize_half.loc[index_6, "close_price"]
            result_dfs_new[sob_count].loc[el_index, "profit_dealtime_6"] = signal.is_profit(open_price, close_price_6)

    print("\nSOB count", sob_count)
    income_percent(result_dfs_new[sob_count], "profit_dealtime")
    income_percent(result_dfs_new[sob_count], "profit_dealtime_6")
