from indicators_reader import VolumeIndicator, SuperOrderBlockIndicator, ScalpProIndicator, NadarayaWatsonIndicator, \
    UMAIndicator, sob_dict
import interval_convertor
from signals import *
from signals import Signal
from interval_convertor import interval_to_int, str_to_interval


class Analizer:
    def analize_func(self, df) -> (bool, Signal, str):
        return False, NeutralSignal(), "error"

    def analize(self, df) -> (bool, Signal, str):
        has_signal, signal, debug_text = self.analize_func(df)
        # print("debug:", debug_text)
        return has_signal, signal, debug_text


class MultitimeframeAnalizer(Analizer):
    def __init__(self, successful_indicators_count, successful_sob_signals_count):
        self.successful_sob_signals_count = successful_sob_signals_count
        self.main = MainAnalizer(successful_indicators_count)
        self.sob = SOBAnalizer()

    def analize_func(self, df, interval, parent_pd_dfs_dict) -> (bool, Signal, str, int, int, int):
        has_signal = False
        signal = NeutralSignal()
        intervals = [interval]

        main_has_signal, main_signal, main_ind_count, main_debug_text = self.main.analize(df, interval)

        sob_signals_count = 0
        if main_has_signal:
            for parent_df in parent_pd_dfs_dict.items():
                sob_has_signal, sob_signal, _ = self.sob.analize(parent_df[1], parent_df[0].interval)

                if sob_has_signal and sob_signal.type == main_signal.type:
                    intervals.append(parent_df[0].interval)
                    sob_signals_count += 1
                    # print("catched sob", parent_df[0].interval)

            if sob_signals_count >= self.successful_sob_signals_count:
                has_signal = True
                signal = main_signal

        # print("calculate dealtime for",df.symbol[0], interval)
        interval_minutes = interval_to_int(interval)
        # print("interval_minutes", interval_minutes)
        deal_time = interval_minutes
        for parent_df in parent_pd_dfs_dict.items():
            deal_time += interval_to_int(parent_df[0].interval)
        # print("deal_time", deal_time)
        deal_time /= 2
        deal_time = int(round(deal_time, 0))
        # print("deal_time_avg", deal_time)
        # print("deal_time_round", deal_time)

        return has_signal, signal, main_debug_text + f"\n SuperOrderBlock на інших таймфреймах: {intervals}", main_ind_count, sob_signals_count, deal_time

    def analize(self, df, interval, parent_pd_dfs_dict) -> (bool, Signal, str, int, int, int):
        has_signal, signal, debug, main_ind_count, sob_signals_count, deal_time = self.analize_func(df, interval, parent_pd_dfs_dict)
        # print(debug)
        return has_signal, signal, debug, main_ind_count, sob_signals_count, deal_time



class MainAnalizer(Analizer):
    def __init__(self, successful_indicators_count):
        self.successful_indicators_count = successful_indicators_count

    def analize_func(self, df, interval) -> (bool, Signal, int, str):
        interval_td = interval_convertor.interval_to_datetime(interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(interval)

        # volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        # sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low, 16, 12, 16)
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta)
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low)

        indicators_signals = {
            "sob": sob_ind.get_signal(),
            # "volume": volume_ind.get_signal(),
            "uma": uma_ind.get_signal(),
            # "sp": sp_ind.get_signal(),
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
        # print("debug:", debug_text)
        return has_signal, signal, ind_count, debug_text


class NoDeltaSOBAnalizer(Analizer):
    def analize_func(self, df, interval) -> (bool, Signal, str):
        interval_td = interval_convertor.interval_to_datetime(interval)
        analize_block_delta = sob_dict.get(df["symbol"][0].split(":")[1]).get(interval)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, interval_td, analize_block_delta, includeDelta=False)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"

    def analize(self, df, interval) -> (bool, Signal, str):
        return self.analize_func(df, interval)


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
        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        signal = volume_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class SPAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 16 12 16
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low, 8, 10, 8)
        signal = sp_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class UMAAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 5
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low, 20)
        signal = uma_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class NWAnalizer(Analizer):
    def analize_func(self, df) -> (bool, Signal, str):
        # 2
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low, mult=3)
        signal = nw_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"
