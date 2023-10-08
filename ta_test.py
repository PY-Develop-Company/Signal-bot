import tradingview_ta
import pandas as pd
from signals import *

audcad_df_1min = pd.read_csv("debug/clasic_AUDCAD_Intervalin_1_minute.csv")
audcad_df_5min = pd.read_csv("debug/clasic_AUDCAD_Intervalin_5_minute.csv")
audcad_df_15min = pd.read_csv("debug/clasic_AUDCAD_Intervalin_15_minute.csv")

audusd_df_1min = pd.read_csv("debug/clasic_AUDUSD_Intervalin_1_minute.csv")
audusd_df_5min = pd.read_csv("debug/clasic_AUDUSD_Intervalin_5_minute.csv")
audusd_df_15min = pd.read_csv("debug/clasic_AUDUSD_Intervalin_15_minute.csv")

eurjpy_df_1min = pd.read_csv("debug/clasic_EURJPY_Intervalin_1_minute.csv")
eurjpy_df_5min = pd.read_csv("debug/clasic_EURJPY_Intervalin_5_minute.csv")
eurjpy_df_15min = pd.read_csv("debug/clasic_EURJPY_Intervalin_15_minute.csv")

# df = pd.concat([audcad_df_1min, eurjpy_df_1min, audusd_df_1min])

df = pd.concat([audcad_df_1min, audcad_df_5min, audcad_df_15min, eurjpy_df_1min, eurjpy_df_5min, eurjpy_df_15min, audusd_df_1min, audusd_df_5min, audusd_df_15min])
df_long = df.loc[(df["NW"] == LongSignal().type) & (df["SuperOrderBlock"] == LongSignal().type)]
df_short = df.loc[(df["NW"] == ShortSignal().type) & (df["SuperOrderBlock"] == ShortSignal().type)]

# df_long = df.loc[(df["Volume"] == LongSignal().type) & (df["NW"] == LongSignal().type) & (df["UMA"] == LongSignal().type) & (df["ScalpPro"] == LongSignal().type)]
# df_short = df.loc[(df["Volume"] == ShortSignal().type) & (df["NW"] == ShortSignal().type) & (df["UMA"] == ShortSignal().type) & (df["ScalpPro"] == ShortSignal().type)]
if len(df_short) > 0:
    for i in range(1, 11):
        new_profit = df_short["is_profit_after_bars_" + str(i)].apply(lambda el: not(bool(el)))
        df_short["is_profit_after_bars_" + str(i)] = new_profit

df = pd.concat([df_long, df_short])
if len(df) > 0:
    for i in range(1, 11):
        print(f"Long 1 хвилина: {i}\n", df["is_profit_after_bars_" + str(i)].value_counts())
else:
    print("no data")