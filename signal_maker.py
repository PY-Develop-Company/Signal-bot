from pandas import Timedelta
from datetime import datetime
from tvDatafeed import Interval
from analizer import MultitimeframeAnalizer, NewMultitimeframeAnalizer
import interval_convertor
from analized_signals_table import AnalizedSignalsTable
import asyncio
from signals import *

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: Interval, bars_count=3):
    delay_seconds = interval_convertor.interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price_original, signal: Signal, pd: PriceData, bars_count):
    position_open_price = pd.get_price_data(bars_count=2)
    await close_position_delay(Interval.in_1_minute, bars_count)

    price_data = pd.get_price_data(bars_count=2)
    if (price_data is None) or (position_open_price is None):
        open_price = position_open_price_original
        close_price = position_open_price_original
    else:
        open_price = position_open_price.close[0]
        close_price = price_data.close[0]

    msg, is_profit_position = signal.get_close_position_signal_message(pd, open_price, close_price, bars_count)
    return msg, is_profit_position, open_price, close_price


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
    # print(real_bars, expected_bars)
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
        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd, deal_time)

        has_signal = True
        AnalizedSignalsTable.add_analized_signal(main_pd, main_price_df.datetime[0], has_signal, signal.type,
                                                 deal_time, open_position_price, msg, start_analize_time)

        print("Created signal file:", msg, main_price_df.datetime[0])

    async def analize_currency_data_loop(analize_pds, additional_pds):
        while True:
            print("analize_loop")
            tasks = []
            for i in range(len(analize_pds)):
                task = asyncio.create_task(analize_currency_data_function(analize_pds[i], additional_pds[i]))
                tasks.append(task)
            await asyncio.gather(*tasks)
            await asyncio.sleep(3)

    asyncio.run(analize_currency_data_loop(analize_pds, additional_pds))
