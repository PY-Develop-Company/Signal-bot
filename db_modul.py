import sqlite3

DB_path = "users/DataBase.db"
user_table = "users"
manager_table = "managers"


def open_db():
    return open_custom_db(DB_path)


def open_custom_db(path):
    try:
        connection = sqlite3.connect(path, check_same_thread=False)
        return connection
    except sqlite3.Error as error:
        print("Error open DB:", error)
        return None


def create_managers_table():
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"""
                        CREATE TABLE IF NOT EXISTS {manager_table} (
                            id INTEGER PRIMARY KEY, do TEXT, status TEXT, language TEXT
                        )
                    """)
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error create_managers_table: ", error)


db_connection = open_db()
create_managers_table()


def get_connection():
    return db_connection
