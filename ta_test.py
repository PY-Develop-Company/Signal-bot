import tradingview_ta
import pandas as pd
from signals import *

df_1min = pd.read_csv("debug/EURUSDIntervalin_1_minute_indicators_count_4.csv")
df_5min = pd.read_csv("debug/EURUSDIntervalin_5_minute_indicators_count_4.csv")
df_15min = pd.read_csv("debug/EURUSDIntervalin_15_minute_indicators_count_4.csv")

df = pd.concat([df_15min])
df_long = df[df["SuperOrderBlock"] == LongSignal().type]
df_short = df[df["SuperOrderBlock"] == ShortSignal().type]
for i in range(1, 11):
    # not(bool(row[]))
    new_profit = df_short["is_profit_after_bars_" + str(i)].apply(lambda el: not(bool(el)))
    df_short["is_profit_after_bars_" + str(i)] = new_profit

df = pd.concat([df_long, df_short])
for i in range(1, 11):
    print(f"Long 1 хвилина: {i}\n", df["is_profit_after_bars_" + str(i)].value_counts())
