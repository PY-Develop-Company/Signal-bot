import sqlite3

DB_path = "./users/DataBase.db"
user_table = "users"
manager_table = "managers"


def open_db():
    try:
        connection = sqlite3.connect(DB_path, check_same_thread=False)
        return connection
    except sqlite3.Error as error:
        print("Error open DB:", error)
        return None


def close_db(connection):
    connection.close()


def create_users_table():
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {user_table} (
                            id INTEGER PRIMARY KEY, name TEXT, tag TEXT, language TEXT, status TEXT, 
                            account_number INTEGER, had_trial_status INTEGER, trial_end_date REAL, 
                            before_trial_status TEXT, time TEXT, get_next_signal INTEGER
                        )
                    """)
    except sqlite3.Error as error:
        print(f"Error create_managers_table: ", error)


def create_managers_table():
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {manager_table} (
                            id INTEGER PRIMARY KEY, do TEXT, status TEXT, language TEXT
                        )
                    """)
    except sqlite3.Error as error:
        print(f"Error create_managers_table: ", error)

#  тимчасово
# def InsertUserDataFromJSON(tmp_table, json_data):
#     connection = OpenDB()
#     cursor = connection.cursor()
#     try:
#         columns = ', '.join(json_data.keys())
#         placeholders = ', '.join('?' * len(json_data))
#         values = tuple(json_data.values())
#
#         query = f"INSERT INTO {tmp_table} ({columns}) VALUES ({placeholders})"
#         cursor.execute(query, values)
#
#         connection.commit()
#         print("Дані з JSON успішно вставлені в таблицю users.")
#     except sqlite3.Error as error:
#         print("Помилка під час вставки даних з JSON:", error)
#     finally:
#         connection.close()


db_connection = open_db()
if __name__ == "__main__":
    from tv_signals.analized_signals_table import update_currencies, AnalyzedSignalsTable
    from tv_signals.signals_table import update_signals
    from tv_signals.price_parser import PriceData
    from tvDatafeed import Interval
    from utils.time import now_time

    # update_currencies()
    # print(update_analized_signals())
    # create_managers_table()
    # create_users_table()
    # for json_data in temp:
    #     InsertUserDataFromJSON(user_Table, json_data)
