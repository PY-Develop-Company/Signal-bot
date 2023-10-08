import tvDatafeed

from indicators_reader import VolumeIndicator, SuperOrderBlockIndicator, ScalpProIndicator, NadarayaWatsonIndicator, \
    UMAIndicator, sob_dict
import interval_convertor
from pandas import DataFrame
from signals import *
from datetime import timedelta
from signals import Signal
import price_parser


class Analizer:
    def analize_func(self, df) -> (bool, Signal, str):
        return False, NeutralSignal(), "error"

    def analize(self, df) -> (bool, Signal, str):
        has_signal, signal, debug_text = self.analize_func(df)
        # print("debug:", debug_text)
        return has_signal, signal, debug_text


class MainAnalizer(Analizer):
    def __init__(self, successful_indicators_count):
        self.successful_indicators_count = successful_indicators_count

    def analize_func(self, df, interval) -> (bool, Signal, int, str):
        interval_td = interval_convertor.interval_to_datetime(interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(interval)

        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low)
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta)
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low)

        indicators_signals = {
            "sob": sob_ind.get_signal(),
            "volume": volume_ind.get_signal(),
            "uma": uma_ind.get_signal(),
            "nw": nw_ind.get_signal(),
            "sp": sp_ind.get_signal()
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

        has_signal = main_signal[1][0] >= self.successful_indicators_count and indicators_signals.get("sob").type == \
                     main_signal[0]

        debug_dict = {}
        for sig in signal_counts.items():
            debug_dict[sig[1][2].text] = sig[1][:2]
        debug_text = f"""\n\nПроверка сигнала:
            \tВалютная пара: {df.symbol[0]}" таймфрейм: {interval} время свечи: {df.datetime[0]}
            \tЕсть ли сигнал: {has_signal}
            \tПоказания индикаторов: {debug_dict})\n
            """
        if has_signal:
            return True, main_signal[1][2], main_signal[1][0], debug_text
        return False, NeutralSignal(), 0, debug_text

    def analize(self, df, interval) -> (bool, Signal, int, str):
        has_signal, signal, ind_count, debug_text = self.analize_func(df, interval)
        print("debug:", debug_text)
        return has_signal, signal, ind_count, debug_text


class SOBAnalizer(Analizer):
    def analize_func(self, df, interval) -> (bool, Signal, str):
        interval_td = interval_convertor.interval_to_datetime(interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(interval)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"

    def analize(self, df, interval) -> (bool, Signal, str):
        return self.analize_func(df, interval)


class VolumeAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 2
        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low, bars_count=2)
        signal = volume_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class SPAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 16 12 16
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low, 16, 12, 16)
        signal = sp_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class UMAAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 5
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low, rolling=5)
        signal = uma_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class NWAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 1
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low, mult=2)
        signal = nw_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"
