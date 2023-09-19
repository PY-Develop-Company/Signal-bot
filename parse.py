import numpy as np
from tvDatafeed import TvDatafeed, Interval
import math
import signal_maker as sm
from datetime import timedelta


def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)


def get_datetime(interval):
    if interval == Interval.in_3_minute:
        return timedelta(minutes=3)
    elif interval == Interval.in_5_minute:
        return timedelta(minutes=5)
    elif interval == Interval.in_15_minute:
        return timedelta(minutes=15)
    else:
        return timedelta(days=1)


def get_price_data(symbol='NIFTY', exchange='NSE', interval=Interval.in_5_minute, username='t4331662@gmail.com', password='Pxp626AmH7_'):
    tv = TvDatafeed()
    # tv = TvDatafeed(username=username, password=password)

    priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=interval, n_bars=1000)
    priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
    # priceData = priceData.set_index("datetime")
    # print(priceData.head())
    # priceData.info()
    return priceData


def scalp_pro(close_price, fast_line=8, slow_line=10, smoothness=8):
    def smooth(par, p):
        res = np.empty(close_price.shape, dtype=float)

        f = (1.414 * math.pi) / par
        a = math.exp(-f)
        c3 = -a * a
        c2 = 2 * a * math.cos(f)
        c1 = 1 - c2 - c3

        for i in range(1, len(p)):
            ssm1 = 0
            ssm2 = 0
            if i > 2:
                ssm1 = 0 if np.isnan(res[i-1]) else res[i-1]
                ssm2 = 0 if np.isnan(res[i-2]) else res[i-2]

            res[i] = c1 * (p[i] + p[i-1]) * 0.5 + c2 * ssm1 + c3 * ssm2
        return res

    smooth1 = smooth(fast_line, close_price)
    smooth2 = smooth(slow_line, close_price)

    macd = (smooth1 - smooth2) * 10000000
    smooth3 = smooth(smoothness, macd)

    return sm.buy_signal if macd[0] > smooth3[0] else sm.sell_signal


def volume(open, close, bars_count=3):
    buy_signal_count = 0
    sell_signal_count = 0
    for i in range(bars_count):
        if open[i] <= close[i]:
            buy_signal_count += 1
        else:
            sell_signal_count += 1

    if buy_signal_count == bars_count:
        return sm.buy_signal
    elif sell_signal_count == bars_count:
        return sm.sell_signal
    else:
        return sm.neutral_signal


def super_order_block(src, open, close, high, low, interval, obMaxBoxSet=10, fvgMaxBoxSet=10):
    obMaxBoxSet = clamp(obMaxBoxSet, 1, 100)
    fvgMaxBoxSet = clamp(fvgMaxBoxSet, 1, 100)

    # Box Arrays
    _bearBoxesOB = []
    _bullBoxesOB = []
    _bearBoxesFVG = []
    _bullBoxesFVG = []

    class Box:
        def __init__(self, left=0, top=0, right=0, bottom=0, signal_type="box"):
            self.left = left
            self.top = top
            self.right = right
            self.bottom = bottom
            self.signal_type = signal_type

        def check_signal(self, bar_low, bar_high, bar_date):
            is_price_in_box = not ((bar_high > self.top and bar_low > self.top) or (bar_high < self.bottom and bar_low < self.bottom))
            is_date_range_in_box = self.left <= bar_date <= self.right
            return self.signal_type if is_price_in_box and is_date_range_in_box else sm.neutral_signal

    def is_up_bar(index):
        return close[index] > open[index]

    def is_down_bar(index):
        return close[index] < open[index]

    def is_ob_box_up(index):
        return is_down_bar(index + 1) and is_up_bar(index) and close[index] > high[index + 1]

    def is_ob_box_down(index):
        return is_up_bar(index + 1) and is_down_bar(index) and close[index] < low[index + 1]

    def is_fvg_box_up(index):
        return low[index] > high[index + 2]

    def is_fvg_box_down(index):
        return high[index] < low[index + 2]

    def pivot_high(price, date):
        highs = {}
        nearest_high_price = price[100]
        for i in range(100, 0, -1):
            if i-1 > 0 and price[i-1] < price[i] > price[i+1]:
                nearest_high_price = price[i]
            highs.update({i: nearest_high_price})
        return highs

    def pivot_low(price, date):
        lows = {}
        nearest_low_price = price[100]
        for i in range(100, 0, -1):
            if i-1 > 0 and price[i-1] > price[i] < price[i+1]:
                nearest_low_price = price[i]
            lows.update({i: nearest_low_price})
        return lows

    def controlBox(boxes, high, low, box_index):
        for i in range(len(boxes)-1, 0, -1):
            is_price_in_box = (high > boxes[i].bottom and low < boxes[i].bottom) or (high > boxes[i].top and low < boxes[i].top)
            if src.datetime[box_index] == boxes[i].right and not is_price_in_box:
                boxes[i].right = src.datetime[box_index] + get_datetime(interval)

    top = pivot_high(high, src.datetime)
    bottom = pivot_low(low, src.datetime)

    # # # # # # # # # # # Order Block # # # # # # # # #
    for i in range(100, 0, -1):
        if is_ob_box_up(i+1):
            _bullboxOB = Box(left=src.datetime[i] - get_datetime(interval)*2, top=high[i+2], right=src.datetime[i], bottom=min(low[i+2], low[i+1]), signal_type=sm.buy_signal)
            if len(_bullBoxesOB) > obMaxBoxSet:
                _bullBoxesOB.remove(_bullBoxesOB[0])
            _bullBoxesOB.append(_bullboxOB)

        if is_ob_box_down(i+1):
            _bearboxOB = Box(left=src.datetime[i] - get_datetime(interval)*2, top=max(high[i+2], high[i+1]), right=src.datetime[i], bottom=low[i+2], signal_type=sm.sell_signal)
            if len(_bearBoxesOB) > obMaxBoxSet:
                _bearBoxesOB.remove(_bearBoxesOB[0])
            _bearBoxesOB.append(_bearboxOB)

        controlBox(_bearBoxesOB, high[i], low[i], i)
        controlBox(_bullBoxesOB, high[i], low[i], i)

    # # # # # # # # # # Fair Value Gap # # # # # # # # #
    for i in range(100, 0, -1):
        if is_fvg_box_up(i):
            _bullboxFVG = None
            if (close[i+1] > top[i]) and (low[i+1] < top[i]) and (high[i+2] < top[i]) and (low[i] > top[i]):
                _bullboxFVG = Box(left=src.datetime[i] - get_datetime(interval)*2, top=low[i], right=src.datetime[i], bottom=high[i+2], signal_type=sm.buy_signal)
            else:
                _bullboxFVG = Box(left=src.datetime[i] - get_datetime(interval)*2, top=low[i], right=src.datetime[i], bottom=high[i+2], signal_type=sm.buy_signal)

            if len(_bullBoxesFVG) > fvgMaxBoxSet:
                _bullBoxesFVG.remove(_bullBoxesFVG[0])
            _bullBoxesFVG.append(_bullboxFVG)

        if is_fvg_box_down(i):
            _bearboxFVG = None
            if (close[i+1] < bottom[i]) and (high[i+1] > bottom[i]) and (low[i+2] > bottom[i]) and (high[i] < bottom[i]):
                _bearboxFVG = Box(left=src.datetime[i] - get_datetime(interval)*2, top=low[i+2], right=src.datetime[i], bottom=high[i], signal_type=sm.sell_signal)
            else:
                _bearboxFVG = Box(left=src.datetime[i] - get_datetime(interval)*2, top=low[i+2], right=src.datetime[i], bottom=high[i], signal_type=sm.sell_signal)
            if len(_bearBoxesFVG) > fvgMaxBoxSet:
                _bearBoxesFVG.remove(_bearBoxesFVG[0])
            _bearBoxesFVG.append(_bearboxFVG)

        controlBox(_bearBoxesFVG, high[i], low[i], i)
        controlBox(_bullBoxesFVG, high[i], low[i], i)

    for box in _bullBoxesOB:
        signal = box.check_signal(low[0], high[0], src.datetime[0])
        if not signal == sm.neutral_signal:
            return signal
    for box in _bearBoxesOB:
        signal = box.check_signal(low[0], high[0], src.datetime[0])
        if not signal == sm.neutral_signal:
            return signal
    for box in _bullBoxesFVG:
        signal = box.check_signal(low[0], high[0], src.datetime[0])
        if not signal == sm.neutral_signal:
            return signal
    for box in _bearBoxesFVG:
        signal = box.check_signal(low[0], high[0], src.datetime[0])
        if not signal == sm.neutral_signal:
            return signal
    return sm.neutral_signal


def ultimate_moving_average(close_price, rolling=20, smoothe=2):
    avg = close_price.rolling(window=rolling).mean()
    avg = avg.shift(periods=-rolling)

    signals = []
    for i in range(len(avg)):
        if np.isnan(avg[i]) or np.isnan(avg[i+smoothe]):
            continue

        ma_up = avg[i] >= avg[i+smoothe]
        signals.append(sm.buy_signal if ma_up else sm.sell_signal)

    return signals[0]


def nadaraya_watson_envelope(close_price, h=8.0, mult=3.0):
    gauss = lambda x, h: math.exp(-(math.pow(x, 2) / (h * h * 2)))

    nwe = []
    sae = 0
    for i in range(0, 500):
        sum = 0.0
        sumw = 0.0

        for j in range(0, 500):
            w = gauss(i - j, h)
            sum += close_price[j] * w
            sumw += w

        y2 = sum/sumw
        sae += abs(close_price[i] - y2)
        nwe.append(y2)

    sae = sae/500 * mult
    signals = []
    for i in range(0, 500):
        if close_price[i] > (nwe[i] + sae) and close_price[i + 1] < (nwe[i] + sae):
            signals.append((i, sm.sell_signal))
        elif close_price[i] < (nwe[i] - sae) and close_price[i + 1] > (nwe[i] - sae):
            signals.append((i, sm.buy_signal))
    return signals[0][1]


if __name__ == '__main__':
    username = 't4331662@gmail.com'
    password = 'Pxp626AmH7_'
    # tv = TvDatafeed()
    # tv = TvDatafeed(username=username, password=password)
    # data = tv.search_symbol("EURUSD")[0]
    # print(data)
    # get_price_data(symbol=data["symbol"], exchange=data["exchange"])
    get_price_data()


