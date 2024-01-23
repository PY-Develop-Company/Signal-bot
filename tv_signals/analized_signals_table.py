from db_modul import db_connection
from tv_signals.price_parser import PriceData
from tv_signals.price_parser import currencies_table_name

from pandas import read_sql_query
from sqlite3 import Error

from my_debuger import debug_error, debug_info


table_name = "analizedSignals"


class AnalyzedSignalsTable:
    @staticmethod
    def create_table():
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"""
                    CREATE TABLE IF NOT EXISTS {table_name} (
                    id                 INTEGER PRIMARY KEY,
                    is_checked         INTEGER DEFAULT (0),
                    currency           INTEGER REFERENCES currencies (id) NOT NULL,
                    interval           TEXT,
                    candle_time        TEXT,
                    has_signal         INTEGER,
                    signal_type        TEXT,
                    deal_time          INTEGER,
                    open_price         REAL,
                    msg                TEXT,
                    start_analize_time INTEGER
                );
                """)
        except Error as error:
            debug_error(error, f"Error create_table AnalyzedSignalsTable")

    @staticmethod
    def add_analyzed_signal(pd: PriceData, candle_time, has_signal, signal_type, deal_time, open_price, msg, start_analize_time):
        cursor = db_connection.cursor()
        sql_query = f"""
                        INSERT INTO analizedSignals (currency, interval, candle_time, has_signal, signal_type, deal_time, open_price, msg, start_analize_time)
                        VALUES ((SELECT id FROM currencies WHERE symbol = "{pd.symbol}" AND exchange = "{pd.exchange}"), "{str(pd.interval)}", 
                        "{str(candle_time)}", {has_signal}, "{signal_type}", {deal_time}, {open_price}, "{msg}", "{start_analize_time}");"""
        try:
            cursor.execute(sql_query)
            db_connection.commit()
        except Error as error:
            debug_error(error, f"Error add_analized_signal")

    @staticmethod
    def get_unchecked_signals():
        result = None
        try:
            sql_query = f"""SELECT {table_name}.id, has_signal, signal_type, symbol, exchange, interval, open_price, deal_time, 
                start_analize_time, msg
                FROM {table_name}
                LEFT JOIN {currencies_table_name} ON {table_name}.currency = {currencies_table_name}.id
                WHERE is_checked = {False} """

            df = read_sql_query(sql_query, db_connection)
            result = df
        except Error as error:
            debug_error(error, f"Error get_unchecked_signals (select)")

        cursor = db_connection.cursor()
        try:
            sql_query = f"""UPDATE {table_name} SET is_checked = {True}
                            WHERE is_checked = 0"""
            cursor.execute(sql_query)
            db_connection.commit()
        except Error as error:
            debug_error(error, f"Error get_unchecked_signals(mark checked)")
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
            debug_error(error, f"Error set_all_checked")


AnalyzedSignalsTable.create_table()


def update_currencies():
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"""
                        UPDATE {table_name}
                        SET currency = (SELECT {currencies_table_name}.id 
                            FROM {currencies_table_name}
                            WHERE {currencies_table_name}.symbol = {table_name}.symbol)
                   """)
        db_connection.commit()
    except Error as error:
        debug_error(error, f"Error update AnalyzedSignalsTable")
