import numpy as np
import pandas
from tvDatafeed import Interval
import math
import signal_maker as sm
from datetime import timedelta, datetime
from pandas import Series
import plotly.graph_objects as go
import price_parser


def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)


def get_datetime(interval):
    if interval == Interval.in_1_minute:
        return timedelta(minutes=1)
    elif interval == Interval.in_3_minute:
        return timedelta(minutes=3)
    elif interval == Interval.in_5_minute:
        return timedelta(minutes=5)
    elif interval == Interval.in_15_minute:
        return timedelta(minutes=15)
    elif interval == Interval.in_30_minute:
        return timedelta(minutes=30)
    elif interval == Interval.in_45_minute:
        return timedelta(minutes=45)
    else:
        return timedelta(days=1)


def get_interval(datetime):
    datetime = math.floor(datetime.total_seconds() / 60)
    if datetime == 15:
        return Interval.in_1_minute
    elif datetime == 5:
        return Interval.in_5_minute
    elif datetime == 1:
        return Interval.in_1_minute
    else:
        return Interval.in_daily


def get_interval_string(datetime):
    return str(datetime).replace(".", "")


def get_scalp_pro_signal(close_price, fast_line=8, slow_line=10, smoothness=8):
    def smooth(par, p: Series):
        res = np.zeros(len(close_price), dtype=float)

        f = (1.414 * 3.141592653589793238462643) / float(par)
        a = math.exp(-f)
        c2 = 2 * a * math.cos(f)
        c3 = -a * a
        c1 = 1 - c2 - c3

        for i in range(len(p) - 2, -1, -1):
            ssm1 = 0
            ssm2 = 0
            if i + 1 < len(p):
                ssm1 = res[i + 1]
            if i + 2 < len(p):
                ssm2 = res[i + 2]

            res[i] = c1 * (p[i] + p[i + 1]) * 0.5 + c2 * ssm1 + c3 * ssm2
        return res

    smooth1 = smooth(fast_line, close_price)
    smooth2 = smooth(slow_line, close_price)

    macd = (smooth1 - smooth2) * 10000000
    smooth3 = smooth(smoothness, macd)

    # fig = go.Figure(
    #     data=[
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=smooth3,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#eb3434'}
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=macd,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#37eb34'}
    #         )
    #     ]
    # )
    # fig.update_layout(
    #     title=f'The Candlestick graph for {src["symbol"][0]}',
    #     xaxis_title='Date',
    #     yaxis_title=f'Price ()',
    #     xaxis_rangeslider_visible=False,
    #     xaxis=dict(type="category")
    # )
    # fig.show()
    if macd[0] == smooth3[0]:
        res_signal = sm.buy_signal if macd[1] > smooth3[1] else (sm.sell_signal if macd[1] < smooth3[1] else sm.neutral_signal)
    else:
        res_signal = sm.buy_signal if macd[0] > smooth3[0] else (sm.sell_signal if macd[0] < smooth3[0] else sm.neutral_signal)
    return res_signal, "scalp_pro"


def get_volume_signal(open_price, close_price, bars_count=3):
    buy_signal_count = 0
    sell_signal_count = 0
    for i in range(bars_count):
        if open_price[i] <= close_price[i]:
            buy_signal_count += 1
        else:
            sell_signal_count += 1

    signal = sm.neutral_signal
    if buy_signal_count == bars_count:
        signal = sm.buy_signal
    elif sell_signal_count == bars_count:
        signal = sm.sell_signal

    return signal, "volume"


def get_super_order_block_signal(src: pandas.DataFrame, open, close, high, low, interval: timedelta,
                                 obMaxBoxSet=10, fvgMaxBoxSet=10):
    class Box:
        def __init__(self, left=0, top=0, right=0, bottom=0, signal_type="box"):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.signal_type = signal_type

        def print_info(self):
            print("Created box: ", self.left, self.top, self.right, self.bottom)

        def check_signal(self, bar_low, bar_high, bar_date):
            is_price_in_box = (bar_high > self.top and bar_low < self.top) or (
                    bar_high > self.bottom and bar_low < self.bottom)
            is_date_range_in_box = self.left <= bar_date <= self.right
            return self.signal_type if (is_price_in_box and is_date_range_in_box) else sm.neutral_signal

    is_up_bar = lambda index: close[index] > open[index]
    is_down_bar = lambda index: close[index] < open[index]
    is_ob_box_up = lambda index: is_down_bar(index + 1) and is_up_bar(index) and close[index] > high[index + 1]
    is_ob_box_down = lambda index: is_up_bar(index + 1) and is_down_bar(index) and close[index] < low[index + 1]
    is_fvg_box_up = lambda index: low[index] > high[index + 2]
    is_fvg_box_down = lambda index: high[index] < low[index + 2]

    def pivot_high(price):
        highs = {}
        prices_count = len(price)
        nearest_high_price = price[prices_count - 1]
        for i in range(prices_count - 2, 0, -1):
            if price[i - 1] < price[i] > price[i + 1]:
                nearest_high_price = price[i]
            highs.update({i: nearest_high_price})
        highs.update({0: nearest_high_price})
        return highs

    def pivot_low(price):
        lows = {}
        prices_count = len(price)
        nearest_low_price = price[prices_count - 1]
        for i in range(prices_count - 2, 0, -1):
            if price[i - 1] > price[i] < price[i + 1]:
                nearest_low_price = price[i]
            lows.update({i: nearest_low_price})
        lows.update({0: nearest_low_price})
        return lows

    def control_box(boxes, high, low, box_index):
        for i in range(len(boxes) - 1, 0, -1):
            is_price_in_box = (high > boxes[i].bottom and low < boxes[i].bottom) or (
                    high > boxes[i].top and low < boxes[i].top)
            if src.datetime[box_index] == boxes[i].right and not is_price_in_box:
                boxes[i].right = src.datetime[box_index] + interval

    date_format = '%Y-%m-%d %H:%M:%S'
    src.datetime = pandas.to_datetime(src.datetime)

    obMaxBoxSet = clamp(obMaxBoxSet, 1, 100)
    fvgMaxBoxSet = clamp(fvgMaxBoxSet, 1, 100)

    _bearBoxesOB = []
    _bullBoxesOB = []
    _bearBoxesFVG = []
    _bullBoxesFVG = []

    top = pivot_high(high)
    bottom = pivot_low(low)

    prices_count = len(src)
    # # # # # # # # # # # Order Block # # # # # # # # #
    for i in range(prices_count - 3, -1, -1):
        date_time = src.datetime[i]
        if is_ob_box_up(i + 1):
            _bullboxOB = Box(left=date_time - interval * 2, top=high[i + 2], right=date_time,
                             bottom=min(low[i + 2], low[i + 1]), signal_type=sm.buy_signal)
            if len(_bullBoxesOB) > obMaxBoxSet:
                _bullBoxesOB.remove(_bullBoxesOB[0])
            _bullBoxesOB.append(_bullboxOB)

        if is_ob_box_down(i + 1):
            _bearboxOB = Box(left=date_time - interval * 2, top=max(high[i + 2], high[i + 1]), right=date_time,
                             bottom=low[i + 2], signal_type=sm.sell_signal)
            if len(_bearBoxesOB) > obMaxBoxSet:
                _bearBoxesOB.remove(_bearBoxesOB[0])
            _bearBoxesOB.append(_bearboxOB)

        if i > 0:
            control_box(_bearBoxesOB, high[i], low[i], i)
            control_box(_bullBoxesOB, high[i], low[i], i)

    # # # # # # # # # Fair Value Gap # # # # # # # # #
    for i in range(prices_count - 3, -1, -1):
        date_time = src.datetime[i]
        if is_fvg_box_up(i):
            _bullboxFVG = None
            if (close[i + 1] > top[i]) and (low[i + 1] < top[i]) and (high[i + 2] < top[i]) and (low[i] > top[i]):
                _bullboxFVG = Box(left=date_time - interval * 2, top=low[i], right=date_time, bottom=high[i + 2],
                                  signal_type=sm.buy_signal)
            else:
                _bullboxFVG = Box(left=date_time - interval * 2, top=low[i], right=date_time, bottom=high[i + 2],
                                  signal_type=sm.buy_signal)

            if len(_bullBoxesFVG) > fvgMaxBoxSet:
                _bullBoxesFVG.remove(_bullBoxesFVG[0])
            _bullBoxesFVG.append(_bullboxFVG)

        if is_fvg_box_down(i):
            _bearboxFVG = None
            if (close[i + 1] < bottom[i]) and (high[i + 1] > bottom[i]) and (low[i + 2] > bottom[i]) and (
                    high[i] < bottom[i]):
                _bearboxFVG = Box(left=date_time - interval * 2, top=low[i + 2], right=date_time, bottom=high[i],
                                  signal_type=sm.sell_signal)
            else:
                _bearboxFVG = Box(left=date_time - interval * 2, top=low[i + 2], right=date_time, bottom=high[i],
                                  signal_type=sm.sell_signal)

            if len(_bearBoxesFVG) > fvgMaxBoxSet:
                _bearBoxesFVG.remove(_bearBoxesFVG[0])
            _bearBoxesFVG.append(_bearboxFVG)

        if i > 0:
            control_box(_bearBoxesFVG, high[i], low[i], i)
            control_box(_bullBoxesFVG, high[i], low[i], i)

    # scatters1 = []
    # scatters2 = []
    # scatters3 = []
    # scatters4 = []
    # for box in _bullBoxesOB:
    #     scatters1.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
    #                                 y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
    #                                 fill="toself", fillcolor='rgba(0, 255, 0,0.1)'))
    # for box in _bearBoxesOB:
    #     scatters2.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
    #                                 y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
    #                                 fill="toself", fillcolor='rgba(255, 0, 0,0.1)'))
    # for box in _bullBoxesFVG:
    #     scatters3.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
    #                                 y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
    #                                 fill="toself", fillcolor='rgba(0, 255, 0,0.1)'))
    # for box in _bearBoxesFVG:
    #     scatters4.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
    #                                 y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
    #                                 fill="toself", fillcolor='rgba(255, 0, 0,0.1)'))

    date_time = src.datetime[0]

    boxes = _bullBoxesOB + _bearBoxesOB + _bullBoxesFVG + _bearBoxesFVG
    return_signal = sm.neutral_signal
    signal_boxes = []
    for box in boxes:
        signal = box.check_signal(low[0], high[0], date_time)
        if not (signal == sm.neutral_signal):
            signal_boxes.append(box)

    if len(signal_boxes) > 0:
        biggest_box = signal_boxes[0]
        biggest_box_height = biggest_box.top - biggest_box.bottom
        for b in signal_boxes:
            if b.left < biggest_box.left:
                biggest_box = b
                biggest_box_height = biggest_box.top - biggest_box.bottom
            elif b.left == biggest_box.left:
                b_height = b.top - b.bottom
                if b_height > biggest_box_height:
                    biggest_box = b
                    biggest_box_height = biggest_box.top - biggest_box.bottom
        return_signal = biggest_box.signal_type

    # fig = go.Figure(
    #     data=[
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         ),
    #         *scatters1,
    #         *scatters2,
    #         *scatters3,
    #         *scatters4,
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         )
    #     ]
    # )
    # fig.update_layout(
    #     title=f'The Candlestick graph for {src["symbol"][0]}',
    #     xaxis_title='Date',
    #     yaxis_title=f'Price ()',
    #     xaxis_rangeslider_visible=False,
    #     xaxis=dict(type="category")
    # )
    # fig.show()

    return return_signal, "super order block"


def get_ultimate_moving_average_signal(close_price, rolling=20, smooth=2):
    avg = close_price.rolling(window=rolling).mean()
    avg = avg.shift(periods=-(rolling-1))

    # avg_long = []
    # avg_short = []
    signals = []
    for i in range(len(avg)):
        if np.isnan(avg[i]) or np.isnan(avg[i + smooth]):
            continue

        ma_up = avg[i] > avg[i + smooth]
        ma_down = avg[i] < avg[i + smooth]
        signals.append(sm.buy_signal if ma_up else (sm.sell_signal if ma_down else sm.neutral_signal))
        # avg_long.append(avg[i] if ma_up else 0)
        # avg_short.append(avg[i] if ma_down else 0)
    if len(signals) == 0:
        print("not enough data warning ultimate moving average")
        signals.append(sm.neutral_signal)

    # fig = go.Figure(
    #     data=[
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=avg_short,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#eb3434'}
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=avg_long,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#37eb34'}
    #         )
    #     ]
    # )
    # fig.update_layout(
    #     title=f'The Candlestick graph for {src["symbol"][0]}',
    #     xaxis_title='Date',
    #     yaxis_title=f'Price ()',
    #     xaxis_rangeslider_visible=False,
    #     xaxis=dict(type="category")
    # )
    # fig.show()
    return signals[0], "ultimate moving average"


def get_nadaraya_watson_envelope_signal(close_price, h=8.0, mult=3.0):
    def gauss(x, k):
        return math.exp(-(math.pow(x, 2) / (k * k * 2)))

    price_count = len(close_price)
    nwe = []
    sae = 0
    for i in range(0, price_count - 2):
        sum = 0.0
        sumw = 0.0

        for j in range(0, price_count - 2):
            w = gauss(i - j, h)
            sum += close_price[j] * w
            sumw += w

        y2 = sum / sumw
        sae += abs(close_price[i] - y2)
        nwe.append(y2)

    sae = sae / (price_count - 2) * mult
    signals = []
    for i in range(0, price_count - 2):
        if close_price[i] > (nwe[i] + sae) > close_price[i + 1]:
            signals.append((i, sm.sell_signal))
        elif close_price[i] < (nwe[i] - sae) < close_price[i + 1]:
            signals.append((i, sm.buy_signal))
    if len(signals) == 0:
        signals.append((0, sm.neutral_signal))
        print("not enough data warning Nadaraya Watson envelope")

    # buy_sig = []
    # sell_sig = []
    #
    # j = 0
    # curr_signal = signals[0]
    # for i in range(0, price_count - 2):
    #     buy_append_val = 0
    #     sell_append_val = 0
    #     if i == curr_signal[0]:
    #         if curr_signal[1] == sm.buy_signal:
    #             buy_append_val = 0.6
    #         elif curr_signal[1] == sm.sell_signal:
    #             sell_append_val = 0.6
    #
    #         j += 1
    #         if j < len(signals):
    #             curr_signal = signals[j]
    #     buy_sig.append(buy_append_val)
    #     sell_sig.append(sell_append_val)
    # fig = go.Figure(
    #     data=[
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=sell_sig,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#eb3434'}
    #         ),
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=buy_sig,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#37eb34'}
    #         )
    #     ]
    # )
    # fig.update_layout(
    #     title=f'The Candlestick graph for {src["symbol"][0]}',
    #     xaxis_title='Date',
    #     yaxis_title=f'Price ()',
    #     xaxis_rangeslider_visible=False,
    #     xaxis=dict(type="category")
    # )
    # fig.show()
    return signals[0][1], "Nadaraya Watson envelope"


# if __name__ == "__main__":
#     df = price_parser.get_price_data("EURUSD", "OANDA", Interval.in_1_minute, bars_count=1000)
#     interval = df.datetime[0] - df.datetime[1]
#     data = get_super_order_block_signal(df, df.open, df.close, df.high, df.low, interval)
