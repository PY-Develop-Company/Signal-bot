import sqlite3

DB_path = "users/DataBase.db"
user_table = "users"
manager_table = "managers"


def create_table(tmp_Table):
    connection = OpenDB()
    cursor = connection.cursor()
    cursor.execute(f"""
        CREATE TABLE IF NOT EXISTS {tmp_Table} (
            id INTEGER PRIMARY KEY
        )
    """)
    connection.commit()
    connection.close()


def OpenDB():
    try:
        connection = sqlite3.connect(DB_path)
        return connection
    except sqlite3.Error as error:
        print("Error open DB", error)
        return None


def AddColumn(table_name, column_name, column_type):
    connection = OpenDB()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"ALTER TABLE {table_name} ADD COLUMN {column_name} {column_type}")
            connection.commit()
            print(f"Conlumn {column_name} add.")
        except sqlite3.Error as error:
            print("Error add column", error)
        CloseDB(connection)


def OpenTable(connection,table_name):
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT * FROM {table_name}")
        rows = cursor.fetchall()
        return rows
    except sqlite3.Error as error:
        print(f"Помилка під час відкриття таблиці {table_name}: {error}")
        return None


def RemoveColumn(table_name, column_name):
    connection = OpenDB()
    if connection:
        cursor = connection.cursor()
        try:
            cursor.execute(f"ALTER TABLE {table_name} DROP COLUMN {column_name}")
            connection.commit()
            print(f"column {column_name} deleted.")
        except sqlite3.Error as error:
            print("Error delete column", error)
        CloseDB(connection)


def CloseDB(connection):
    connection.close()


def CreateUsersTable():
    create_table(user_table)
    AddColumn(user_table, "name", "TEXT")
    AddColumn(user_table, "tag", "TEXT")
    AddColumn(user_table, "language", "TEXT")
    AddColumn(user_table, "status", "TEXT")
    AddColumn(user_table, "account_number", "INTEGER")
    AddColumn(user_table, "had_trial_status", "INTEGER")
    AddColumn(user_table, "trial_end_date", "REAL")
    AddColumn(user_table, "before_trial_status", "TEXT")
    AddColumn(user_table, "time", "TEXT")
    AddColumn(user_table, "get_next_signal", "INTEGER")


def CreateManagersTable():
    create_table(manager_table)
    AddColumn(manager_table, "do", "TEXT")
    AddColumn(manager_table, "status", "TEXT")
    AddColumn(manager_table, "language", "TEXT")

#  тимчасово
def InsertUserDataFromJSON(tmp_table, json_data):
    connection = OpenDB()
    cursor = connection.cursor()
    try:
        columns = ', '.join(json_data.keys())
        placeholders = ', '.join('?' * len(json_data))
        values = tuple(json_data.values())

        query = f"INSERT INTO {tmp_table} ({columns}) VALUES ({placeholders})"
        cursor.execute(query, values)

        connection.commit()
        print("Дані з JSON успішно вставлені в таблицю users.")
    except sqlite3.Error as error:
        print("Помилка під час вставки даних з JSON:", error)
    finally:
        connection.close()


db_connection = OpenDB()
# import file_manager
CreateManagersTable()
CreateUsersTable()
# temp = file_manager.read_file("users/db.txt")
# for json_data in temp:
#     InsertUserDataFromJSON(user_Table, json_data)
