from interval_convertor import timedelta_to_close_string


photo_long_path = "img/long.jpg"
photo_short_path = "img/short.jpg"

long_signal_smile = "🟢"
short_signal_smile = "🔴"

long_signal_text = "LONG ⬆"
short_signal_text = "SHORT ⬇"
neutral_signal_text = "Нет сигнала"

profit_smile = "✅"
loss_smile = "❌"


class Signal:
    type = None

    def __init__(self):
        self.signal = None
        self.photo_path = None
        self.smile = None
        self.text = None

    def get_open_msg_text(self, symbol, interval):
        return self.smile + symbol + " " + self.text + " " + timedelta_to_close_string(interval)

    def get_photo_path(self):
        return self.photo_path


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


class ShortSignal(Signal):
    type = "short"

    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_short_path
        self.smile = short_signal_smile
        self.text = short_signal_text


def get_signal_by_type(signal_type):
    if signal_type == NeutralSignal.type:
        return NeutralSignal()
    elif signal_type == LongSignal.type:
        return LongSignal()
    elif signal_type == ShortSignal.type:
        return ShortSignal()

    return None
