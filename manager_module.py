import os
import user_module
from user_module import *

manager_username = "@bwg_Golden"
tester_ids = [741867026, 693562775, 5359645780]
managers_id = [5964166439, 741867026, 693562775,5359645780]
manager_url = f"https://t.me/{manager_username[1:]}"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"
none_manager_status = "none"


async def add_manager(message):
    connection = OpenedDB
    cursor = connection.cursor()
    cursor.execute(f"SELECT id FROM {user_Table} WHERE id = ?", (message.from_user.id,))
    existing_user = cursor.fetchone()
    if existing_user:
        pass
    else:
        cursor.execute(f'''INSERT INTO {user_Table} (id, status, do, language) VALUES (?, ?, ?, ?)''', (message.from_user.id, none_manager_status, "none", startLanguage))
        connection.commit()


def get_manager_language(id):
    connection = sqlite3.connect('your_database.db')  # Replace 'your_database.db' with your actual database file
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT language FROM manager_table WHERE id = ?", (id,))
        language = cursor.fetchone()[0]
        return language
    except sqlite3.Error as error:
        print(f"Error fetching manager's language: {error}")
        return None


def set_manager_language(id, language):
    connection = OpenedDB
    cursor = connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_username} SET language = ? WHERE id = ?", (language, id))
        connection.commit()
    except sqlite3.Error as error:
        print(f"Error set language manager {id}: {error}")


def update_manager_do(manager_id, do):
    connection = OpenedDB
    cursor = connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_Table} SET do = ? WHERE id = ?", (do, manager_id))
        connection.commit()
    except sqlite3.Error as error:
        print(f"Error updating manager's 'do': {error}")


async def update_manager_status(manager_id, status):
    connection = OpenedDB
    cursor = connection.cursor()
    try:
        cursor.execute(f"UPDATE {manager_Table} SET status = ? WHERE id = ?", (status, manager_id))
        connection.commit()
    except sqlite3.Error as error:
        print(f"Error updating manager's 'status': {error}")


def get_manager_do(manager_id):
    try:
        connection = OpenedDB
        cursor = connection.cursor()
        cursor.execute("SELECT do FROM manager_table WHERE id = ?", (manager_id,))
        do_value = cursor.fetchone()
        if do_value:
            return do_value[0]
        else:
            return None
    except sqlite3.Error as error:
        print(f"Error get manager 'do': {error}")
        return None


def get_manager_user_acount(manager_id):
    return user_module.get_user_account_number(int(get_manager_do(manager_id)))


def is_manager_status(manager_id, status):
    connection = OpenedDB
    cursor = connection.cursor()
    try:
        cursor.execute(f"SELECT status FROM {manager_Table} WHERE id = ?", (manager_id,))
        fetched_status = cursor.fetchone()
        if fetched_status and fetched_status[0] == status:
            return True
        return False
    except sqlite3.Error as error:
        print(f"Error fetching manager's status: {error}")
        return False
