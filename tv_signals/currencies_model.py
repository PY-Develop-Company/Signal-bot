import sqlite3

from db_modul import get_connection

from pandas import read_sql_query

from my_debuger import debug_error


class CurrenciesModel:
    __tablename__ = "currencies"

    @staticmethod
    def get_all_in_use():
        currencies = []

        try:
            sql_query = f"""SELECT * FROM {CurrenciesModel.__tablename__};"""
            df = read_sql_query(sql_query, get_connection())

            for currency in df.index:
                if df["is_in_use"][currency] == 1:
                    symbol = df['symbol'][currency]
                    exchange = df['exchange'][currency]
                    currencies.append((symbol, exchange))
        except sqlite3.Error as e:
            debug_error(e, "Error get_currencies")

        return currencies

    @staticmethod
    def create_table():
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {CurrenciesModel.__tablename__} "
                f"(id INTEGER AUTO_INCREMENT PRIMARY KEY, symbol TEXT, exchange TEXT, puncts REAL, is_in_use)")
            connection.commit()
        except sqlite3.Error as error:
            print(f"Error can't create table {CurrenciesModel.__tablename__}: ", error)

CurrenciesModel.create_table()
