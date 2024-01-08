from db_modul import db_connection

from utils.time import datetime_to_secs

from sqlite3 import Error

from my_debuger import debug_error, debug_info

table_name = "completedSignals"


class SignalsTable:
    @staticmethod
    def create_table():
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"""
                            CREATE TABLE IF NOT EXISTS {table_name} (
                                id                 INTEGER PRIMARY KEY,
                                analized_signal_id INTEGER REFERENCES analizedSignals (id) ON DELETE CASCADE NOT NULL,
                                open_time_secs     INTEGER,
                                open_time          TEXT,
                                close_time_secs    INTEGER,
                                close_time         TEXT,
                                open_price         REAL,
                                close_price        REAL,
                                is_profit          INTEGER
                            )
                        """)
        except Error as error:
            debug_error(f"{error}", f"Error create_table SignalsTable")

    @staticmethod
    def add_sended_signal(analized_signal_id, open_time, close_time,open_price, close_price, is_profit):
        columns = ("analized_signal_id", "open_time_secs", "open_time", "close_time_secs", "close_time", "open_price", "close_price", "is_profit")
        data = (open_time, datetime_to_secs(open_time), close_time, datetime_to_secs(close_time), open_price, close_price, is_profit)
        cursor = db_connection.cursor()
        try:
            sql_query = f"""
                INSERT INTO {table_name} {columns}
                VALUES ({analized_signal_id}, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(sql_query, data)
            db_connection.commit()
        except Error as error:
            debug_error(f"{error}", f"Error SignalsTable add_sended_signal")

    @staticmethod
    def get_all_data():
        cursor = db_connection.cursor()
        try:
            sql_query = f"""SELECT * FROM {table_name}"""
            res = cursor.execute(sql_query)
            return res.fetchall()
        except Error as error:
            debug_error(f"{error}", f"Error SignalsTable get_all_data")
            return None

    @staticmethod
    def get_profit_data_in_period(start_period_secs, stop_period_secs):
        cursor = db_connection.cursor()
        try:
            sql_query = f"""
                SELECT is_profit FROM {table_name} 
                WHERE close_time < {start_period_secs} AND close_time > {stop_period_secs}"""
            res = cursor.execute(sql_query)
            return res.fetchall()
        except Error as error:
            debug_error(f"{error}", f"Error SignalsTable get_profit_data_in_period")
            return None


def update_signals():
    from tv_signals.analized_signals_table import table_name as analized_table_name, currencies_table_name
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"""
                        UPDATE {table_name}
                        SET analized_signal_id = (SELECT {analized_table_name}.id 
                            FROM {analized_table_name} 
                            LEFT JOIN {currencies_table_name} ON {analized_table_name}.currency = {currencies_table_name}.id
                            WHERE {analized_table_name}.currency = {currencies_table_name}.id AND {currencies_table_name}.symbol ={table_name}.currency
                            AND {analized_table_name}.interval = {table_name}.interval
                            AND {analized_table_name}.signal_type = {table_name}.signal_type
                            AND {analized_table_name}.open_price = {table_name}.open_price
                            AND {analized_table_name}.deal_time = {table_name}.deal_time)
                   """)
        db_connection.commit()
    except Error as error:
        debug_error(f"{error}", f"Error update SignalsTable")


SignalsTable.create_table()
# SignalsTable.add_sended_signal(PriceData("AUD", "OANDA", Interval.in_1_minute), 4, datetime_to_secs(now_time()), datetime_to_secs(now_time()), "long", 1, 2, True)
# print(SignalsTable.get_all_data())
# start_time = datetime_to_secs(now_time())
# stop_time = datetime_to_secs(now_time() - timedelta(days=1))
# print(start_time)
# print(stop_time)
# print(SignalsTable.get_profit_data_in_period(start_time, start_time))
