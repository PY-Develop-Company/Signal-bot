import time

import tradingview_ta
import pandas as pd
from signals import *


def income_percent_diff(df1, df2):
    if len(df1) > 0 and len(df2) > 0:
        for i in range(3, 4):
            print("df1", df1.shape)
            print("df2", df2.shape)
            profit_data_1 = df1["is_profit_after_bars_" + str(i)].value_counts()
            profit_data_2 = df2["is_profit_after_bars_" + str(i)].value_counts()
            profit_percent_1 = profit_data_1[True] / profit_data_1[False] * 100
            profit_percent_2 = profit_data_2[True] / profit_data_2[False] * 100
            print(f" Барів {i} Різниця профіту:\n", profit_percent_1 - profit_percent_2)
            print(f" Профіт 1:\n", profit_percent_1)
            print(f" Профіт 2:\n", profit_percent_2, "\n")
    else:
        print("no data")


def income_percent(df):
    if len(df) > 0:
        for i in range(2, 11):
            profit_data = df["is_profit_after_bars_" + str(i)].value_counts()
            profit_percent = profit_data[True] / profit_data[False] * 100
            print(f"Профіт: {i}\n", profit_percent)
    else:
        print("no data")


def reverse_results(df):
    if len(df) > 0:
        for i in range(1, 11):
            new_profit = df["is_profit_after_bars_" + str(i)].apply(lambda el: not (bool(el)))
            df["is_profit_after_bars_" + str(i)] = new_profit
        return df


def import_dfs(paths, elements_count=-1):
    if elements_count > 0:
        df = pd.read_csv(paths[0]).loc[:elements_count]
    else:
        df = pd.read_csv(paths[0])
    for path in paths[1:]:
        if elements_count > 0:
            df = pd.concat([df, pd.read_csv(path).loc[:elements_count]])
        else:
            df = pd.concat([df, pd.read_csv(path)])
    return df


def get_analzied_df(df):
    def test(df: pd.DataFrame):
        return_df = pd.DataFrame(columns=df.columns)
        df = df.reset_index()
        df = df.drop(columns=["Unnamed: 0", "index"])
        # print(df)
        for ind in df.index:
            columns = ["SuperOrderBlock"]
            one_of_columns = ["Volume", "ScalpPro", "UMA", "NW"]
            columns_long_count = 0
            columns_short_count = 0
            for col in one_of_columns:
                if (df.loc[ind, col] == LongSignal().type):
                    columns_long_count += 1
                elif (df.loc[ind, col] == ShortSignal().type):
                    columns_short_count += 1

            counts = [columns_long_count, columns_short_count]
            cols_count = max(counts)
            if cols_count > 2:
                index = counts.index(cols_count)
                if df.loc[ind, columns[0]] == ShortSignal().type and index == 1 or \
                        df.loc[ind, columns[0]] == LongSignal().type and index == 0:
                    return_df = pd.concat([return_df, df.iloc[ind:ind+1]])

        return_df = return_df.drop(columns=["Unnamed: 0"])
        return return_df

    columns = ["SuperOrderBlock"]
    df_long_old = df
    df_short_old = df
    for col in columns:
        df_long_old = df_long_old.loc[(df_long_old[col] == LongSignal().type)]
        df_short_old = df_short_old.loc[(df_short_old[col] == ShortSignal().type)]

    df_short_old = reverse_results(df_short_old)
    df = pd.concat([df_long_old, df_short_old])

    df = test(df)

    return df




def compare():
    paths = [
        "debug/AUDUSD_Intervalin_1_minute.csv",
        "debug/AUDUSD_Intervalin_5_minute.csv",
        "debug/AUDUSD_Intervalin_15_minute.csv",
        "debug/EURJPY_Intervalin_1_minute.csv",
        "debug/EURJPY_Intervalin_5_minute.csv",
        "debug/EURJPY_Intervalin_15_minute.csv"
    ]
    df = import_dfs(paths)

    print("==============\n\n\n")

    paths = [
        "debug/clasic_AUDUSD_Intervalin_1_minute.csv",
        "debug/clasic_AUDUSD_Intervalin_5_minute.csv",
        "debug/clasic_AUDUSD_Intervalin_15_minute.csv",
        "debug/clasic_EURJPY_Intervalin_1_minute.csv",
        "debug/clasic_EURJPY_Intervalin_5_minute.csv",
        "debug/clasic_EURJPY_Intervalin_15_minute.csv"
    ]
    df_old = import_dfs(paths, 1489)
    df_old["ScalpPro"] = df["ScalpPro"]
    df_old["Volume"] = df["Volume"]
    # df_old["NW"] = df["NW"]
    df_old["UMA"] = df["UMA"]
    df_old = get_analzied_df(df_old)
    df_old_full = get_analzied_df(import_dfs(paths))

    # print(df_old.to_string())
    # income_percent_diff(df, df_old)
    income_percent_diff(df_old, df_old_full)

paths = [
    "debug/clasic_AUDCAD_Intervalin_1_minute.csv",
    "debug/clasic_AUDCAD_Intervalin_5_minute.csv",
    "debug/clasic_AUDCAD_Intervalin_15_minute.csv",
    "debug/clasic_AUDUSD_Intervalin_1_minute.csv",
    "debug/clasic_AUDUSD_Intervalin_5_minute.csv",
    "debug/clasic_AUDUSD_Intervalin_15_minute.csv",
    "debug/clasic_EURJPY_Intervalin_1_minute.csv",
    "debug/clasic_EURJPY_Intervalin_5_minute.csv",
    "debug/clasic_EURJPY_Intervalin_15_minute.csv"
]

df = import_dfs(paths)

columns = ["SuperOrderBlock", "ScalpPro", "Volume", "ScalpPro", "NW"]
df_long_old = df
df_short_old = df
for col in columns:
    df_long_old = df_long_old.loc[(df_long_old[col] == LongSignal().type)]
    df_short_old = df_short_old.loc[(df_short_old[col] == ShortSignal().type)]

df_short_old = reverse_results(df_short_old)
df = pd.concat([df_long_old, df_short_old])

income_percent(df)