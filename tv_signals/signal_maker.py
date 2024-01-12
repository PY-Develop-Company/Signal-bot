from datetime import datetime

from tv_signals.analizer import NewMultitimeframeAnalizer
from tv_signals.analized_signals_table import AnalyzedSignalsTable
from tv_signals.signal_types import *

from utils import interval_convertor
from utils.time import origin_date

from pandas import Timedelta
from tvDatafeed import Interval
import asyncio

from my_debuger import debug_tv_data_feed, debug_temp, debug_info

signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: Interval, bars_count=3):
    delay_seconds = interval_convertor.interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price_original, signal: Signal, pd: PriceData, bars_count):
    position_open_price = pd.get_price_data(bars_count=2)

    open_price = position_open_price_original if position_open_price is None else position_open_price.close[0]
    open_price_date = origin_date if position_open_price is None else position_open_price.datetime[0]

    await close_position_delay(Interval.in_1_minute, bars_count)

    price_data = pd.get_price_data(bars_count=2)
    close_price = position_open_price_original if price_data is None else price_data.close[0]
    close_price_date = origin_date if price_data is None else price_data.datetime[0]

    msg, is_profit_position = signal.get_close_position_signal_message(pd, open_price, close_price, bars_count)
    return msg, is_profit_position, open_price, close_price, open_price_date, close_price_date


def is_all_charts_collected(main_pd: PriceData, parent_pds: [PriceData]):
    expected_bars = []
    real_bars = []

    main_df = main_pd.get_chart_data_if_exists()
    if main_df is None:
        return False
    main_df_last_bar_checked = main_df["datetime"][0]

    expected_bars.append(main_df_last_bar_checked)
    real_bars.append(main_df_last_bar_checked)
    res = True
    for parent_pd in parent_pds:
        parent_df = parent_pd.get_chart_data_if_exists()
        if parent_df is None:
            res = False
            break
        parent_df_last_bar_checked = parent_df["datetime"][0]
        needed_bar = parent_pd.get_needed_chart_bar_to_analize(main_df_last_bar_checked, main_pd.interval)

        real_bars.append(parent_df_last_bar_checked)
        expected_bars.append(needed_bar)
        if not (parent_df_last_bar_checked == needed_bar):
            res = False
            break
    # debug_info(f"{real_bars} {expected_bars}")
    return res


def analize_currency_data_controller(analize_pds, additional_pds):
    async def analize_currency_data_function(check_pds: [PriceData], additional_pds):
        main_pd = check_pds[0]
        start_analize_time = check_pds[0].get_chart_download_time()

        if not is_all_charts_collected(check_pds[0], check_pds[1:]):
            return

        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        prices_dfs = []
        for pd in check_pds:
            ch_data = pd.get_chart_data_if_exists()
            if ch_data is None:
                continue
            prices_dfs.append(ch_data)

        analizer = NewMultitimeframeAnalizer(1, 1)
        has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)
        has_signal = True
        signal = LongSignal()
        deal_time = 3

        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd, deal_time)
        
        AnalyzedSignalsTable.add_analyzed_signal(main_pd, main_price_df.datetime[0], has_signal, signal.type,
                                                 deal_time, open_position_price, msg, start_analize_time)

        # debug_tv_data_feed(f"Created signal file {msg} {main_price_df.datetime[0]}")

    async def analize_currency_data_loop(analize_pds, additional_pds):
        while True:
            debug_temp(f"analize_loop")
            tasks = []
            for i in range(len(analize_pds)):
                task = asyncio.create_task(analize_currency_data_function(analize_pds[i], additional_pds[i]))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(10)

    asyncio.run(analize_currency_data_loop(analize_pds, additional_pds))
