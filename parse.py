import numpy as np
from tvDatafeed import TvDatafeed, Interval
import math
import signal_maker as sm

def clamp(value, min_value, max_value):
    return max(min(value, max_value), min_value)

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

tv = TvDatafeed()
symbol = 'NIFTY'
exchange = 'NSE'


priceData = tv.get_hist(symbol=symbol, exchange=exchange, interval=Interval.in_5_minute, n_bars=1000)
priceData = priceData.reindex(index=priceData.index[::-1]).reset_index()
# priceData = priceData.set_index("datetime")
# print(priceData.head())


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


#barindex[0] or barindex[-1]
def super_order_block(open, close, high, low, pivotLookup=1,
                      plotOB=True, obBullColor=(0, 255, 0), obBearColor=(255, 0, 0), obMaxBoxSet=10, mitOBColor=(100, 100, 100),
                      plotFVG=True, plotStructureBreakingFVG=True, fvgBullColor=(255,255,255), fvgBearColor=(255,255,255),
                      fvgStructBreakingColor=(0, 0, 255), fvgMaxBoxSet=10, filterMitFVG=False, mitFVGColor=(100,100,100)):
    pass

    # pivotLookup = clamp(pivotLookup, 1, 5)
    # obMaxBoxSet = clamp(obMaxBoxSet, 1, 100)
    # fvgMaxBoxSet = clamp(fvgMaxBoxSet, 1, 100)
    #
    # # Box Types
    # _ob = 1
    # _fvg = 2
    #
    # # Box Arrays
    # _bearBoxesOB = []
    # _bullBoxesOB = []
    # _bearBoxesFVG = []
    # _bullBoxesFVG = []
    #
    #
    # class Box():
    #     def __init__(self, left=0, top=0, right=0, bottom=0, type="box"):
    #         self.left = left
    #         self.top = top
    #         self.right = right
    #         self.bottom = bottom
    #         self.type = type
    #         print("Created", "l=", left, "r=", right, "t=", top, "bottom=", bottom, "type=", type)
    #     def signal(self, bar_close, bar_date):
    #         return bottom < bar_close < top
    #
    # # Functions
    # def is_up_bar(index):
    #     return close[index] > open[index]
    #
    #
    # def is_down_bar(index):
    #     return close[index] < open[index]
    #
    # def is_ob_box_up(index):
    #     return is_down_bar(index + 1) and is_up_bar(index) and close[index] > high[index + 1]
    #
    # def is_ob_box_down(index):
    #     return is_up_bar(index + 1) and is_down_bar(index) and close[index] < low[index + 1]
    #
    # def is_fvg_box_up(index):
    #     return low[index] > high[index + 2]
    #
    # def is_fvg_box_down(index):
    #     return high[index] < low[index + 2]
    #
    # # Function to Calculte Box Length
    # def controlBox(_boxes, _high, _low, _type):
    #     if len(_boxes) > 0:
    #         for i in range(len(_boxes)-1, 0):
    #             _box = _boxes[i]
    #             _boxLow = _box.bottom
    #             _boxHigh = _box.top
    #             _boxRight = _box.right
    #             if None or (bar_index == _boxRight and not ((_high > _boxLow and _low < _boxLow) or (_high > _boxHigh and _low < _boxHigh))):
    #                 _box.right = bar_index + 1
    #
    # # # # # # # # # # # Pivots # # # # # # # # # #
    # def pivot_high(source, leftbars, rightbars):
    #     pivot_highs = []
    #     for i in range(len(source)):
    #          if i+rightbars >= len(source) or i-leftbars < 0:
    #              continue
    #          if (source[i] > source[i+rightbars]) and (source[i] > source[i-leftbars]):
    #              pivot_highs.append(source[i])
    #     return pivot_highs
    # def pivot_low(source, leftbars, rightbars):
    #     pivot_lows = []
    #     for i in range(len(source)):
    #         if i + rightbars >= len(source) or i - leftbars < 0:
    #             continue
    #         if (source[i] < source[i+rightbars]) and (source[i] < source[i-leftbars]):
    #             pivot_lows.append(source[i])
    #     return pivot_lows
    #
    # def value_when(condition, source):
    #     result = []
    #     y = len(condition)-1
    #     for i in range(len(source), 0, -1):
    #         if condition[y] == source[i-1]:
    #             result.append(source[i-1])
    #             y = clamp(y-1, 0, y)
    #         elif len(result) == 0:
    #             result.append(0)
    #         else:
    #             result.append(result[-1])
    #     return result
    #
    #
    # def del_box(boxes, box):
    #     boxes.remove(box)
    #
    # hih = pivot_high(high, pivotLookup, pivotLookup)
    # lol = pivot_low(low, pivotLookup, pivotLookup)
    # top = value_when(hih, high)
    # bottom = value_when(lol, low)
    #
    # # # # # # # # # # # # Order Block # # # # # # # # #
    # # Bullish OB Box Plotting
    # if is_ob_box_up(1) and plotOB:
    #     _bullboxOB = Box(left=bar_index[0] - 2, top=high[2], right=bar_index[0], bottom=math.min(low[2], low[1]), type="OB+")
    #     if len(_bullBoxesOB) > obMaxBoxSet:
    #         del_box(_bullBoxesOB, _bullBoxesOB[0])
    #     _bullBoxesOB.append(_bullboxOB)
    #
    # # Bearish OB Box Plotting
    # if is_ob_box_down(1) and plotOB:
    #     _bearboxOB = Box(left=bar_index[0] - 2, top=math.max(high[2], high[1]), right=bar_index[0], bottom=low[2], type="OB-")
    #     if len(_bearBoxesOB) > obMaxBoxSet:
    #         del_box(_bearBoxesOB[0])
    #     _bearBoxesOB.append(_bearboxOB)
    #
    # if plotOB:
    #     controlBox(_bearBoxesOB, high, low, _ob)
    #     controlBox(_bullBoxesOB, high, low, _ob)
    #
    # # # # # # # # # # # Fair Value Gap # # # # # # # # #
    # # Bullish FVG Box Plotting
    # if is_fvg_box_up(0):
    #     _bullboxFVG = None
    #     if plotStructureBreakingFVG and (close[-1] > top) and (low[-1] < top) and (high[-2] < top) and (low > top):
    #         _bullboxFVG = Box(left=bar_index[0] - 2, top=low[0], right=bar_index[0], bottom=high[2], type="FVG+")
    #     elif plotFVG:
    #         _bullboxFVG = Box(left=bar_index[0] - 2, top=low[0], right=bar_index[0], bottom=high[2], type="FVG+")
    #     if len(_bullBoxesFVG) > fvgMaxBoxSet:
    #         del_box(_bullBoxesFVG[0])
    #     _bullBoxesFVG.append(_bullboxFVG)
    #
    # # Bearish FVG Box Plotting
    # if is_fvg_box_down(0):
    #     _bearboxFVG = None
    #     if plotStructureBreakingFVG and (close[1] < bottom) and (high[1] > bottom) and (low[2] > bottom) and (high < bottom):
    #         _bearboxFVG = Box(left=bar_index[0] - 2, top=low[2], right=bar_index[0], bottom=high[0], type="FVG-")
    #     elif plotFVG:
    #             _bearboxFVG = Box(left=bar_index[0] - 2, top=low[2], right=bar_index[0], bottom=high[0], type="FVG-")
    #     if len(_bearBoxesFVG) > fvgMaxBoxSet:
    #         del_box(_bearBoxesFVG[0])
    #     _bearBoxesFVG.append(_bearboxFVG)
    #
    #     if plotFVG or plotStructureBreakingFVG:
    #         controlBox(_bearBoxesFVG, high[0], low[0], _fvg)
    #         controlBox(_bullBoxesFVG, high[0], low[0], _fvg)


def ultimate_moving_average(close_price, rolling=20, smoothe=2):
    # def sma(x, y):
    #     sum = 0.0
    #     for i in range(0, y):
    #         sum += x[i] / y
    #
    #     return sum
    #
    # def ema(src, length):
    #     alpha = 2 / (length + 1)
    #     sum = sma(src, length) if (sum[1] == None) else alpha * src[0] + (1 - alpha) * sum[1]
    #     return sum

    avg = close_price.rolling(window=rolling).mean()
    avg = avg.shift(periods=-rolling)

    # avg_red = []
    # avg_green = []
    signals = []
    for i in range(len(avg)):
        if np.isnan(avg[i]) or np.isnan(avg[i+smoothe]):
            continue

        ma_up = avg[i] >= avg[i+smoothe]
        # ma_down = avg[i] < avg[i+smoothe]

        signals.append(sm.buy_signal if ma_up else sm.sell_signal)
        # if ma_up:
        #     avg_red.append((avg.index, 0))
        #     avg_green.append((avg.index, avg[i]))
        # if ma_down:
        #     avg_red.append((avg.index, avg[i]))
        #     avg_green.append((avg.index, 0))

    # z_avg_red = list(zip(*avg_red))
    # avg_red = pd.Series(z_avg_red[1], index=z_avg_red[0])
    # z_avg_green = list(zip(*avg_green))
    # avg_green = pd.Series(z_avg_green[1], index=z_avg_green[0])
    #
    # fig = go.Figure(
    #     data=[
    #         go.Candlestick(
    #             x=src["datetime"],
    #             open=src["open"],
    #             high=src["high"],
    #             low=src["low"],
    #             close=src["close"]
    #         ),
    #
    #         go.Scatter(
    #             x=src["datetime"],
    #             y=avg_red,
    #             mode='lines',
    #             name='red_signal',
    #             line={'color': '#eb3434'}
    #         )
    #     ]
    # )
    # fig.update_layout(
    #     title=f'The Candlestick graph for {symbol}',
    #     xaxis_title='Date',
    #     yaxis_title=f'Price ({exchange})',
    #     xaxis_rangeslider_visible=False,
    #     xaxis=dict(type="category")
    # )
    #
    # fig.show()

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
    print(volume(priceData.open, priceData.close))