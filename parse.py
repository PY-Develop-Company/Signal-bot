import numpy
from tvDatafeed import TvDatafeed, Interval
import math

username = 't4331662@gmail.com'
password = 'Pxp626AmH7_'

tv = TvDatafeed()

priceData = tv.get_hist(symbol='NIFTY', exchange='NSE', interval=Interval.in_1_hour, n_bars=1000)

# tv = TvDatafeed()
# print(tv.search_symbol('EURUSD'))


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

    "Fast Line"
    "Slow Line"
    "Smoothness"
    smooth1 = smooth(fast_line, close_price)
    smooth2 = smooth(slow_line, close_price)

    macd = (smooth1 - smooth2) * 10000000
    smooth3 = smooth(smoothness, macd)

    return macd[-1] > smooth3[-1]


def volume():
    pass


def super_order_block():
    pass


def ultimate_moving_average():
    pass


def nadaraya_watson_envelope():
    pass


# print('Buy' if scalp_pro(priceData.close.to_numpy()) else 'Sell')
