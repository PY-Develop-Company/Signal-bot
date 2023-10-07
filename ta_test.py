import tradingview_ta
import pandas as pd

df = pd.read_csv("debug/AUDCADIntervalin_1_minute_indicators_count_3deal_time3.csv")
print("1 хвилина:\n", df["is_profit"].value_counts())


df = pd.read_csv("debug/AUDCADIntervalin_5_minute_indicators_count_3deal_time3.csv")
print("5 хвилин:\n", df["is_profit"].value_counts())


df = pd.read_csv("debug/AUDCADIntervalin_15_minute_indicators_count_3deal_time3.csv")
print("15 хвилин:\n", df["is_profit"].value_counts())
