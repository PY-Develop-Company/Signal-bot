from DBModul import db_connection
from sqlite3 import Error
from price_parser import PriceData
from pandas import read_sql_query

table_name = "analizedSignals"


class AnalyzedSignalsTable:
    @staticmethod
    def create_table():
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                        id INTEGER PRIMARY KEY, is_checked INTEGER, symbol TEXT, exchange TEXT, interval TEXT, 
                        candle_time TEXT, has_signal INTEGER, signal_type TEXT, deal_time INTEGER, open_price REAL,
                        msg TEXT, start_analize_time INTEGER
                    )
                """)
        except Error as error:
            print(f"Error create_table AnalyzedSignalsTable: ", error)

    @staticmethod
    def add_analyzed_signal(pd: PriceData, candle_time, has_signal, signal_type, deal_time, open_price, msg, start_analize_time):
        columns = ("is_checked", "symbol", "exchange", "interval", "candle_time", "has_signal", "signal_type", "deal_time", "open_price", "msg", "start_analize_time")
        data = (False, pd.symbol, pd.exchange, str(pd.interval), str(candle_time), has_signal, signal_type, deal_time, open_price, msg, start_analize_time)
        cursor = db_connection.cursor()
        try:
            sql_query = f"""
                INSERT INTO {table_name} {columns}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(sql_query, data)
            db_connection.commit()
        except Error as error:
            print(f"add_analized_signal {error}")

    @staticmethod
    def get_unchecked_signals():
        result = None
        try:
            sql_query = f"""SELECT * FROM {table_name}
                WHERE is_checked = {False}"""

            # print("sql_query1", sql_query)
            df = read_sql_query(sql_query, db_connection)
            result = df
        except Error as error:
            print(f"Error get_unchecked_signals (select): {error}")

        cursor = db_connection.cursor()
        try:
            sql_query = f"""UPDATE {table_name} SET is_checked = {True}
                            WHERE is_checked = 0"""
            cursor.execute(sql_query)
            db_connection.commit()
        except Error as error:
            print(f"Error get_unchecked_signals(mark checked): {error}")
        return result

    @staticmethod
    def set_all_checked():
        cursor = db_connection.cursor()
        try:
            sql_query = f"""UPDATE {table_name} SET is_checked = NULL
                WHERE is_checked = 0"""
            cursor.execute(sql_query)
            db_connection.commit()
        except Error as error:
            print(f"set_all_checked {error}")


AnalyzedSignalsTable.create_table()

if __name__ == "__main__":
    from tvDatafeed import Interval
    AnalyzedSignalsTable.add_analyzed_signal(PriceData("BTCUSDT", "binance", Interval.in_1_minute), 1, 1, 1, 1, 1, 1, 1)
    AnalyzedSignalsTable.add_analyzed_signal(PriceData("BTCUSDT", "binance", Interval.in_1_minute), 1, 1, 1, 1, 1, 1, 1)

    # AnalizedSignalsTable.get_unchecked_signals()
    AnalyzedSignalsTable.set_all_checked()
