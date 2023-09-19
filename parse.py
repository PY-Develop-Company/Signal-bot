import numpy
from plotly.graph_objs.layout import xaxis
from tvDatafeed import TvDatafeed, Interval
import math
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import pandas as pd
import signal_maker as sm
# from torch import clamp

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
        res = numpy.empty(close_price.shape, dtype=float)

        f = (1.414 * math.pi) / par
        a = math.exp(-f)
        c3 = -a * a
        c2 = 2 * a * math.cos(f)
        c1 = 1 - c2 - c3

        for i in range(len(p)):
            ssm1 = 0
            ssm2 = 0
            if i > 2:
                ssm1 = 0 if numpy.isnan(res[i-1]) else res[i-1]
                ssm2 = 0 if numpy.isnan(res[i-2]) else res[i-2]

            res[i] = c1 * (p[i] + p[i-1]) * 0.5 + c2 * ssm1 + c3 * ssm2
        return res

    smooth1 = smooth(fast_line, close_price)
    smooth2 = smooth(slow_line, close_price)

    macd = (smooth1 - smooth2) * 10000000
    smooth3 = smooth(smoothness, macd)

    return sm.buy_signal if macd[0] > smooth3[0] else sm.sell_signal

def volume():
    pass


#barindex[0] or barindex[-1]
def super_order_block(open, close, high, low, pivotLookup=1,
                      plotOB=True, obBullColor=(0, 255, 0), obBearColor=(255, 0, 0), obMaxBoxSet=10, mitOBColor=(100, 100, 100),
                      plotFVG=True, plotStructureBreakingFVG=True, fvgBullColor=(255,255,255), fvgBearColor=(255,255,255),
                      fvgStructBreakingColor=(0, 0, 255), fvgMaxBoxSet=10, filterMitFVG=False, mitFVGColor=(100,100,100)):
    pass


def ultimate_moving_average(src, rolling=20, smoothe=2):
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

    avg = src["close"].rolling(window=rolling).mean()
    avg = avg.shift(periods=-rolling)

    # avg_red = []
    # avg_green = []
    signals = []
    for i in range(len(avg)):
        if numpy.isnan(avg[i]) or numpy.isnan(avg[i+smoothe]):
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


def nadaraya_watson_envelope():
    pass


if __name__ == '__main__':
    print(ultimate_moving_average(priceData))