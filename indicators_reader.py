import numpy as np
import pandas
from tvDatafeed import Interval
import math
import signal_maker as sm
from datetime import timedelta
from pandas import Series
import plotly.graph_objects as go


class Indicator:
    def __init__(self, src, open, close, high, low):
        self.src = src
        self.open = open
        self.close = close
        self.high = high
        self.low = low
        self.name = "indicator"

    def get_signal(self) -> sm.Signal:
        print("no get_signal implemented")
        return sm.neutral_signal_text, self.name

    def graph(self):
        print("no graph implemented")


class SuperOrderBlockIndicator(Indicator):
    def __init__(self, src, open, close, high, low, interval: timedelta, obMaxBoxSet=10, fvgMaxBoxSet=10):
        super().__init__(src, open, close, high, low)
        self.interval = interval
        obMaxBoxSet = clamp(obMaxBoxSet, 1, 100)
        fvgMaxBoxSet = clamp(fvgMaxBoxSet, 1, 100)
        self.obMaxBoxSet = obMaxBoxSet
        self.fvgMaxBoxSet = fvgMaxBoxSet
        self.name = "SuperOrderBlock"

    def is_up_bar(self, index):
        return self.close[index] > self.open[index]

    def is_down_bar(self, index):
        return self.close[index] < self.open[index]

    def is_ob_box_up(self, index):
        return self.is_down_bar(index + 1) and self.is_up_bar(index) and self.close[index] > self.high[index + 1]

    def is_ob_box_down(self, index):
        return self.is_up_bar(index + 1) and self.is_down_bar(index) and self.close[index] < self.low[index + 1]

    def is_fvg_box_up(self, index):
        return self.low[index] > self.high[index + 2]

    def is_fvg_box_down(self, index):
        return self.high[index] < self.low[index + 2]

    class Box:
        def __init__(self, left=0, top=0, right=0, bottom=0, signal_type=sm.ns):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.signal_type = signal_type

        def print_info(self):
            print("Created box: ", self.left, self.top, self.right, self.bottom)

        def check_signal(self, bar_low, bar_high, bar_date):
            is_price_in_box = (bar_high > self.top > bar_low) or (bar_high > self.bottom > bar_low)
            is_date_range_in_box = self.left <= bar_date <= self.right
            return self.signal_type if (is_price_in_box and is_date_range_in_box) else sm.neutral_signal_text

    def pivot_high(self, price):
        highs = {}
        prices_count = len(price)
        nearest_high_price = price[prices_count - 1]
        for i in range(prices_count - 2, 0, -1):
            if price[i - 1] < price[i] > price[i + 1]:
                nearest_high_price = price[i]
            highs.update({i: nearest_high_price})
        highs.update({0: nearest_high_price})
        return highs

    def pivot_low(self, price):
        lows = {}
        prices_count = len(price)
        nearest_low_price = price[prices_count - 1]
        for i in range(prices_count - 2, 0, -1):
            if price[i - 1] > price[i] < price[i + 1]:
                nearest_low_price = price[i]
            lows.update({i: nearest_low_price})
        lows.update({0: nearest_low_price})
        return lows

    def control_box(self, boxes, high, low, box_index):
        for i in range(len(boxes) - 1, 0, -1):
            is_price_in_box = (high > boxes[i].bottom > low) or (high > boxes[i].top > low)
            if self.src.datetime[box_index] == boxes[i].right and not is_price_in_box:
                boxes[i].right = self.src.datetime[box_index] + self.interval

    def get_signal(self):
        self.src.datetime = pandas.to_datetime(self.src.datetime)

        _bearBoxesOB = []
        _bullBoxesOB = []
        _bearBoxesFVG = []
        _bullBoxesFVG = []

        top = self.pivot_high(self.high)
        bottom = self.pivot_low(self.low)

        prices_count = len(self.src)
        # # # # # # # # # # # Order Block # # # # # # # # #
        for i in range(prices_count - 3, -1, -1):
            date_time = self.src.datetime[i]
            if self.is_ob_box_up(i + 1):
                _bullboxOB = self.Box(left=date_time - self.interval * 2, top=self.high[i + 2], right=date_time,
                                      bottom=min(self.low[i + 2], self.low[i + 1]), signal_type=sm.ls)
                if len(_bullBoxesOB) > self.obMaxBoxSet:
                    _bullBoxesOB.remove(_bullBoxesOB[0])
                _bullBoxesOB.append(_bullboxOB)

            if self.is_ob_box_down(i + 1):
                _bearboxOB = self.Box(left=date_time - self.interval * 2, top=max(self.high[i + 2], self.high[i + 1]),
                                      right=date_time, bottom=self.low[i + 2], signal_type=sm.ss)
                if len(_bearBoxesOB) > self.obMaxBoxSet:
                    _bearBoxesOB.remove(_bearBoxesOB[0])
                _bearBoxesOB.append(_bearboxOB)

            if i > 0:
                self.control_box(_bearBoxesOB, self.high[i], self.low[i], i)
                self.control_box(_bullBoxesOB, self.high[i], self.low[i], i)

        # # # # # # # # # Fair Value Gap # # # # # # # # #
        for i in range(prices_count - 3, -1, -1):
            date_time = self.src.datetime[i]
            if self.is_fvg_box_up(i):
                _bullboxFVG = None
                if (self.close[i + 1] > top[i]) and (self.low[i + 1] < top[i]) and (
                        self.high[i + 2] < top[i]) and (self.low[i] > top[i]):
                    _bullboxFVG = self.Box(left=date_time - self.interval * 2, top=self.low[i], right=date_time,
                                           bottom=self.high[i + 2], signal_type=sm.ls)
                else:
                    _bullboxFVG = self.Box(left=date_time - self.interval * 2, top=self.low[i], right=date_time,
                                           bottom=self.high[i + 2], signal_type=sm.ls)

                if len(_bullBoxesFVG) > self.fvgMaxBoxSet:
                    _bullBoxesFVG.remove(_bullBoxesFVG[0])
                _bullBoxesFVG.append(_bullboxFVG)

            if self.is_fvg_box_down(i):
                _bearboxFVG = None
                if (self.close[i + 1] < bottom[i]) and (self.high[i + 1] > bottom[i]) and (
                        self.low[i + 2] > bottom[i]) and (self.high[i] < bottom[i]):
                    _bearboxFVG = self.Box(left=date_time - self.interval * 2, top=self.low[i + 2], right=date_time,
                                           bottom=self.high[i], signal_type=sm.ss)
                else:
                    _bearboxFVG = self.Box(left=date_time - self.interval * 2, top=self.low[i + 2], right=date_time,
                                           bottom=self.high[i], signal_type=sm.ss)

                if len(_bearBoxesFVG) > self.fvgMaxBoxSet:
                    _bearBoxesFVG.remove(_bearBoxesFVG[0])
                _bearBoxesFVG.append(_bearboxFVG)

            if i > 0:
                self.control_box(_bearBoxesFVG, self.high[i], self.low[i], i)
                self.control_box(_bullBoxesFVG, self.high[i], self.low[i], i)

        date_time = self.src.datetime[0]

        boxes = _bullBoxesOB + _bearBoxesOB + _bullBoxesFVG + _bearBoxesFVG
        return_signal = sm.ns
        signal_boxes = []
        for box in boxes:
            signal = box.check_signal(self.low[0], self.high[0], date_time)
            if not (signal == sm.neutral_signal_text):
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

        # self.graph(_bullBoxesOB, _bearBoxesOB, _bullBoxesFVG, _bearBoxesFVG)

        return return_signal, self.name

    def graph(self, _bullBoxesOB, _bearBoxesOB, _bullBoxesFVG, _bearBoxesFVG):
        scatters1 = []
        scatters2 = []
        scatters3 = []
        scatters4 = []
        for box in _bullBoxesOB:
            scatters1.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
                                        y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
                                        fill="toself", fillcolor='rgba(0, 255, 0,0.1)'))
        for box in _bearBoxesOB:
            scatters2.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
                                        y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
                                        fill="toself", fillcolor='rgba(255, 0, 0,0.1)'))
        for box in _bullBoxesFVG:
            scatters3.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
                                        y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
                                        fill="toself", fillcolor='rgba(0, 255, 0,0.1)'))
        for box in _bearBoxesFVG:
            scatters4.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
                                        y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
                                        fill="toself", fillcolor='rgba(255, 0, 0,0.1)'))
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                ),
                *scatters1,
                *scatters2,
                *scatters3,
                *scatters4,
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                )
            ]
        )
        fig.update_layout(
            title=f'The Candlestick graph for {self.src["symbol"][0]}',
            xaxis_title='Date',
            yaxis_title=f'Price ()',
            xaxis_rangeslider_visible=False,
            xaxis=dict(type="category")
        )
        fig.show()


class ScalpProIndicator(Indicator):
    def __init__(self, src, open, close, high, low, fast_line=8, slow_line=10, smoothness=8):
        super().__init__(src, open, close, high, low)
        self.fast_line = fast_line
        self.slow_line = slow_line
        self.smoothness = smoothness
        self.name = "ScalpPro"

    def smooth(self, par, p: Series):
        res = np.zeros(len(self.close), dtype=float)

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

    def get_signal(self):
        smooth1 = self.smooth(self.fast_line, self.close)
        smooth2 = self.smooth(self.slow_line, self.close)

        macd = (smooth1 - smooth2) * 10000000
        smooth3 = self.smooth(self.smoothness, macd)

        # self.graph(smooth3, macd)
        if macd[0] == smooth3[0]:
            res_signal = sm.ls if macd[1] > smooth3[1] else (
                sm.ss if macd[1] < smooth3[1] else sm.ns)
        else:
            res_signal = sm.ls if macd[0] > smooth3[0] else (
                sm.ss if macd[0] < smooth3[0] else sm.ns)
        return res_signal, self.name

    def graph(self, smooth3, macd):
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=smooth3,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#eb3434'}
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=macd,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#37eb34'}
                )
            ]
        )
        fig.update_layout(
            title=f'The Candlestick graph for {self.src["symbol"][0]}',
            xaxis_title='Date',
            yaxis_title=f'Price ()',
            xaxis_rangeslider_visible=False,
            xaxis=dict(type="category")
        )
        fig.show()


class VolumeIndicator(Indicator):
    def __init__(self, src, open, close, high, low, bars_count=3):
        super().__init__(src, open, close, high, low)
        self.bars_count = bars_count
        self.name = "Volume"

    def get_signal(self):
        buy_signal_count = 0
        sell_signal_count = 0
        for i in range(self.bars_count):
            if self.open[i] <= self.close[i]:
                buy_signal_count += 1
            else:
                sell_signal_count += 1

        signal = sm.ns
        if buy_signal_count == self.bars_count:
            signal = sm.ls
        elif sell_signal_count == self.bars_count:
            signal = sm.ss

        return signal, self.name


class UMAIndicator(Indicator):
    def __init__(self, src, open, close, high, low, rolling=20, smooth=2):
        super().__init__(src, open, close, high, low)
        self.rolling = rolling
        self.smooth = smooth
        self.name = "UMA"

    def get_signal(self):
        avg = self.close.rolling(window=self.rolling).mean()
        avg = avg.shift(periods=-(self.rolling - 1))

        avg_long = []
        avg_short = []
        signals = []
        for i in range(len(avg)):
            if np.isnan(avg[i]) or np.isnan(avg[i + self.smooth]):
                continue

            ma_up = avg[i] > avg[i + self.smooth]
            ma_down = avg[i] < avg[i + self.smooth]
            signals.append(sm.ls if ma_up else (sm.ss if ma_down else sm.ns))
            avg_long.append(avg[i] if ma_up else 0)
            avg_short.append(avg[i] if ma_down else 0)
        if len(signals) == 0:
            print("not enough data warning ultimate moving average")
            signals.append(sm.ns)

        # self.graph(avg_short, avg_long)
        return signals[0], self.name

    def graph(self, avg_short, avg_long):
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=avg_short,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#eb3434'}
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=avg_long,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#37eb34'}
                )
            ]
        )
        fig.update_layout(
            title=f'The Candlestick graph for {self.src["symbol"][0]}',
            xaxis_title='Date',
            yaxis_title=f'Price ()',
            xaxis_rangeslider_visible=False,
            xaxis=dict(type="category")
        )
        fig.show()


class NadarayaWatsonIndicator(Indicator):
    def __init__(self, src, open, close, high, low, h=8.0, mult=3.0):
        super().__init__(src, open, close, high, low)
        self.h = h
        self.mult = mult
        self.name = "NadarayaWatson"

    def gauss(self, x, k):
        return math.exp(-(pow(x, 2)/(k * k * 2)))

    def get_signal(self):
        price_count = len(self.close)
        nwe = []
        sae = 0.0
        for i in range(0, min(price_count - 2, 499)):
            sum = 0.0
            sumw = 0.0

            for j in range(0, min(price_count - 2, 499)):
                w = self.gauss(i - j, self.h)
                sum += self.close[j] * w
                sumw += w

            y2 = sum / sumw
            sae += abs(self.close[i] - y2)
            nwe.append(y2)
        sae = sae / (min(price_count - 2, 499)) * self.mult
        signals = []
        for i in range(0, min(price_count - 2, 499)):
            if self.close[i] > (nwe[i] + sae) > self.close[i + 1]:
                signals.append((i, sm.ss))
            elif self.close[i] < (nwe[i] - sae) < self.close[i + 1]:
                signals.append((i, sm.ls))
        if len(signals) == 0:
            signals.append((0, sm.ns))
            print(f"not enough data warning {self.name} envelope")

        # buy_sig = []
        # sell_sig = []
        # j = 0
        # curr_signal = signals[0]
        # for i in range(0, min(price_count - 2, 499)):
        #     buy_append_val = 0
        #     sell_append_val = 0
        #     if i == curr_signal[0]:
        #         if curr_signal[1] == sm.ls:
        #             buy_append_val = 30000
        #         elif curr_signal[1] == sm.ss:
        #             sell_append_val = 30000
        #
        #         j += 1
        #         if j < len(signals):
        #             curr_signal = signals[j]
        #     buy_sig.append(buy_append_val)
        #     sell_sig.append(sell_append_val)
        # self.graph(buy_sig, sell_sig, upsae, downsae)
        return signals[0][1], self.name

    def graph(self, buy_sig, sell_sig, upsae, downsae):
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=sell_sig,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#eb3434'}
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=buy_sig,
                    mode='lines',
                    name='red_signal',
                    line={'color': '#37eb34'}
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=upsae,
                    mode='lines',
                    name='grin_sae',
                    line={'color': '#eb3434'}
                ),
                go.Scatter(
                    x=self.src["datetime"],
                    y=downsae,
                    mode='lines',
                    name='red_sae',
                    line={'color': '#37eb34'}
                )
            ]
        )
        fig.update_layout(
            title=f'The Candlestick graph for {self.src["symbol"][0]} {self.src["datetime"]}',
            xaxis_title='Date',
            yaxis_title=f'Price ()',
            xaxis_rangeslider_visible=False,
            xaxis=dict(type="category")
        )
        fig.show()


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

# if __name__ == "__main__":
#     df = price_parser.get_price_data("EURUSD", "OANDA", Interval.in_1_minute, bars_count=1000)
#     interval = df.datetime[0] - df.datetime[1]
#     data = get_super_order_block_signal(df, df.open, df.close, df.high, df.low, interval)
