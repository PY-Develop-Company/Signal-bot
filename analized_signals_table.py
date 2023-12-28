from DBModul import create_table, AddColumn, DB_OPEN_WORK
from sqlite3 import Error
from price_parser import PriceData
from pandas import read_sql_query

completed_signals_table = "analizedSignals"

connection = DB_OPEN_WORK


class AnalizedSignalsTable:
    @staticmethod
    def create_signals_info_table():
        create_table(completed_signals_table)

        AddColumn(completed_signals_table, "is_checked", "INTEGER")

        AddColumn(completed_signals_table, "symbol", "TEXT")
        AddColumn(completed_signals_table, "exchange", "TEXT")
        AddColumn(completed_signals_table, "interval", "TEXT")
        AddColumn(completed_signals_table, "candle_time", "TEXT")

        AddColumn(completed_signals_table, "has_signal", "INTEGER")
        AddColumn(completed_signals_table, "signal_type", "TEXT")
        AddColumn(completed_signals_table, "deal_time", "INTEGER")

        AddColumn(completed_signals_table, "open_price", "REAL")

        AddColumn(completed_signals_table, "msg", "TEXT")
        AddColumn(completed_signals_table, "start_analize_time", "INTEGER")

    @staticmethod
    def add_analized_signal(pd: PriceData, candle_time, has_signal, signal_type, deal_time, open_price, msg, start_analize_time):
        columns = ("is_checked", "symbol", "exchange", "interval", "candle_time", "has_signal", "signal_type", "deal_time", "open_price", "msg", "start_analize_time")
        data = (False, pd.symbol, pd.exchange, str(pd.interval), str(candle_time), has_signal, signal_type, deal_time, open_price, msg, start_analize_time)
        cursor = connection.cursor()
        try:
            sql_query = f"""
                INSERT INTO {completed_signals_table} {columns}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(sql_query, data)
            connection.commit()
        except Error as error:
            print(f"{error}")

    @staticmethod
    def get_unchecked_signals():
        result = None
        try:
            sql_query = f"""SELECT * FROM {completed_signals_table}
                WHERE is_checked = {False}"""

            df = read_sql_query(sql_query, connection)
            result = df
        except Error as error:
            print(f"{error}")

        cursor = connection.cursor()
        try:
            sql_query = f"""UPDATE {completed_signals_table} SET is_checked = {True}
                        WHERE id IN{tuple(result["id"].values)}"""
            cursor.execute(sql_query)
            connection.commit()
        except Error as error:
            print(f"{error}")
        return result

    @staticmethod
    def set_all_checked():
        cursor = connection.cursor()
        try:
            sql_query = f"""UPDATE {completed_signals_table} SET is_checked = {None}
                WHERE is_checked = {False}"""
            cursor.execute(sql_query)
            connection.commit()
        except Error as error:
            print(f"{error}")


AnalizedSignalsTable.create_signals_info_table()
