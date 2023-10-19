from pandas import DataFrame, Timedelta, read_csv
from datetime import datetime
from tvDatafeed import Interval
import file_manager
from analizer import MultitimeframeAnalizer
import interval_convertor
from price_parser import PriceData
import asyncio
from signals import *

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

signals_data_path = "signals/"
signals_check_ended = "signals/check_ended/"
signals_analysis_last_date = {}
signal_last_update = datetime.now()


async def close_position_delay(interval: Interval, bars_count=3):
    delay_seconds = interval_convertor.interval_to_datetime(interval) / Timedelta(seconds=1) * bars_count
    await asyncio.sleep(delay_seconds)


async def close_position(position_open_price, signal: Signal, pd: PriceData, bars_count):
    await close_position_delay(Interval.in_1_minute, bars_count)

    price_data = pd.get_price_data(bars_count=2)

    msg, is_profit_position = signal.get_close_position_signal_message(pd, position_open_price, price_data.close[0], bars_count)
    return msg, is_profit_position


def save_signal_file(df, pd: PriceData):
    interval = str(pd.interval).replace(".", "")
    path = signals_data_path + pd.symbol + interval + ".csv"
    df.to_csv(path)
    with open(f"{signals_check_ended}{pd.symbol}{str(pd.interval).replace('.', '')}.txt", "w") as file:
        pass


def is_signal_analized(pd):
    path = signals_check_ended + pd.symbol + str(pd.interval).replace(".", "") + ".txt"
    if not file_manager.is_file_exists(path):
        return False

    return True


def is_signals_analized(prices_data):
    prev_pd = None
    for pd in prices_data:
        prev_pd = pd
        path = signals_check_ended + pd.symbol + str(pd.interval).replace(".", "") + ".txt"
        if not file_manager.is_file_exists(path):
            # print("\tnot created ", path)
            return False, None

    path = signals_data_path + prev_pd.symbol + str(prev_pd.interval).replace(".", "") + ".csv"
    if file_manager.is_file_exists(path):
        df = read_csv(path)
        date = datetime.strptime(df.date[0], '%Y-%m-%d %H:%M:%S')
        return True, date
    return False, None


def read_signal_data(pd: PriceData):
    interval = str(pd.interval).replace(".", "")
    path = signals_check_ended + pd.symbol + interval + ".txt"
    if not file_manager.is_file_exists(path):
        return None
    path = signals_data_path + pd.symbol + interval + ".csv"
    if not file_manager.is_file_exists(path):
        return None

    df = read_csv(path)
    return df


def reset_signals_files(prices_data: [PriceData]):
    for pd in prices_data:
        interval = str(pd.interval).replace(".", "")
        path = signals_check_ended + pd.symbol + interval + ".txt"
        file_manager.delete_file_if_exists(path)


def analize_currency_data_controller(analize_pair):
    def analize_currency_data_function(check_pds: [PriceData], unit_pd: PriceData):
        main_pd = check_pds[0]
        main_price_df = main_pd.get_chart_data_if_exists_if_can_analize()
        if main_price_df is None:
            return

        dt = main_price_df["datetime"][0]
        if not unit_pd.is_analize_time(dt):
            return

        prices_dfs = [pd.get_chart_data_if_exists() for pd in check_pds]

        analizer = MultitimeframeAnalizer(2, 2)
        has_signal, signal, debug, deal_time = analizer.analize(prices_dfs, check_pds)

        open_position_price = main_price_df.close[0]
        msg = signal.get_open_msg_text(main_pd, deal_time)

        data = [[has_signal, signal.type, msg + "\n" + debug, main_price_df.datetime[0], open_position_price, main_pd.interval,
                 main_pd.symbol, main_pd.exchange, deal_time]]
        columns = ["has_signal", "signal_type", "msg", "date", "open_price", "interval", "symbol", "exchange", "deal_time"]
        df = DataFrame(data, columns=columns)
        save_signal_file(df, main_pd)

        print("Created signal file:", msg, main_price_df.datetime[0])

    async def analize_currency_data_loop(analize_pair):
        while True:
            analize_currency_data_function([analize_pair[0], *analize_pair[1]], analize_pair[2])
            await asyncio.sleep(1)

    asyncio.run(analize_currency_data_loop(analize_pair))
