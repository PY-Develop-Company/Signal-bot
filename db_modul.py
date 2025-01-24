import sqlite3
from sqlite3 import connect
from threading import Lock

DB_path = "users/DataBase.db"
user_table = "users"
manager_table = "managers"


def open_db():
    return ConnectionPool().get_conn(DB_path)


# def open_custom_db(path):
#     try:
#         connection = sqlite3.connect(path, check_same_thread=False)
#         return connection
#     except sqlite3.Error as error:
#         print("Error open DB:", error)
#         return None
    



class ConnectionPool:
    _instance = None
    _lock = Lock()
    
    def __new__(cls):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super().__new__(cls)
                cls._instance.pool = []
            return cls._instance
            
    def get_conn(self, path):
        with self._lock:
            if not self.pool:
                conn = connect(path, check_same_thread=False) 
                self.pool.append(conn)
            return self.pool.pop()
            
    def return_conn(self, conn):
        with self._lock:
            self.pool.append(conn)


# def create_managers_table():
#     cursor = db_connection.cursor()
#     try:
#         cursor.execute(f"""
#                         CREATE TABLE IF NOT EXISTS {manager_table} (
#                             id INTEGER PRIMARY KEY, do TEXT, status TEXT, language TEXT
#                         )
#                     """)
#         db_connection.commit()
#     except sqlite3.Error as error:
#         print(f"Error create_managers_table: ", error)

def create_managers_table():
    conn = get_connection()
    try:
        cursor = conn.cursor()
        cursor.execute("""CREATE TABLE IF NOT EXISTS ...""")
        conn.commit()
    finally:
        close_connection(conn)


db_connection = open_db()
create_managers_table()


pool = ConnectionPool()

def get_connection():
    return pool.get_conn(DB_path)

def close_connection(conn):
    pool.return_conn(conn)