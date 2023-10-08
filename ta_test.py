import tradingview_ta
import pandas as pd
from signals import *

df_1min = pd.read_csv("debug/1000/_EURUSDIntervalin_1_minute_indicators_count_4.csv")
df_5min = pd.read_csv("debug/1000/_EURUSDIntervalin_5_minute_indicators_count_4.csv")
df_15min = pd.read_csv("debug/1000/_EURUSDIntervalin_15_minute_indicators_count_4.csv")

df = pd.concat([df_1min, df_5min, df_15min])
df_long = df.loc[(df["SuperOrderBlock"] == LongSignal().type)]
df_short = df.loc[(df["SuperOrderBlock"] == ShortSignal().type)]

# df_long = df.loc[(df["Volume"] == LongSignal().type) & (df["NW"] == LongSignal().type) & (df["UMA"] == LongSignal().type) & (df["ScalpPro"] == LongSignal().type)]
# df_short = df.loc[(df["Volume"] == ShortSignal().type) & (df["NW"] == ShortSignal().type) & (df["UMA"] == ShortSignal().type) & (df["ScalpPro"] == ShortSignal().type)]
if len(df_short) > 0:
    for i in range(1, 11):
        # not(bool(row[]))
        new_profit = df_short["is_profit_after_bars_" + str(i)].apply(lambda el: not(bool(el)))
        df_short["is_profit_after_bars_" + str(i)] = new_profit

df = pd.concat([df_long, df_short])
if len(df) > 0:
    for i in range(1, 11):
        print(f"Long 1 хвилина: {i}\n", df["is_profit_after_bars_" + str(i)].value_counts())
else:
    print("no data")