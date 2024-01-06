import json

from user_module import *
from db_modul import *

import configparser

config = configparser.ConfigParser()
config.read("config.ini")


manager_username = config["ADMIN"]["ManagerUsername"]
tester_ids = json.loads(config.get("ADMIN", "TesterIds"))
managers_ids = json.loads(config.get("ADMIN", "ManagersIds"))
manager_url = f"https://t.me/{manager_username[1:]}"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"
none_manager_status = "none"


async def add_manager(id):
    cursor = db_connection.cursor()
    cursor.execute(f"SELECT id FROM {manager_table} WHERE id = ?", (id,))
    existing_user = cursor.fetchone()
    if existing_user is None:
        cursor.execute(f'''INSERT INTO {manager_table} (id, status, do, language) VALUES (?, ?, ?, ?)''', (id, none_manager_status, "none", startLanguage))
        db_connection.commit()


def get_manager_language(id):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"SELECT language FROM {manager_table} WHERE id = ?", (id,))
        language = cursor.fetchone()[0]
        return language
    except sqlite3.Error as error:
        print(f"Error fetching manager's language: {error}")
        return None


def set_manager_language(id, language):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_table} SET language = ? WHERE id = ?", (language, id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error set language manager {id}: {error}")


def update_manager_do(manager_id, do):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_table} SET do = ? WHERE id = ?", (do, manager_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error updating manager's 'do': {error}, {(do, manager_id)}")


async def update_manager_status(manager_id, status):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_table} SET status = ? WHERE id = ?", (status, manager_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error updating manager's 'status': {error}")


def get_manager_do(manager_id):
    try:
        cursor = db_connection.cursor()
        cursor.execute(f"SELECT do FROM {manager_table} WHERE id = {manager_id}")
        do = cursor.fetchone()[0]
        return do
    except sqlite3.Error as error:
        print(f"Error get manager 'do': {error}, {manager_id}")
        return None


def get_manager_user_account(manager_id):
    return get_user_account_number(get_manager_do(manager_id))


def is_manager_status(manager_id, needed_status):
    connection = db_connection
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT status FROM {manager_table} WHERE id = ?", (manager_id,))
        status = cursor.fetchone()
        return status[0] == needed_status
    except sqlite3.Error as error:
        print(f"Error fetching manager's status: {error}")
        return False
