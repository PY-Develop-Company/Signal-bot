import numpy as np
import pandas
import math
from tvDatafeed import Interval, TvDatafeed
from datetime import timedelta
from pandas import Series
import plotly.graph_objects as go
from signals import *
from price_parser import PriceData
import interval_convertor


sob_dict = {
    "EURUSD": {
        Interval.in_1_minute: 35,
        Interval.in_3_minute: 70,
        Interval.in_5_minute: 110,
        Interval.in_15_minute: 155,
        Interval.in_30_minute: 210,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "AUDUSD": {
        Interval.in_1_minute: 35,
        Interval.in_3_minute: 75,
        Interval.in_5_minute: 120,
        Interval.in_15_minute: 150,
        Interval.in_30_minute: 220,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "AUDCAD": {
        Interval.in_1_minute: 40,
        Interval.in_3_minute: 94,
        Interval.in_5_minute: 145,
        Interval.in_15_minute: 150,
        Interval.in_30_minute: 200,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "EURJPY": {
        Interval.in_1_minute: 40,
        Interval.in_3_minute: 90,
        Interval.in_5_minute: 124,
        Interval.in_15_minute: 155,
        Interval.in_30_minute: 199,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "EURCAD": {
        Interval.in_1_minute: 85,
        Interval.in_3_minute: 146,
        Interval.in_5_minute: 178,
        Interval.in_15_minute: 235,
        Interval.in_30_minute: 270,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "AUDCHF": {
        Interval.in_1_minute: 30,
        Interval.in_3_minute: 79,
        Interval.in_5_minute: 125,
        Interval.in_15_minute: 170,
        Interval.in_30_minute: 200,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "GBPUSD": {
        Interval.in_1_minute: 85,
        Interval.in_3_minute: 99,
        Interval.in_5_minute: 125,
        Interval.in_15_minute: 185,
        Interval.in_30_minute: 220,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "AUDJPY": {
        Interval.in_1_minute: 50,
        Interval.in_3_minute: 120,
        Interval.in_5_minute: 170,
        Interval.in_15_minute: 220,
        Interval.in_30_minute: 240,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "GBPAUD": {
        Interval.in_1_minute: 77,
        Interval.in_3_minute: 155,
        Interval.in_5_minute: 215,
        Interval.in_15_minute: 320,
        Interval.in_30_minute: 370,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    },
    "BTCUSD": {
        Interval.in_1_minute: 0,
        Interval.in_3_minute: 0,
        Interval.in_5_minute: 0,
        Interval.in_15_minute: 0,
        Interval.in_30_minute: 0,
        Interval.in_45_minute: 0,
        Interval.in_1_hour: 0,
        Interval.in_2_hour: 0
    }
}

min_sob_size = {
    Interval.in_1_minute: 10,
    Interval.in_3_minute: 30,
    Interval.in_5_minute: 45,
    Interval.in_15_minute: 68,
    Interval.in_30_minute: 100
}


class Indicator:
    def __init__(self, src, open, close, high, low):
        self.src = src
        self.open = np.array(open)
        self.close = close
        self.high = np.array(high)
        self.low = np.array(low)
        self.name = "indicator"

    def get_signal(self) -> Signal:
        print("no get_signal implemented")
        return NeutralSignal()

    def graph(self):
        print("no graph implemented")


class SuperOrderBlockIndicator(Indicator):
    def __init__(self, src, open, close, high, low, price_data: PriceData, includeDelta=True, obMaxBoxSet=100, fvgMaxBoxSet=100):
        super().__init__(src, open, close, high, low)
        self.src.datetime = pandas.to_datetime(self.src.datetime)
        self.interval = interval_convertor.interval_to_datetime(price_data.interval)
        self.obMaxBoxSet = clamp(obMaxBoxSet, 1, 100)
        self.fvgMaxBoxSet = clamp(fvgMaxBoxSet, 1, 100)
        self.analize_block_delta = price_data.get_real_puncts(sob_dict.get(price_data.symbol).get(price_data.interval))
        self.min_sob_size = price_data.get_real_puncts(min_sob_size.get(price_data.interval))
        self.name = "SuperOrderBlock"
        self.includeDelta = includeDelta

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
        def __init__(self, left=0, top=0, right=0, bottom=0, signal=Signal()):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.signal = signal
            self.is_early_created = False

        def print_info(self):
            print("Created box: ", self.left, self.top, self.right, self.bottom)
            print("Created box: ", self.left, self.top, self.right, self.bottom)

        def set_early_created(self):
            self.is_early_created = True

        def check_signal(self, bar_low, bar_high, bar_date):
            is_price_in_box = (self.top > bar_high > self.bottom) or (self.top > bar_low > self.bottom) #(bar_high > self.top > bar_low) or (bar_high > self.bottom > bar_low)
            #
            is_date_range_in_box = self.left <= bar_date <= self.right
            return self.signal if (is_price_in_box and is_date_range_in_box and not self.is_early_created) else NeutralSignal()

    def pivot_high(self, price):
        highs = {}
        prices_count = len(price) - 1
        nearest_high_price = price[prices_count]
        for i in range(prices_count - 1, 0, -1):
            if price[i - 1] < price[i] > price[i + 1]:
                nearest_high_price = price[i]
            highs.update({i: nearest_high_price})
        highs.update({0: nearest_high_price})
        return highs

    def pivot_low(self, price):
        lows = {}
        prices_count = len(price) - 1
        nearest_low_price = price[prices_count]
        for i in range(prices_count - 1, 0, -1):
            if price[i - 1] > price[i] < price[i + 1]:
                nearest_low_price = price[i]
            lows.update({i: nearest_low_price})
        lows.update({0: nearest_low_price})
        return lows

    def control_box(self, boxes, high, low, box_index):
        dt = self.src.datetime[box_index]
        for i in range(len(boxes) - 1, 0, -1):
            is_price_in_box = (high > boxes[i].bottom > low) or (high > boxes[i].top > low)
            if dt == boxes[i].right and not is_price_in_box:
                boxes[i].right = dt + self.interval

    def is_block_in_range(self, block, low_price, high_price):
        return (block.top >= low_price) and (high_price >= block.bottom)

    def is_closing_block_nearby(self, signal, unclosed_blocks):
        if signal.type == NeutralSignal().type:
            return False
        elif signal.type == LongSignal().type:
            analize_range = self.close[0] + self.analize_block_delta
            for block in unclosed_blocks:
                if not (block.signal.type == ShortSignal().type):
                    continue
                if self.is_block_in_range(block, self.close[0], analize_range):
                    return True
        elif signal.type == ShortSignal().type:
            analize_range = self.close[0] - self.analize_block_delta
            for block in unclosed_blocks:
                if not (block.signal.type == LongSignal().type):
                    continue
                if self.is_block_in_range(block, analize_range, self.close[0]):
                    return True
        return False

    def get_signal(self):
        _bearBoxesOB = []
        _bullBoxesOB = []
        _bearBoxesFVG = []
        _bullBoxesFVG = []

        prices_count = len(self.src)-3

        bear_boxes_index_OB = 0
        bull_boxes_index_OB = 0
        bear_boxes_index_FVG = 0
        bull_boxes_index_FVG = 0

        last_added_box_index = 0
        for i in range(0, prices_count+1):
            # # # # # # # # # # # Order Block # # # # # # # # #
            right = self.src.datetime[i]
            left = right - self.interval * 2

            h2 = self.high[i + 1]
            l2 = self.low[i + 1]
            _left = right - self.interval

            if self.is_ob_box_up(i) and bull_boxes_index_OB <= self.obMaxBoxSet:
                _t = h2
                _b = min(l2, self.low[i])
                if _t-_b >= self.min_sob_size:
                    _bullboxOB = self.Box(left=_left, top=_t, right=right, bottom=_b, signal=LongSignal())
                    _bullBoxesOB.append(_bullboxOB)
                    bull_boxes_index_OB += 1
                    last_added_box_index = i

            if self.is_ob_box_down(i) and bear_boxes_index_OB <= self.obMaxBoxSet:
                _t = max(h2, self.high[i])
                _b = l2
                if _t-_b >= self.min_sob_size:
                    _bearboxOB = self.Box(left=_left, top=_t, right=right, bottom=_b, signal=ShortSignal())
                    _bearBoxesOB.append(_bearboxOB)
                    bear_boxes_index_OB += 1
                    last_added_box_index = i

            # # # # # # # # # Fair Value Gap # # # # # # # # #
            h = self.high[i]
            l = self.low[i]

            if self.is_fvg_box_up(i) and bull_boxes_index_FVG <= self.fvgMaxBoxSet:
                t = l
                b = self.high[i + 2]
                if t-b >= self.min_sob_size:
                    _bullboxFVG = self.Box(left=left, top=t, right=right, bottom=b, signal=LongSignal())
                    _bullBoxesFVG.append(_bullboxFVG)
                    bull_boxes_index_FVG += 1
                    last_added_box_index = i

            if self.is_fvg_box_down(i) and bear_boxes_index_FVG <= self.fvgMaxBoxSet:
                t = self.low[i + 2]
                b = h
                if t-b >= self.min_sob_size:
                    _bearboxFVG = self.Box(left=left, top=t, right=right, bottom=b, signal=ShortSignal())
                    _bearBoxesFVG.append(_bearboxFVG)
                    bear_boxes_index_FVG += 1
                    last_added_box_index = i

        for i, box in enumerate(_bullBoxesOB):
            if _bullBoxesOB[i].right == self.src.datetime[0]:
                _bullBoxesOB[i].set_early_created()
                continue
            _bullBoxesOB[i].right += self.interval
        for i, box in enumerate(_bearBoxesOB):
            if _bearBoxesOB[i].right == self.src.datetime[0]:
                _bearBoxesOB[i].set_early_created()
                continue
            _bearBoxesOB[i].right += self.interval

        boxes = _bullBoxesOB + _bearBoxesOB + _bullBoxesFVG + _bearBoxesFVG
        for i in range(last_added_box_index, -1, -1):
            h = self.high[i]
            l = self.low[i]
            if i > 0:
                self.control_box(boxes, h, l, i)

        right = self.src.datetime[0]

        not_closed_boxes = []
        return_signal = NeutralSignal()
        signal_boxes = []

        for box in boxes:
            signal = box.check_signal(self.low[0], self.high[0], right)
            if not (signal.type == NeutralSignal.type):
                signal_boxes.append(box)

        for box in boxes:
            if box.right == self.src["datetime"][0]:
                not_closed_boxes.append(box)

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
            return_signal = biggest_box.signal

        if self.includeDelta and self.is_closing_block_nearby(return_signal, not_closed_boxes):
            return NeutralSignal()

        # self.graph(boxes)
        return return_signal

    def graph(self, boxes):
        unclosed_boxes_scatter = []
        for box in boxes:
            unclosed_boxes_scatter.append(go.Scatter(x=[box.left, box.left, box.right, box.right, box.left],
                                                     y=[box.bottom, box.top, box.top, box.bottom, box.bottom],
                                                     fill="toself", fillcolor='rgba(0, 255, 0,0.1)'))
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
        fig = go.Figure(
            data=[
                go.Candlestick(
                    x=self.src["datetime"],
                    open=self.src["open"],
                    high=self.src["high"],
                    low=self.src["low"],
                    close=self.src["close"]
                ),
                *unclosed_boxes_scatter,
                # *scatters1,
                # *scatters2,
                # *scatters3,
                # *scatters4,
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

        res = np.array([c1 * (p[i] + p[i + 1]) * 0.5 + c2 *
                        res[i + 1] if (i + 1 < len(p)) else 0 +
                        c3 *
                        res[i + 2] if (i + 2 < len(p)) else 0
                        for i in range(len(p) - 2, -1, -1)])
        # for i in range(len(p) - 2, -1, -1):
        #     ssm1 = 0
        #     ssm2 = 0
        #     if i + 1 < len(p):
        #         ssm1 = res[i + 1]
        #     if i + 2 < len(p):
        #         ssm2 = res[i + 2]
        #
        #     res[i] = c1 * (p[i] + p[i + 1]) * 0.5 + c2 * ssm1 + c3 * ssm2
        return res

    def get_signal(self):
        smooth1 = self.smooth(self.fast_line, self.close)
        smooth2 = self.smooth(self.slow_line, self.close)

        macd = (smooth1 - smooth2) * 10000000
        smooth3 = self.smooth(self.smoothness, macd)

        # self.graph(smooth3, macd)
        if macd[0] == smooth3[0]:
            res_signal = LongSignal() if macd[1] > smooth3[1] else (
                ShortSignal() if macd[1] < smooth3[1] else NeutralSignal())
        else:
            res_signal = LongSignal() if macd[0] > smooth3[0] else (
                ShortSignal() if macd[0] < smooth3[0] else NeutralSignal())
        return res_signal

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

        signal = NeutralSignal()
        if buy_signal_count == self.bars_count:
            signal = LongSignal()
        elif sell_signal_count == self.bars_count:
            signal = ShortSignal()

        return signal


class UMAIndicator(Indicator):
    def __init__(self, src, open, close, high, low, rolling=20, smooth=2):
        super().__init__(src, open, close, high, low)
        self.rolling = rolling
        self.smooth = smooth
        self.name = "UMA"

    def get_signal(self):
        avg = self.close.rolling(window=self.rolling).mean()
        avg = avg.shift(periods=-(self.rolling - 1))

        # avg_long = []
        # avg_short = []
        signals = []
        for i in range(0, len(avg), len(avg)):
            if np.isnan(avg[i]) or np.isnan(avg[i + self.smooth]):
                continue

            ma_up = avg[i] > avg[i + self.smooth]
            ma_down = avg[i] < avg[i + self.smooth]
            signals.append(LongSignal() if ma_up else (ShortSignal() if ma_down else NeutralSignal()))
            # avg_long.append(avg[i] if ma_up else 0)
            # avg_short.append(avg[i] if ma_down else 0)
        if len(signals) == 0:
            print("not enough data warning ultimate moving average")
            signals.append(NeutralSignal())

        # self.graph(avg_short, avg_long)
        return signals[0]

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
        return np.exp(-(x*x) / (k * k * 2))
    def old_gauss(self, x, k):
        return math.exp(-(x*x) / (k * k * 2))

    def get_signal(self):
        price_count = min(len(self.close)-2, 499)
        close = np.array(self.close[0:price_count])
        nwe = np.zeros(price_count)

        for i in range(0, price_count):
            x = np.arange(price_count)
            x = i - x
            # sumw = np.array([self.gauss(i - j, self.h) for j in range(0, price_count)])  # np.zeros(price_count)
            sumw = np.array(self.gauss(x, np.array(self.h)))
            sum_ = np.array([close * sumw])  # np.zeros(price_count)

            nwe[i] = np.sum(sum_) / np.sum(sumw)
        sae = np.sum(abs(close - nwe)) / price_count * self.mult


        signals = []
        for i in range(0, price_count):
            if self.close[i] > (nwe[i] + sae) > self.close[i + 1]:
                signals.append((i, ShortSignal()))
                break
            elif self.close[i] < (nwe[i] - sae) < self.close[i + 1]:
                signals.append((i, LongSignal()))
                break
        if len(signals) == 0:
            signals.append((0, NeutralSignal()))
            print(f"not enough data warning {self.name} envelope")

        return signals[0][1]

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


if __name__ == "__main__":
    tv = TvDatafeed()
    interval = Interval.in_1_minute
    currency = "GBPUSD"
    data = tv.get_hist(currency, "OANDA", interval=interval, n_bars=500)
    data = data.reindex(index=data.index[::-1]).iloc[1:].reset_index()

    interval_timedelta = interval_convertor.interval_to_datetime(interval)
    sob = SuperOrderBlockIndicator(data, data.open, data.close, data.high, data.low, interval_timedelta, sob_dict[currency][interval])
    res = sob.get_signal()
