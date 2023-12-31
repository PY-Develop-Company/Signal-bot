from indicators_reader import VolumeIndicator, SuperOrderBlockIndicator, ScalpProIndicator, NadarayaWatsonIndicator, \
    UMAIndicator, sob_dict
import interval_convertor
from signals import *
from signals import Signal
from interval_convertor import interval_to_int, str_to_interval
from price_parser import PriceData
import pytz
from datetime import datetime


class Analizer:
    def analize_func(self, df, pd) -> (bool, Signal, str):
        return False, NeutralSignal(), "error"

    async def analize(self, df, pd) -> (bool, Signal, str):
        has_signal, signal, debug_text = self.analize_func(df, pd)
        # print("debug:", debug_text)
        return has_signal, signal, debug_text


class MultitimeframeAnalizer(Analizer):
    def __init__(self, successful_indicators_count, successful_sob_signals_count):
        self.successful_sob_signals_count = successful_sob_signals_count
        self.successful_indicators_count = successful_indicators_count
        self.ma = MainAnalizer(successful_indicators_count)
        self.sob = SOBAnalizer()

    def analize_multitimeframe(self, pds_dfs, analizer: Analizer):
        long_intervals = []
        short_intervals = []
        long_signals_count = 0
        short_signals_count = 0

        for parent_df in pds_dfs.items():
            has_signal, signal, debug = analizer.analize(parent_df[1], parent_df[0])

            if has_signal:
                if signal.type == LongSignal().type:
                    long_intervals.append(parent_df[0].interval)
                    long_signals_count += 1
                elif signal.type == ShortSignal().type:
                    short_intervals.append(parent_df[0].interval)
                    short_signals_count += 1

        return long_signals_count, short_signals_count, long_intervals, short_intervals

    def analize_func(self, parent_dfs, pds) -> (bool, Signal, str, int):
        pds_dfs = dict(zip(pds, parent_dfs))
        sob_long_count, sob_short_count, sob_long_intervals, sob_short_intervals = self.analize_multitimeframe(pds_dfs, self.sob)
        if self.successful_indicators_count > 0:
            has_signal_ma, signal_ma, debug_text_ma = self.ma.analize_func(parent_dfs[0], pds[0])
        # nw_long_count, nw_short_count, nw_long_intervals, nw_short_intervals = self.analize_multitimeframe(pds_dfs, self.nw)
        # uma_long_count, uma_short_count, uma_long_intervals, uma_short_intervals = self.analize_multitimeframe(pds_dfs, self.uma)

        has_signal = False
        signal = NeutralSignal()

        if (sob_long_count >= self.successful_sob_signals_count and sob_short_count == 0) or \
                (sob_short_count >= self.successful_sob_signals_count and sob_long_count == 0):
            has_signal = True
            signal = LongSignal() if sob_long_count > sob_short_count else ShortSignal()

        if has_signal:
            if self.successful_indicators_count > 0:
                if has_signal_ma and signal_ma.type == signal.type:
                    pass
                else:
                    has_signal = False
                    signal = NeutralSignal()
            # if signal.type == LongSignal().type and nw_long_count >= self.successful_indicators_count <= uma_long_count:
            #     pass
            # elif signal.type == ShortSignal().type and nw_short_count >= self.successful_indicators_count <= uma_short_count:
            #     pass
            # else:
            #     has_signal = False
            #     signal = if has_signal:
            # if has_signal_ma and signal_ma.type == signal.type:
            #     pass
            # else:
            #     has_signal = False
            #     signal = NeutralSignal()
            # if signal.type == LongSignal().type and nw_long_count >= self.successful_indicators_count <= uma_long_count:
            #     pass
            # elif signal.type == ShortSignal().type and nw_short_count >= self.successful_indicators_count <= uma_short_count:
            #     pass
            # else:
            #     has_signal = False
            #     signal = NeutralSignal()

        deal_time = 0
        for pd in pds:
            deal_time += interval_to_int(pd.interval)
        deal_time /= 2
        deal_time = int(round(deal_time, 0))

        debug_text = f"""\n\nПроверка сигнала:
                    \tВалютная пара: {pds[0].symbol}" таймфрейми: {[pd.interval for pd in pds]} время свеч: {[df.datetime[0] for df in parent_dfs]}
                    \tЕсть ли сигнал: {has_signal}
                    \tПоказания индикаторов: long_sob_count{sob_long_count} short_sob_count{sob_short_count}
                    \t\t * SOB -> long {sob_long_intervals} short {sob_short_intervals}
                    """
        # \t\t * NW -> long {nw_long_intervals} short {nw_short_intervals}
        # \t\t * UMA -> long {uma_long_intervals} short {uma_short_intervals}\n

        return has_signal, signal, debug_text, deal_time

    def analize(self, parent_dfs, pds) -> (bool, Signal, str, int):
        has_signal, signal, debug, deal_time = self.analize_func(parent_dfs, pds)
        time_zone = pytz.timezone("Europe/Bucharest")
        time_now = datetime.now(time_zone)
        debug += f" time_now {time_now}"
        print(debug)
        return has_signal, signal, debug, deal_time


class MainAnalizer(Analizer):
    def __init__(self, successful_indicators_count):
        self.successful_indicators_count = successful_indicators_count

    def analize_func(self, df, pd) -> (bool, Signal, str):
        interval_td = interval_convertor.interval_to_datetime(pd.interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(pd.interval)

        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low, 16, 12, 16)
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low, rolling=5)
        # sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta)
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low)

        indicators_signals = {
            # "sob": sob_ind.get_signal(),
            "volume": volume_ind.get_signal(),
            "uma": uma_ind.get_signal(),
            "sp": sp_ind.get_signal(),
            "nw": nw_ind.get_signal()
        }

        signal_counts = {LongSignal.type: [0, [], LongSignal()], ShortSignal.type: [0, [], ShortSignal()],
                         NeutralSignal.type: [0, [], NeutralSignal()]}
        for ind_signal in indicators_signals.items():
            signal_counts.get(ind_signal[1].type)[0] += 1
            signal_counts.get(ind_signal[1].type)[1].append(ind_signal[0])

        main_signal = (NeutralSignal.type, [0, [], NeutralSignal()])
        for signal_count in signal_counts.items():
            if signal_count[1][0] > main_signal[1][0] and not (signal_count[0] == NeutralSignal.type):
                main_signal = signal_count

        has_signal = main_signal[1][0] >= self.successful_indicators_count # and indicators_signals.get("sob").type == main_signal[0]

        debug_dict = {}
        for sig in signal_counts.items():
            debug_dict[sig[1][2].text] = sig[1][:2]
        debug_text = f"""\n\nПроверка сигнала:
            \tВалютная пара: {df.symbol[0]}" таймфрейм: {pd.interval} время свечи: {df.datetime[0]}
            \tЕсть ли сигнал: {has_signal}
            \tПоказания индикаторов: {debug_dict})\n
            """
        if has_signal:
            return True, main_signal[1][2], debug_text
        return False, NeutralSignal(), debug_text

    def analize(self, df, interval) -> (bool, Signal, str):
        has_signal, signal, debug_text = self.analize_func(df, interval)
        return has_signal, signal, debug_text


class NoDeltaSOBAnalizer(Analizer):
    def analize_func(self, df, pd: PriceData) -> (bool, Signal, str):
        interval_td = interval_convertor.interval_to_datetime(pd.interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(pd.interval)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta, includeDelta=False)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"

    def analize(self, df, interval) -> (bool, Signal, str):
        return self.analize_func(df, interval)


class SOBAnalizer(Analizer):
    def analize_func(self, df, pd: PriceData) -> (bool, Signal, str):
        interval_td = interval_convertor.interval_to_datetime(pd.interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(pd.interval)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"

    def analize(self, df, pd) -> (bool, Signal, str):
        return self.analize_func(df, pd)


class VolumeAnalizer(Analizer):
    def __init__(self, bars_count):
        self.bc = bars_count

    def analize_func(self, df, pd) -> (bool, Signal, str):
        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low, self.bc)
        signal = volume_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class SPAnalizer(Analizer):
    def __init__(self, fast, slow, smooth):
        self.fast = fast
        self.slow = slow
        self.smooth = smooth

    def analize_func(self, df, pd) -> (bool, Signal, str):
        # 16 12 16
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low, self.fast, self.slow, self.smooth)
        signal = sp_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class UMAAnalizer(Analizer):

    def __init__(self, rolling):
        self.rolling_count = rolling

    def analize_func(self, df, pd) -> (bool, Signal, str):
        # 5
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low, rolling=self.rolling_count)
        signal = uma_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class NWAnalizer(Analizer):
    def __init__(self, mult):
        self.mult = mult

    def analize_func(self, df, pd) -> (bool, Signal, str):
        # 2
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low, mult= self.mult)
        signal = nw_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"
