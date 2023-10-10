from interval_convertor import timedelta_to_close_string, interval_to_datetime

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

    def get_open_msg_text(self, pd, bars_count):
        return self.smile + pd.symbol[:3] + "/" + pd.symbol[3:] + " " + self.text + " " + timedelta_to_close_string(interval_to_datetime(pd.interval), bars_count)

    def get_photo_path(self):
        return self.photo_path

    def is_profit(self, open_price, close_price):
        return False

    def get_close_position_signal_message(self, pd, open, close, bars_count):
        is_profit_position = self.is_profit(open, close)
        prifit_smile_text = profit_smile if is_profit_position else loss_smile
        # debug_text = f"\nЦіна закриття позиції {str(close)} Ціна відкриття позиції: {str(open)}"

        message = f"{self.smile} Сделка в {prifit_smile_text} {pd.symbol[:3]}/{pd.symbol[3:]} {self.text} {timedelta_to_close_string(interval_to_datetime(pd.interval), bars_count)}"
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

    def is_profit(self, open_price, close_price):
        return True if close_price >= open_price else False


class ShortSignal(Signal):
    type = "short"

    def __init__(self):
        self.signal = type(self)
        self.photo_path = photo_short_path
        self.smile = short_signal_smile
        self.text = short_signal_text

    def is_profit(self, open_price, close_price):
        return True if (close_price <= open_price) else False


def get_signal_by_type(signal_type):
    if signal_type == NeutralSignal.type:
        return NeutralSignal()
    elif signal_type == LongSignal.type:
        return LongSignal()
    elif signal_type == ShortSignal.type:
        return ShortSignal()

    return None
