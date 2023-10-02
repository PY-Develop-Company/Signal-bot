from pandas import DataFrame
from pandas import Timedelta
from datetime import timedelta, datetime
from tvDatafeed import Interval
import price_parser
import indicators_reader
import asyncio
from multiprocessing import Process, Array

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

photo_long_path = "img/long.jpg"
photo_short_path = "img/short.jpg"

long_signal_smile = "🟢"
short_signal_smile = "🔴"

long_signal_text = "LONG ⬆"
short_signal_text = "SHORT ⬇"
neutral_signal_text = "Нет сигнала"

profit_smile = "✅"
loss_smile = "❌"


class Signal:
    def __init__(self):
        self.signal = None
        self.photo_path = None
        self.smile = None
        self.text = None
        self.type = None

    def get_msg(self, symbol, interval):
        return self.smile + symbol + " " + self.text + " " + timedelta_to_string(interval)

    def get_photo_path(self):
        return self.photo_path


class NeutralSignal(Signal):
    def __init__(self):
        self.signal = type(self)
        self.photo_path = "None"
        self.smile = "None"
        self.text = neutral_signal_text
        self.type = "neutral"


class LongSignal(Signal):
    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_long_path
        self.smile = long_signal_smile
        self.text = long_signal_text
        self.type = "long"


class ShortSignal(Signal):
    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_short_path
        self.smile = short_signal_smile
        self.text = short_signal_text
        self.type = "short"


ns = NeutralSignal()
ls = LongSignal()
ss = ShortSignal()


def timedelta_to_string(interval):
    delay_days = interval / Timedelta(days=1)
    delay_hours = interval / Timedelta(hours=1)
    delay_minutes = interval / Timedelta(minutes=1)
    if delay_days > 0:
        str(int(delay_days * 3)) + "Д"
    elif delay_hours > 0:
        return str(int(delay_hours * 3)) + "ч"
    return str(int(delay_minutes * 3)) + "мин"


def is_profit(open_price, close_price, signal):
    return (True if close_price >= open_price else False) if (signal == ls) else (
        True if (close_price <= open_price) else False)


def get_close_position_signal_message(open, close, signal, symbol, interval):
    is_profit_position = is_profit(open, close, signal)
    text = profit_smile if is_profit_position else loss_smile
    debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

    message = f"{signal.smile} Сделка в {text} {symbol} {signal.text} {timedelta_to_string(interval)} \n{debug_text}"
    return message, is_profit_position


async def close_position(position_open_price, signal, symbol, exchange, interval: timedelta, bars_count=3):
    delay_minutes = interval / Timedelta(minutes=1)
    await asyncio.sleep(delay_minutes * bars_count * 60)

    interval = indicators_reader.get_interval(interval)
    price_data = price_parser.get_price_data(symbol.replace("/", ""), exchange, interval, bars_count=2)
    msg, is_profit_position = get_close_position_signal_message(position_open_price, price_data.close[0], signal, symbol,
                                                       price_data.datetime[0] - price_data.datetime[1])
    return msg, is_profit_position


def check_signal(prices_df: DataFrame, interval: timedelta, successful_indicators_count=4):
    volume_ind = indicators_reader.VolumeIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    sp_ind = indicators_reader.ScalpProIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    uma_ind = indicators_reader.UMAIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)
    sob_ind = indicators_reader.SuperOrderBlockIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low, interval)
    nw_ind = indicators_reader.NadarayaWatsonIndicator(prices_df, prices_df.open, prices_df.close, prices_df.high, prices_df.low)

    indicators_signals = [sob_ind.get_signal(), volume_ind.get_signal(), uma_ind.get_signal(), nw_ind.get_signal(), sp_ind.get_signal()]

    signal_counts = {ls.type: [0, [], ls], ss.type: [0, [], ss], ns.type: [0, [], ns]}
    for signal in indicators_signals:
        signal_counts.get(signal[0].type)[0] += 1
        signal_counts.get(signal[0].type)[1].append(", " + signal[1])

    main_signal = (ns.type, [0, [], ns])
    for signal_count in signal_counts.items():
        if signal_count[1][0] > main_signal[1][0] and not(signal_count[0] == ns.type):
            main_signal = signal_count

    has_signal = main_signal[1][0] >= successful_indicators_count and indicators_signals[0][0].type == main_signal[0]

    debug_dict = {}
    for sig in signal_counts.items():
        debug_dict[sig[1][2].text] = sig[1][:2]
    debug_text = f"""\n\nПроверка сигнала:
    \tВалютная пара: {prices_df.symbol[0]}" таймфрейм: {interval} время свечи: {prices_df.datetime[0]}
    \tЕсть ли сигнал: {has_signal}
    \tПоказания индикаторов: {debug_dict})
    """
    print(debug_text)
    # print("="*200, "\n")
    if has_signal:
        return True, main_signal[1][2], debug_text
    return False, ns, debug_text


#test


def signal_message_check_function(price_data_frame: DataFrame, bars_to_analyse=200, successful_indicators_count=4):
    if len(price_data_frame) < bars_to_analyse:
        return

    data = []
    interval = price_data_frame["datetime"][0] - price_data_frame["datetime"][1]

    profit_dict = [0, 0]

    loop_count = len(price_data_frame) - bars_to_analyse
    full_df = price_data_frame
    for i in range(loop_count):
        check_df = full_df.iloc[3:].reset_index(drop=True)
        start_check_time = datetime.now()

        has_signal, open_signal, debug_text = check_signal(check_df, interval, successful_indicators_count=successful_indicators_count)
        # print("delay", datetime.now() - start_check_time)

        if has_signal:
            open_position_price = check_df.close[0]
            close_position_price = full_df.close[0]
            has_profit = is_profit(open_position_price, close_position_price, open_signal)
            profit_dict[has_profit] += 1
            print("open_position_price", open_position_price)
            print("close_position_price", close_position_price)

            print(debug_text)
            print("Profit data:", "\n\tprofit ---> ", profit_dict[1], "\n\tloss ---> ", profit_dict[0])
            data_el = [profit_dict[1], profit_dict[0], open_signal.type, open_position_price, close_position_price, debug_text]
            data.append(data_el)

        full_df = price_data_frame[i+1:i+bars_to_analyse+4].reset_index(drop=True)
        full_df = full_df.iloc[1:].reset_index(drop=True)

    path = "debug/" + price_data_frame.symbol[0].split(":")[1] + str(indicators_reader.get_interval(interval)).replace(".", "") + "_indicators_count_"+str(successful_indicators_count)+ ".csv"
    df = DataFrame(data, columns=["profit", "loss", "signal", "open_signal_price", "close_signal_price", "data"])
    df.to_csv(path)



if __name__ == "__main__":
    currencies = price_parser.get_currencies() #, [("BTCUSD", "COINBASE"), ("ETHUSD", "COINBASE")]  #
    intervals = [Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute]

    # profit_dict = Array('i', [0, 0])

    # print("Profit data", profit_dict[:])
    for interval in intervals:
        for currency in currencies:
            df = price_parser.get_price_data(currency[0], currency[1], interval, 2000)
            Process(target=signal_message_check_function, args=(df, )).start()
            # signal_message_check_function(df, profit_dict)

    # print("Profit data:", "\n\tprofit ---> ", profit_dict[1], "\n\tloss ---> ", profit_dict[0])
