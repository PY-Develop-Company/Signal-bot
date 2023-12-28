from DBModul import create_table, AddColumn, db_connection
from sqlite3 import Error
from price_parser import PriceData
from tvDatafeed import Interval
from datetime import timedelta
from my_time import now_time, datetime_to_secs, secs_to_date

completed_signals_table = "completedSignals"


class SignalsTable:
    @staticmethod
    def create_signals_info_table():
        create_table(completed_signals_table)
        AddColumn(completed_signals_table, "currency", "TEXT")
        AddColumn(completed_signals_table, "interval", "TEXT")
        AddColumn(completed_signals_table, "deal_time", "INTEGER")
        AddColumn(completed_signals_table, "open_time_secs", "INTEGER")
        AddColumn(completed_signals_table, "open_time", "TEXT")
        AddColumn(completed_signals_table, "close_time_secs", "INTEGER")
        AddColumn(completed_signals_table, "close_time", "TEXT")
        AddColumn(completed_signals_table, "signal_type", "TEXT")
        AddColumn(completed_signals_table, "open_price", "REAL")
        AddColumn(completed_signals_table, "close_price", "REAL")
        AddColumn(completed_signals_table, "is_profit", "INTEGER")

    @staticmethod
    def add_sended_signal(pd: PriceData, deal_time, open_time, close_time, signal_type, open_price, close_price, is_profit):
        columns = ("currency", "interval", "deal_time", "open_time_secs", "open_time", "close_time_secs", "close_time", "signal_type", "open_price", "close_price", "is_profit")
        data = (pd.symbol, str(pd.interval), deal_time, open_time, datetime_to_secs(open_time), close_time, datetime_to_secs(close_time), signal_type, open_price, close_price, is_profit)
        cursor = db_connection.cursor()
        try:
            sql_query = f"""
                INSERT INTO {completed_signals_table} {columns}
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?);"""
            cursor.execute(sql_query, data)
            db_connection.commit()
        except Error as error:
            print(f"Error SignalsTable add_sended_signal: {error}")

    @staticmethod
    def get_all_data():
        cursor = db_connection.cursor()
        try:
            sql_query = f"""SELECT * FROM {completed_signals_table}"""
            res = cursor.execute(sql_query)
            return res.fetchall()
        except Error as error:
            print(f"Error SignalsTable add_sended_signal: {error}")
            return None

    @staticmethod
    def get_profit_data_in_period(start_period_secs, stop_period_secs):
        cursor = db_connection.cursor()
        try:
            sql_query = f"""
                SELECT is_profit FROM {completed_signals_table} 
                WHERE close_time < {start_period_secs} AND close_time > {stop_period_secs}"""
            res = cursor.execute(sql_query)
            return res.fetchall()
        except Error as error:
            print(f"Error SignalsTable add_sended_signal: {error}")
            return None


SignalsTable.create_signals_info_table()
# SignalsTable.add_sended_signal(PriceData("AUD", "OANDA", Interval.in_1_minute), 4, datetime_to_secs(now_time()), datetime_to_secs(now_time()), "long", 1, 2, True)
# print(SignalsTable.get_all_data())
# start_time = datetime_to_secs(now_time())
# stop_time = datetime_to_secs(now_time() - timedelta(days=1))
# print(start_time)
# print(stop_time)
# print(SignalsTable.get_profit_data_in_period(start_time, start_time))
