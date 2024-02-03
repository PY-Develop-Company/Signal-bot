from tv_signals.price_parser import PriceData

photo_long_path = "./img/long.jpg"
photo_short_path = "./img/short.jpg"

long_signal_smile = "🟢"
short_signal_smile = "🔴"

long_signal_text = "LONG ⬆"
short_signal_text = "SHORT ⬇"
neutral_signal_text = "Нет сигнала"

profit_smile = "✅"
loss_smile = "❌"

puncts_pohibka = 5


class Signal:
    type = None

    def __init__(self, signal, photo_path, smile, text):
        self.signal = signal
        self.photo_path = photo_path
        self.smile = smile
        self.text = text

    def get_open_msg_text(self, pd, minutes):
        return self.smile + pd.symbol + " " + self.text + " " + str(minutes) + "{}"

    def get_photo_path(self):
        return self.photo_path

    def is_profit(self, open_price, close_price, pd: PriceData):
        return False

    def get_close_position_signal_message(self, pd, open, close, bars_count):
        is_profit_position = self.is_profit(open, close, pd)
        prifit_smile_text = profit_smile if is_profit_position else loss_smile
        # debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

        message = f"{self.smile} " + "{}" + f" {prifit_smile_text} {pd.symbol[:3]}/{pd.symbol[3:]} {self.text} {bars_count}" + "{}"
        return message, is_profit_position


class NeutralSignal(Signal):
    type = "neutral"

    def __init__(self):
        super().__init__(type(self), "None", "None", neutral_signal_text)


class LongSignal(Signal):
    type = "long"

    def __init__(self):
        super().__init__(type(self), photo_long_path, long_signal_smile, long_signal_text)

    def is_profit(self, open_price, close_price, pd: PriceData):
        return True if close_price + pd.get_real_puncts(puncts_pohibka) >= open_price else False


class ShortSignal(Signal):
    type = "short"

    def __init__(self):
        super().__init__(type(self), photo_short_path, short_signal_smile, short_signal_text)

    def is_profit(self, open_price, close_price, pd: PriceData):
        return True if close_price - pd.get_real_puncts(puncts_pohibka) <= open_price else False


def get_signal_by_type(signal_type):
    if signal_type == NeutralSignal.type:
        return NeutralSignal()
    elif signal_type == LongSignal.type:
        return LongSignal()
    elif signal_type == ShortSignal.type:
        return ShortSignal()

    return None


def get_oposite_by_type(signal_type):
    if signal_type == NeutralSignal.type:
        return NeutralSignal()
    elif signal_type == LongSignal.type:
        return ShortSignal()
    elif signal_type == ShortSignal.type:
        return LongSignal()
