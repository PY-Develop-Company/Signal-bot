import tradingview_ta
import pandas as pd

df = pd.read_csv("debug/EURUSDIntervalin_15_minute_indicators_count_4deal_time3.csv")
print(df)
print("1 хвилина:\n", df["is_profit"].value_counts())


df = pd.read_csv("debug/EURUSDIntervalin_5_minute_indicators_count_4deal_time3.csv")
print("5 хвилин:\n", df["is_profit"].value_counts())


df = pd.read_csv("debug/EURUSDIntervalin_15_minute_indicators_count_4deal_time3.csv")
print("15 хвилин:\n", df["is_profit"].value_counts())
