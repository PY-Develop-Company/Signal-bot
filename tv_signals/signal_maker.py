import time
from datetime import datetime
from icecream import ic

from tv_signals.price_updater import FCSForexPriceUpdater
from tv_signals.analizer import NewMultitimeframeAnalizer
from tv_signals.analized_signals_table import AnalyzedSignalsTable
from tv_signals.signal_types import *

from utils import interval_convertor
from utils.time import origin_date, now_time

from pandas import Timedelta
from tv_signals.interval import Interval as MyInterval
import asyncio

from my_debuger import debug_info

signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: MyInterval, bars_count=3):
    delay_seconds = interval_convertor.my_interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price_original, signal: Signal, pd: PriceData, bars_count, price_updater: FCSForexPriceUpdater):
    open_price, open_price_date = price_updater.latest_price_and_date(pd.symbol)

    await close_position_delay(MyInterval.in_1_minute, bars_count)

    close_price, close_price_date = price_updater.latest_price_and_date(pd.symbol)
    print("closing_position", open_price, open_price_date, close_price, close_price_date)
    msg, is_profit_position = signal.get_close_position_signal_message(pd, open_price, close_price, bars_count)
    return msg, is_profit_position, open_price, close_price, open_price_date, close_price_date


def analyze_currency_data_controller(analyze_pair, lock):
    try:
        main_pd = analyze_pair.main_pd
        all_pds = analyze_pair.get_all_pds()

        lock.acquire()
        main_price_df = main_pd.get_saved_chart_data(5000)
        all_dfs = [pd.get_saved_chart_data(5000) for pd in analyze_pair.get_all_pds()]
        lock.release()

        start_analyze_time = now_time()  # main_price_df.iloc[0].loc["download_time"]

        analyzer = NewMultitimeframeAnalizer(1, 1)
        lock.acquire()
        has_signal, signal, debug, deal_time = analyzer.analize(all_dfs, all_pds)
        open_position_price = main_pd.get_saved_chart_data(bars_count=1).iloc[0].loc["close"]
        lock.release()

        msg = signal.get_open_msg_text(main_pd, deal_time)

        AnalyzedSignalsTable.add_analyzed_signal(main_pd, main_price_df["datetime"][0], has_signal, signal.type,
                                                 deal_time, open_position_price, msg, start_analyze_time)
        debug_info(f"analyzed {[main_pd.symbol, main_pd.exchange, main_pd.interval]}")
    except Exception as e:
        print(e)
