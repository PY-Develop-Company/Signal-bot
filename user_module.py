import manager_module
import market_info
import asyncio

from utils.time import secs_to_date, now_time, str_to_datetime, datetime_to_str

from datetime import timedelta
from DBModul import *
from pandas import read_sql_query, to_datetime

startLanguage = "english"

current_users_pointer_max_dict = dict()
current_users_pointer_min_dict = dict()

current_users_data_dict = dict()

# STATUSES
deposit_status = "status Deposit"
trial_status = 'status Trial'
id_status = "status ID"
none_status = "status none"
wait_id_status = 'status wait check ID'
wait_id_input_status = 'status wait input ID'
wait_deposit_status = 'status wait check Deposit'


def find_user_with_id(id):
    try:
        sql_query = f"SELECT * FROM {user_table} WHERE id = {id}"

        df = read_sql_query(sql_query, db_connection)

        if len(df) == 0:
            return None

        user_dict = {
            "id": df["id"][0],
            "name": df["name"][0],
            "tag": df["tag"][0],
            "language": df["language"][0],
            "status": df["status"][0],
            "account_number": df["account_number"][0],
            "had_trial_status": df["had_trial_status"][0],
            "trial_end_date": df["trial_end_date"][0],
            "before_trial_status": df["before_trial_status"][0],
            "time": df["time"][0],
            "get_next_signal": df["get_next_signal"][0],
        }
        return user_dict
    except sqlite3.Error as error:
        print(f"Error find user: {error}")
        return None


def get_user_time(id):
    user = find_user_with_id(id)

    if user:
        return str_to_datetime(user.get('time'))
    return None


def set_user_time(user_id, new_time):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {user_table} SET time = ? WHERE id = ?", (new_time, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error set time {user_id}: {error}")


def get_users_groups_ids(groups_count, users_in_group_count, delay_second):
    statuses = [deposit_status, trial_status]
    sql_query = f"""
        SELECT * FROM {user_table} 
        WHERE (status IN {tuple(statuses)} OR id IN {tuple(manager_module.tester_ids)}) AND get_next_signal = {True} 
        ORDER BY time """
    users_df = read_sql_query(sql_query, db_connection)

    all_users_count = groups_count * users_in_group_count
    if len(users_df) > all_users_count:
        users_df = users_df[:all_users_count]

    result_users_groups = []
    group = []
    users_df['time'] = to_datetime(users_df['time'])
    for i, user in users_df.iterrows():
        if len(group) >= users_in_group_count:
            result_users_groups.append(group)
            group = []
        if len(result_users_groups) >= groups_count:
            break

        if user['time'] < now_time():
            group.append(user["id"])
            set_user_time(user['id'], datetime_to_str(now_time() + timedelta(seconds=delay_second)))

    if len(group) > 0:
        result_users_groups.append(group)

    for i in range(len(result_users_groups), groups_count):
        result_users_groups.append([])

    return result_users_groups


def remove_user_with_id(id):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f'''
            SELECT name, account_number, status FROM {user_table}
            WHERE id = ? AND status = ?
        ''', (id, deposit_status))
        user = cursor.fetchone()
        if user:
            cursor.execute(f'''UPDATE {user_table} SET status = ?
                WHERE id = ? AND status = ?
            ''', (none_status, id, deposit_status))
            db_connection.commit()
            data = f"{user[0]} | {user[1]} | {none_status}"
            return True, data
        else:
            return False, ""
    except sqlite3.Error as error:
        print(f"Error delete {id}: {error}")
        return False, ""


def get_users_strings():
    cursor = db_connection.cursor()

    users_strings_list = []
    users_data = []

    try:
        cursor.execute(f'''
            SELECT id, name, account_number, tag, status, trial_end_date
            FROM {user_table}
            WHERE status IN (?, ?)
        ''', (deposit_status, trial_status))

        rows = cursor.fetchall()
        user_number = 1

        for row in rows:
            telegram_id, telegram_name, account_number, tag, status, trial_end_date = row
            if status == deposit_status:
                users_data.append((telegram_id, telegram_name, account_number))
                users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status}")
            elif status == trial_status:
                formatted_end_date = secs_to_date(trial_end_date)
                users_data.append((telegram_id, telegram_name, account_number))
                users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status} | {formatted_end_date}")
            user_number += 1
        return users_strings_list, users_data
    except sqlite3.Error as error:
        print(f"Error  get users string: {error}")
        return [], []


def prev_user_strings(users_for_print_count, manager_id):
    global current_users_pointer_min_dict, current_users_pointer_max_dict, current_users_data_dict
    users_strings_list, users_data = get_users_strings()

    counter = 1
    strings = []

    if current_users_pointer_min_dict.get(manager_id, -1) - 1 < 0:
        current_users_pointer_min_dict.update({manager_id: len(users_strings_list)})
    range_val = range(current_users_pointer_min_dict.get(manager_id, -1) - 1, -1, -1)

    current_users_pointer_max_dict.update({manager_id: current_users_pointer_min_dict.get(manager_id, -1) - 1})
    new_current_users_data = []
    for i in range_val:
        strings.append(users_strings_list[i])
        new_current_users_data.append((i + 1, *users_data[i]))
        counter = counter + 1
        is_last_user = (i == 0)
        if counter > users_for_print_count or is_last_user:
            current_users_pointer_min_dict.update(
                {manager_id: current_users_pointer_max_dict.get(manager_id) - users_for_print_count + 1})
            break

    new_current_users_data.reverse()
    strings.reverse()
    current_users_data_dict.update({manager_id: new_current_users_data})
    return strings


def next_user_strings(users_for_print_count, manager_id):
    global current_users_pointer_max_dict, current_users_pointer_min_dict, current_users_data_dict
    users_strings_list, users_data = get_users_strings()

    counter = 1
    strings = []

    if current_users_pointer_max_dict.get(manager_id, -1) + 1 >= len(users_strings_list):
        current_users_pointer_max_dict.update({manager_id: -1})
    range_val = range(current_users_pointer_max_dict.get(manager_id, -1) + 1, len(users_strings_list))
    current_users_pointer_min_dict.update({manager_id: current_users_pointer_max_dict.get(manager_id, -1) + 1})
    new_current_users_data = []
    for i in range_val:
        strings.append(users_strings_list[i])
        new_current_users_data.append((i + 1, *users_data[i]))
        counter = counter + 1
        is_last_user = (i == len(users_strings_list) - 1)
        if counter > users_for_print_count or is_last_user:
            current_users_pointer_max_dict.update(
                {manager_id: current_users_pointer_min_dict.get(manager_id) + users_for_print_count - 1})
            break

    current_users_data_dict.update({manager_id: new_current_users_data})
    return strings


def get_current_users_data(manager_id):
    return current_users_data_dict.get(manager_id, [])


def has_user_status(id, status):
    user = find_user_with_id(id)

    return not (user is None) and user['status'] == status


def get_user_language(id):
    if id in manager_module.managers_id:
        return manager_module.get_manager_language(id)
    else:
        user = find_user_with_id(id)
        if not (user is None):
            return user['language']
    return None


def set_user_language(user_id, new_language):
    cursor = db_connection.cursor()
    try:
        if user_id in manager_module.managers_id:
            manager_module.set_manager_language(user_id, new_language)
        else:
            cursor.execute(f"UPDATE {user_table} SET language = ? WHERE id = ?", (new_language, user_id))
            db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error change language {user_id}: {error}")


def set_next_signal_status(user_id, flag):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {user_table} SET get_next_signal = ? WHERE id = ?", (flag, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error 'get_next_signal': {error}")


def get_next_signal_status(user_id):
    user = find_user_with_id(user_id)
    if user:
        return user.get('get_next_signal')
    return None


def get_users_ids_with_status(status):
    try:
        sql_query = f"SELECT * FROM {user_table} WHERE status = '{status}'"
        users_df = read_sql_query(sql_query, db_connection)
        return users_df["id"].values.tolist()
    except sqlite3.Error as error:
        print(f"Error get users with status '{status}': {error}")
        return []


def had_trial_status(user_id):
    user = find_user_with_id(user_id)
    if user:
        return user.get('had_trial_status')
    return None


def set_trial_to_user(user_id):
    cursor = db_connection.cursor()
    try:
        trial_end_date = market_info.get_trial_end_date()
        cursor.execute(f'''
            UPDATE {user_table}
            SET had_trial_status = 1, before_trial_status = status, status = ?, trial_end_date = ?
            WHERE id = ?
        ''', (trial_status, trial_end_date, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error set trial {user_id}: {error}")


def remove_trial_from_user(user_id):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f'''
            UPDATE {user_table}
            SET status = before_trial_status, before_trial_status = ?
            WHERE id = ?
        ''', (none_status, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error remove trial {user_id}: {error}")


def get_user_trial_end_date(user_id):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"SELECT trial_end_date FROM {user_table} WHERE id = ?", (user_id,))
        trial_end_date = cursor.fetchone()

        if trial_end_date:
            return trial_end_date[0]
        return None
    except sqlite3.Error as error:
        print(f"Error get trial end time {user_id}: {error}")
        return None


def add_user(id, first_name, last_name, tag):
    cursor = db_connection.cursor()

    try:
        cursor.execute(f"SELECT * FROM {user_table} WHERE id = ?", (id,))
        user_exists = cursor.fetchone()

        if not user_exists:
            pass
        else:
            full_name = f"{first_name} {last_name}"
            cursor.execute(f'''
                INSERT INTO {user_table} (
                    id, name, tag, language, status,
                    account_number, had_trial_status, trial_end_date,
                    before_trial_status, time, get_next_signal
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            ''', (
                id, full_name, tag, startLanguage, none_status,
                0, False, None, "none", datetime_to_str(now_time()), False
            ))
            db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error add {id}: {error}")


def update_status_user(id, status):
    cursor = db_connection.cursor()
    cursor.execute(f"UPDATE {user_table} SET status = ? WHERE id = ?", (status, id))
    db_connection.commit()


async def set_user_tag(user_id, tag):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {user_table} SET tag = ? WHERE id = ?", (tag, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        print(f"Error set 'tag': {error}")


async def get_user_with_status(status):
    users_ids_with_status = get_users_ids_with_status(status)

    has_users_with_status = len(users_ids_with_status) > 0
    result_user = users_ids_with_status[0] if has_users_with_status else None

    return has_users_with_status, result_user


def get_user_status(id):
    user = find_user_with_id(id)
    if user:
        return user['status']
    return None


def get_user_tag(id):
    user = find_user_with_id(id)
    if user:
        return user['tag']
    return None


def get_user_account_number(id):
    user = find_user_with_id(id)
    if user:
        return user.get('account_number')
    return None


def have_user_with_id(id):
    user = find_user_with_id(id)
    return not (user is None)


async def main():
    # find_user_with_id(5418713788)
    print(get_users_groups_ids(50, 20, 60 * 5))


if __name__ == "__main__":
    asyncio.run(main())
