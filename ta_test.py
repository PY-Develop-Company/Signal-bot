import time
from _operator import index

import tradingview_ta
import pandas as pd
from pandas import Timedelta
from signals import *
from datetime import timedelta, datetime


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


def income_percent(df):
    if len(df) > 0:
        for i in range(2, 11):
            print("Кількість угод в новій стратегії:", len(df.index))
            profit_data = df["is_profit_after_bars_" + str(i)].value_counts()
            profit_percent = profit_data[True] / profit_data[False]
            print(f" Час угоди {i} свічок \n")
            print(f"Профіт: {i}\n", profit_percent)
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
    # df = df.reset_index(drop=True)
    df = df.drop(columns=["Unnamed: 0"])
    for path in paths[1:]:
        if elements_count > 0:
            df = pd.concat([df, pd.read_csv(path).loc[:elements_count]])
        else:
            df = pd.concat([df, pd.read_csv(path)]).reset_index(drop=True)
    return df


def get_analzied_df(df):
    def test(df: pd.DataFrame):
        return_df = pd.DataFrame(columns=df.columns)
        df = df.reset_index(drop=True)
        print(len(df))
        columns = ["SuperOrderBlock"]
        one_of_columns = ["Volume", "UMA", "ScalpPro"]
        i = 0
        for ind in df.index:
            # print("analize loop", i)
            i += 1
            columns_long_count = 0
            columns_short_count = 0
            for col in one_of_columns:
                if (df.loc[ind, col] == LongSignal().type):
                    columns_long_count += 1
                elif (df.loc[ind, col] == ShortSignal().type):
                    columns_short_count += 1

            counts = [columns_long_count, columns_short_count]
            cols_count = max(counts)
            if cols_count >= 2:
                index = counts.index(cols_count)
                if len(columns) > 0:
                    if df.loc[ind, columns[0]] == ShortSignal().type and index == 1 or \
                            df.loc[ind, columns[0]] == LongSignal().type and index == 0:
                        return_df = pd.concat([return_df, df.iloc[ind:ind + 1]])
                else:
                    return_df = pd.concat([return_df, df.iloc[ind:ind + 1]])

        print("проводимо аналіз для індикаторів:", one_of_columns, columns)
        return return_df

    columns = ["SuperOrderBlock"]
    print("Аналіз для індикаторів: ", columns)
    df_long_old = df
    df_short_old = df
    for col in columns:
        df_long_old = df_long_old.loc[(df_long_old[col] == LongSignal().type)]
        df_short_old = df_short_old.loc[(df_short_old[col] == ShortSignal().type)]

    df_short_old = reverse_results(df_short_old)
    df = pd.concat([df_long_old, df_short_old])

    # df = test(df)

    return df.reset_index(drop=True)


def get_analzied_df_multitimeframe(df, sob_dfs, successful_sob_counts):
    # df = get_analzied_df(df)
    indexes_to_delete = []
    for row_index in df.index:
        sob_count = 0
        # print(df.loc[row_index, "datetime"])
        _date = datetime.strptime(df.loc[row_index, "datetime"], '%Y-%m-%d %H:%M:%S')
        _date = timedelta(days=_date.day, hours=_date.hour, minutes=_date.minute)
        _date = _date / Timedelta(minutes=1)
        # print(_date)
        for sob_df_index in range(len(sob_dfs)):
            sob_indexes_to_delete = []
            prev_date_date = None
            prev_date = None
            prev_index = None
            next_date = False
            for sob_df_row_index in sob_dfs[sob_df_index].index:
                if next_date:
                    # print("origin my date:", df.loc[row_index, "datetime"])
                    # print("my date:", sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"])
                    # print("prev date:", prev_date_date)
                    # print(f"needed date\n")
                    if sob_dfs[sob_df_index].loc[sob_df_row_index, "SuperOrderBlock"] == df.loc[
                        row_index, "SuperOrderBlock"]:
                        sob_count += 1
                    break
                sob_date = datetime.strptime(sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"], '%Y-%m-%d %H:%M:%S')
                sob_date = timedelta(days=sob_date.day, hours=sob_date.hour, minutes=sob_date.minute)
                sob_date = sob_date / Timedelta(minutes=1)
                if prev_date is None:
                    # print("set prev_date")
                    prev_date = sob_date
                    prev_date_date = sob_dfs[sob_df_index].loc[sob_df_row_index, "datetime"]
                    prev_index = sob_df_row_index
                    continue

                if _date >= prev_date:
                    # print("prev_date it too big\n")
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

        # print(f" {row_index} sob_count", sob_count)
        if sob_count < successful_sob_counts:
            indexes_to_delete.append(row_index)

    if len(indexes_to_delete) > 0:
        df = df.drop(index=indexes_to_delete)
    return df


def compare():
    paths = [
        "debug/new_extra/AUDUSD_Intervalin_1_minute.csv",
        "debug/new_extra/AUDUSD_Intervalin_3_minute.csv",
        "debug/new_extra/AUDUSD_Intervalin_5_minute.csv",
        "debug/new_extra/AUDUSD_Intervalin_15_minute.csv",
        "debug/new_extra/AUDUSD_Intervalin_30_minute.csv",

        "debug/new_extra/AUDCAD_Intervalin_1_minute.csv",
        "debug/new_extra/AUDCAD_Intervalin_3_minute.csv",
        "debug/new_extra/AUDCAD_Intervalin_5_minute.csv",
        "debug/new_extra/AUDCAD_Intervalin_15_minute.csv",
        "debug/new_extra/AUDCAD_Intervalin_30_minute.csv",

        "debug/new_extra/EURJPY_Intervalin_1_minute.csv",
        "debug/new_extra/EURJPY_Intervalin_3_minute.csv",
        "debug/new_extra/EURJPY_Intervalin_5_minute.csv",
        "debug/new_extra/EURJPY_Intervalin_15_minute.csv",
        "debug/new_extra/EURJPY_Intervalin_30_minute.csv"
    ]
    df = import_dfs(paths)

    print("==============\n\n\n")

    paths = [
        "debug/new_clasic/AUDUSD_Intervalin_1_minute.csv",
        "debug/new_clasic/AUDUSD_Intervalin_3_minute.csv",
        "debug/new_clasic/AUDUSD_Intervalin_5_minute.csv",
        "debug/new_clasic/AUDUSD_Intervalin_15_minute.csv",
        "debug/new_clasic/AUDUSD_Intervalin_30_minute.csv",

        "debug/new_clasic/AUDCAD_Intervalin_1_minute.csv",
        "debug/new_clasic/AUDCAD_Intervalin_3_minute.csv",
        "debug/new_clasic/AUDCAD_Intervalin_5_minute.csv",
        "debug/new_clasic/AUDCAD_Intervalin_15_minute.csv",
        "debug/new_clasic/AUDCAD_Intervalin_30_minute.csv",

        "debug/new_clasic/EURJPY_Intervalin_1_minute.csv",
        "debug/new_clasic/EURJPY_Intervalin_3_minute.csv",
        "debug/new_clasic/EURJPY_Intervalin_5_minute.csv",
        "debug/new_clasic/EURJPY_Intervalin_15_minute.csv",
        "debug/new_clasic/EURJPY_Intervalin_30_minute.csv"
    ]
    df_old = import_dfs(paths)
    df_old_changed = import_dfs(paths)
    print(len(df_old_changed))

    df["Volume"] = df_old["Volume"]
    df = get_analzied_df(df)
    df_old = get_analzied_df(df_old)

    income_percent_diff(df, df_old)


# paths = [
#     "debug/clasic_AUDCAD_Intervalin_1_minute.csv",
#     "debug/clasic_AUDCAD_Intervalin_5_minute.csv",
#     "debug/clasic_AUDCAD_Intervalin_15_minute.csv",
#     "debug/clasic_AUDUSD_Intervalin_1_minute.csv",
#     "debug/clasic_AUDUSD_Intervalin_5_minute.csv",
#     "debug/clasic_AUDUSD_Intervalin_15_minute.csv",
#     "debug/clasic_EURJPY_Intervalin_1_minute.csv",
#     "debug/clasic_EURJPY_Intervalin_5_minute.csv",
#     "debug/clasic_EURJPY_Intervalin_15_minute.csv"
# ]
#
# df = import_dfs(paths)
#
# columns = ["SuperOrderBlock", "ScalpPro", "Volume", "ScalpPro", "NW"]
# df_long_old = df
# df_short_old = df
# for col in columns:
#     df_long_old = df_long_old.loc[(df_long_old[col] == LongSignal().type)]
#     df_short_old = df_short_old.loc[(df_short_old[col] == ShortSignal().type)]
#
# df_short_old = reverse_results(df_short_old)
# df = pd.concat([df_long_old, df_short_old])
#
# income_percent(df)

# compare()


paths_clasic = [
    # ["debug/clasic/clasic_AUDUSD_Intervalin_1_minute.csv",
    # "debug/clasic/clasic_AUDUSD_Intervalin_5_minute.csv",
    # "debug/clasic/clasic_AUDUSD_Intervalin_15_minute.csv"],
    # ["debug/clasic/clasic_AUDCAD_Intervalin_1_minute.csv",
    #  "debug/clasic/clasic_AUDCAD_Intervalin_5_minute.csv",
    #  "debug/clasic/clasic_AUDCAD_Intervalin_15_minute.csv"],
    # ["debug/clasic/clasic_EURJPY_Intervalin_1_minute.csv",
    #  "debug/clasic/clasic_EURJPY_Intervalin_5_minute.csv",
    #  "debug/clasic/clasic_EURJPY_Intervalin_15_minute.csv"]



    ["debug/new_clasic/AUDUSD_Intervalin_1_minute.csv",
    "debug/new_clasic/AUDUSD_Intervalin_3_minute.csv",
    "debug/new_clasic/AUDUSD_Intervalin_5_minute.csv",
    "debug/new_clasic/AUDUSD_Intervalin_15_minute.csv",
    "debug/new_clasic/AUDUSD_Intervalin_30_minute.csv"],

    ["debug/new_clasic/AUDCAD_Intervalin_1_minute.csv",
     "debug/new_clasic/AUDCAD_Intervalin_3_minute.csv",
     "debug/new_clasic/AUDCAD_Intervalin_5_minute.csv",
     "debug/new_clasic/AUDCAD_Intervalin_15_minute.csv",
     "debug/new_clasic/AUDCAD_Intervalin_30_minute.csv"],

    ["debug/new_clasic/EURJPY_Intervalin_1_minute.csv",
     "debug/new_clasic/EURJPY_Intervalin_3_minute.csv",
     "debug/new_clasic/EURJPY_Intervalin_5_minute.csv",
     "debug/new_clasic/EURJPY_Intervalin_15_minute.csv",
     "debug/new_clasic/EURJPY_Intervalin_30_minute.csv"]
]
# print(import_dfs(paths)["SuperOrderBlock"].value_counts())
paths_extra = [
    # ["debug/5000extra/AUDUSD_Intervalin_1_minute.csv",
    # "debug/5000extra/AUDUSD_Intervalin_5_minute.csv",
    # "debug/5000extra/AUDUSD_Intervalin_15_minute.csv"],
    # ["debug/5000extra/AUDCAD_Intervalin_1_minute.csv",
    #  "debug/5000extra/AUDCAD_Intervalin_5_minute.csv",
    #  "debug/5000extra/AUDCAD_Intervalin_15_minute.csv"],
    # ["debug/5000extra/EURJPY_Intervalin_1_minute.csv",
    #  "debug/5000extra/EURJPY_Intervalin_5_minute.csv",
    #  "debug/5000extra/EURJPY_Intervalin_15_minute.csv"]



    ["debug/new_extra/AUDUSD_Intervalin_1_minute.csv",
    "debug/new_extra/AUDUSD_Intervalin_3_minute.csv",
    "debug/new_extra/AUDUSD_Intervalin_5_minute.csv",
    "debug/new_extra/AUDUSD_Intervalin_15_minute.csv",
    "debug/new_extra/AUDUSD_Intervalin_30_minute.csv"],

    ["debug/new_extra/AUDCAD_Intervalin_1_minute.csv",
    "debug/new_extra/AUDCAD_Intervalin_3_minute.csv",
    "debug/new_extra/AUDCAD_Intervalin_5_minute.csv",
    "debug/new_extra/AUDCAD_Intervalin_15_minute.csv",
    "debug/new_extra/AUDCAD_Intervalin_30_minute.csv"],

    ["debug/new_extra/EURJPY_Intervalin_1_minute.csv",
    "debug/new_extra/EURJPY_Intervalin_3_minute.csv",
    "debug/new_extra/EURJPY_Intervalin_5_minute.csv",
    "debug/new_extra/EURJPY_Intervalin_15_minute.csv",
    "debug/new_extra/EURJPY_Intervalin_30_minute.csv"]
]
# print(import_dfs(paths)["SuperOrderBlock"].value_counts())

# path = paths_extra[0]
#
# df_new = import_dfs(paths_clasic[0][0:1])
#
# df = import_dfs(path[0:1])
# dfs = [import_dfs(path[1:2]), import_dfs(path[2:3])]
#
# df["Volume"] = df_new["Volume"]
# # df["UMA"] = df_new["UMA"]
# df = get_analzied_df(df)
# df_sob = get_analzied_df_multitimeframe(df, dfs, 1)
#
# income_percent_diff(df, df_sob)


base_dfs = pd.DataFrame()
new_dfs = pd.DataFrame()
for i in range(len(paths_clasic)):
    for j in range(len(paths_clasic[i])-2):
        path = paths_extra[i]

        df_new = import_dfs(paths_clasic[i][j:j+1])

        df = import_dfs(path[j:j + 1])
        dfs = []
        for k in range(j+1, len(paths_clasic[i])):
            dfs.append(import_dfs(path[k:k+1]))

        # df["SuperOrderBlock"] = df_new["SuperOrderBlock"]
        # df["Volume"] = df_new["Volume"]
        df = get_analzied_df(df)
        base_dfs = pd.concat([base_dfs, df]).reset_index(drop=True)
        df_sob = get_analzied_df_multitimeframe(df, dfs, 2)
        new_dfs = pd.concat([new_dfs, df_sob]).reset_index(drop=True)

income_percent_diff(new_dfs, base_dfs)