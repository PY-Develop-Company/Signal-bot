photo_long_path = "img/long.jpg"
photo_short_path = "img/short.jpg"

long_signal_smile = "🟢"
short_signal_smile = "🔴"

long_signal_text = "LONG ⬆"
short_signal_text = "SHORT ⬇"
neutral_signal_text = "Нет сигнала"

profit_smile = "✅"
loss_smile = "❌"

puncts_pohibka = 0.030

puncts_pohibka_dict = {
    "EURUSD": 0.00030,
    "AUDUSD": 0.00030,
    "AUDCAD": 0.00030,
    "EURJPY": 0.030,
    "EURCAD": 0.00030,
    "AUDCHF": 0.00030,
    "GBPUSD": 0.00030,
    "AUDJPY": 0.030,
    "GBPAUD": 0.00030
}


class Signal:
    type = None

    def __init__(self):
        self.signal = None
        self.photo_path = None
        self.smile = None
        self.text = None

    def get_open_msg_text(self, pd, minutes):
        return self.smile + pd.symbol[:3] + "/" + pd.symbol[3:] + " " + self.text + " " + str(minutes) + "мин"

    def get_photo_path(self):
        return self.photo_path

    def is_profit(self, open_price, close_price, currency):
        return False

    def get_close_position_signal_message(self, pd, open, close, bars_count):
        is_profit_position = self.is_profit(open, close, pd.symbol)
        prifit_smile_text = profit_smile if is_profit_position else loss_smile
        # debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

        message = f"{self.smile} Сделка в {prifit_smile_text} {pd.symbol[:3]}/{pd.symbol[3:]} {self.text} {bars_count}мин"
        return message, is_profit_position


class NeutralSignal(Signal):
    type = "neutral"

    def __init__(self):
        self.signal = type(self)
        self.photo_path = "None"
        self.smile = "None"
        self.text = neutral_signal_text


class LongSignal(Signal):
    type = "long"

    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_long_path
        self.smile = long_signal_smile
        self.text = long_signal_text

    def is_profit(self, open_price, close_price, currency):
        return True if close_price + puncts_pohibka_dict.get(currency) >= open_price else False


class ShortSignal(Signal):
    type = "short"

    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_short_path
        self.smile = short_signal_smile
        self.text = short_signal_text

    def is_profit(self, open_price, close_price, currency):
        return True if close_price - puncts_pohibka_dict.get(currency) <= open_price else False


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
