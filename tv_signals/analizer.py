from tv_signals.indicators_reader import VolumeIndicator, SuperOrderBlockIndicator, ScalpProIndicator, \
    NadarayaWatsonIndicator, UMAIndicator, OBVolumeIndicator

from tv_signals.signal_types import *
from tv_signals.price_parser import PriceData

from utils.interval_convertor import interval_to_int
from utils.time import now_time


def has_multitimeframe_signal(needed_count, long_count, short_count):
    is_long = long_count >= needed_count and short_count == 0
    is_short = short_count >= needed_count and long_count == 0
    return is_long, is_short


def get_deal_time(pds):
    deal_time = 0
    for pd in pds:
        deal_time += interval_to_int(pd.interval)
    deal_time /= 2
    deal_time = int(round(deal_time, 0))
    return deal_time


class Analizer:
    def analize_func(self, df, pd) -> (bool, Signal, str):
        return False, NeutralSignal(), "error"

    def analize(self, df, pd) -> (bool, Signal, str):
        has_signal, signal, debug_text = self.analize_func(df, pd)
        # print("debug:", debug_text)
        return has_signal, signal, debug_text


class MultitimeframeAnalizer(Analizer):
    def __init__(self, successful_indicators_count, successful_sob_signals_count):
        self.successful_sob_signals_count = successful_sob_signals_count
        self.successful_indicators_count = successful_indicators_count
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
        has_signal = False
        signal = NeutralSignal()

        is_long, is_sort = has_multitimeframe_signal(self.successful_sob_signals_count, sob_long_count, sob_short_count)
        if is_long or is_sort:
            has_signal = True
            signal = LongSignal() if is_long else ShortSignal()

        deal_time = get_deal_time(pds)

        debug_text = f"""\n\nПроверка сигнала:
                    \tВалютная пара: {pds[0].symbol}" таймфрейми: {[pd.interval for pd in pds]} время свеч: {[df.datetime[0] for df in parent_dfs]}
                    \tЕсть ли сигнал: {has_signal}
                    \tПоказания индикаторов: long_sob_count{sob_long_count} short_sob_count{sob_short_count}
                    \t\t * SOB -> long {sob_long_intervals} short {sob_short_intervals}
                    """

        return has_signal, signal, debug_text, deal_time

    def analize(self, parent_dfs, pds) -> (bool, Signal, str, int):
        has_signal, signal, debug, deal_time = self.analize_func(parent_dfs, pds)
        debug += f" time_now {now_time()}"

        return has_signal, signal, debug, deal_time


class NewMultitimeframeAnalizer(Analizer):
    def __init__(self, vob_count, sob_count):
        self.vob_count = vob_count
        self.sob_count = sob_count

        self.sob = SOBAnalizer()
        self.vob = VOBAnalizer()

    def analize_multitimeframe(self, pds_dfs, analizer: Analizer):
        long_intervals = []
        short_intervals = []
        long_signals_count = 0
        short_signals_count = 0
        debugs = []
        for parent_df in pds_dfs.items():
            has_signal, signal, debug = analizer.analize(parent_df[1], parent_df[0])
            debugs.append(debug)

            if has_signal:
                if signal.type == LongSignal().type:
                    long_intervals.append(parent_df[0].interval)
                    long_signals_count += 1
                elif signal.type == ShortSignal().type:
                    short_intervals.append(parent_df[0].interval)
                    short_signals_count += 1

        return long_signals_count, short_signals_count, long_intervals, short_intervals, debugs

    def analize_func(self, parent_dfs, pds) -> (bool, Signal, str, int):
        pds_dfs = dict(zip(pds, parent_dfs))
        sob_long_count, sob_short_count, sob_long_intervals, sob_short_intervals, sob_debugs = self.analize_multitimeframe(pds_dfs, self.sob)
        vob_long_count, vob_short_count, vob_long_intervals, vob_short_intervals, vob_debugs = self.analize_multitimeframe(pds_dfs, self.vob)
        has_signal = False
        signal = NeutralSignal()

        sob_is_long, sob_is_short = has_multitimeframe_signal(self.sob_count, sob_long_count, sob_short_count)
        vob_is_long, vob_is_short = has_multitimeframe_signal(self.vob_count, vob_long_count, vob_short_count)
        if (sob_is_long and vob_is_long) or (sob_is_short and vob_is_short):
            has_signal = True
            signal = LongSignal() if sob_long_count > sob_short_count else ShortSignal()
        # if vob_is_long or vob_is_short:
        #     has_signal = True
        #     signal = LongSignal() if vob_long_count > vob_short_count else ShortSignal()

        deal_time = get_deal_time(pds)

        debug_text = f"""\n\nПроверка сигнала:
                            \tВалютная пара: {pds[0].symbol}" таймфрейми: {[pd.interval for pd in pds]} время свеч: {[df.datetime[0] for df in parent_dfs]}
                            \tЕсть ли сигнал: {has_signal}
                            \tПоказания индикаторов: long_sob_count{sob_long_count} short_sob_count{sob_short_count} long_vob_count{vob_long_count} short_vob_count{vob_short_count}
                            \t\t * SOB -> long {sob_long_intervals} short {sob_short_intervals}
                            \t\t * VOB -> long {vob_long_intervals} short {vob_short_intervals}
                            \n vob debugs{vob_debugs}"""

        return has_signal, signal, debug_text, deal_time

    def analize(self, parent_dfs, pds) -> (bool, Signal, str, int):
        has_signal, signal, debug_text, deal_time = self.analize_func(parent_dfs, pds)
        print(debug_text)
        return has_signal, signal, debug_text, deal_time


class MainAnalizer(Analizer):
    def __init__(self, successful_indicators_count):
        self.successful_indicators_count = successful_indicators_count

    def analize_func(self, df, pd) -> (bool, Signal, str):
        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low)
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low)
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, pd)
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low)

        indicators_signals = {
            "sob": sob_ind.get_signal(),
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

        has_signal = main_signal[1][0] >= self.successful_indicators_count and indicators_signals.get("sob").type == \
                     main_signal[0]

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


class NoDeltaSOBAnalizer(Analizer):
    def analize_func(self, df, pd: PriceData) -> (bool, Signal, str):
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, pd, include_delta=False)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class SOBAnalizer(Analizer):
    def analize_func(self, df, pd: PriceData) -> (bool, Signal, str):
        sob_ind = SuperOrderBlockIndicator(df, df.open, df.close, df.high, df.low, pd)

        signal = sob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class VOBAnalizer(Analizer):
    def analize_func(self, df, pd: PriceData) -> (bool, Signal, str):
        alt_pd = PriceData(pd.symbol, pd.exchange, OBVolumeIndicator.get_alt_interval(pd.interval))
        alt_df = alt_pd.get_chart_data_if_exists()
        vob_ind = OBVolumeIndicator(df, alt_df, df.open, df.close, df.high, df.low, pd)
        # if alt_df is not None:
        #     print("vob analize", pd.symbol, pd.interval, alt_pd.interval, len(alt_df))

        signal, debug = vob_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, debug

    def analize(self, df, pd) -> (bool, Signal, str):
        return self.analize_func(df, pd)


class VolumeAnalizer(Analizer):
    def analize_func(self, df, pd) -> (bool, Signal, str):
        volume_ind = VolumeIndicator(df, df.open, df.close, df.high, df.low)
        signal = volume_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class SPAnalizer(Analizer):
    def analize_func(self, df, pd) -> (bool, Signal, str):
        sp_ind = ScalpProIndicator(df, df.open, df.close, df.high, df.low)
        signal = sp_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class UMAAnalizer(Analizer):
    def analize_func(self, df, pd) -> (bool, Signal, str):
        uma_ind = UMAIndicator(df, df.open, df.close, df.high, df.low)
        signal = uma_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"


class NWAnalizer(Analizer):
    def analize_func(self, df, pd) -> (bool, Signal, str):
        nw_ind = NadarayaWatsonIndicator(df, df.open, df.close, df.high, df.low)
        signal = nw_ind.get_signal()
        has_signal = not(signal.type == NeutralSignal())
        return has_signal, signal, "no debug"
