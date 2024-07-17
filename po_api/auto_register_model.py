import sqlite3

from db_modul import get_connection


class Account:
    __tablename__ = 'accounts'

    def __init__(self, id, type, is_registered=False, is_deposited=False):
        self.id = id
        self.type = type
        self.is_registered = is_registered
        self.is_deposited = is_deposited

    @staticmethod
    def get_by_id(id):
        cursor = get_connection().cursor()
        cursor.execute(f"SELECT * FROM {Account.__tablename__} WHERE id = ?", (id,))
        data = cursor.fetchone()
        return Account(data[0], data[1], data[2], data[3])

    @staticmethod
    def create_table():
        connection = get_connection()
        cursor = connection.cursor()
        try:
            cursor.execute(
                f"CREATE TABLE IF NOT EXISTS {Account.__tablename__} "
                f"(id TEXT PRIMARY KEY, type TEXT, is_registered INTEGER, is_deposited INTEGER)")
            connection.commit()
        except sqlite3.Error as error:
            print(f"Error can't create table {Account.__tablename__}: ", error)

    def create_if_not_exists(self):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(f"SELECT * FROM {Account.__tablename__} WHERE id = ?", (self.id,))
        existing_account = cursor.fetchall()
        if len(existing_account) == 0:
            cursor.execute(f"INSERT INTO {Account.__tablename__} (id, type, is_registered, is_deposited) "
                           f"VALUES (?, ?, ?, ?)",
                           (self.id, self.type, self.is_registered, self.is_deposited))

        connection.commit()

    @staticmethod
    def set_registration(id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(f"UPDATE {Account.__tablename__} SET is_registered = 1 WHERE id = ?", (id,))
        connection.commit()

    @staticmethod
    def set_deposit(id):
        connection = get_connection()
        cursor = connection.cursor()
        cursor.execute(f"UPDATE {Account.__tablename__} SET is_registered = 1, is_deposited = 1 WHERE id = ?", (id,))
        connection.commit()


Account.create_table()
