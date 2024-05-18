from datetime import timedelta
from abc import ABC, abstractmethod

import config

from utils.time import datetime_to_str, now_time, secs_to_date
import market_info
from db_modul import *
from user_status_type import UserStatusType

from pandas import read_sql_query, to_datetime

from my_debuger import debug_error, debug_info

startLanguage = "none"

current_users_pointer_max_dict = dict()
current_users_pointer_min_dict = dict()

current_users_data_dict = dict()


class GenericUser(ABC):
    def __init__(self, id, full_name, tag):
        self.id = id
        self.full_name = full_name
        self.tag = tag
        self.language = startLanguage

    @abstractmethod
    def add_user(self, id, full_name, tag):
        pass

    @abstractmethod
    def load_user(self):
        pass

    @abstractmethod
    def set_language(self, new_language):
        pass

    def has_language(self):
        return self.language != startLanguage


class User(GenericUser):
    def __init__(self, id, full_name, tag):
        super().__init__(id, full_name, tag)

        self.status = None
        self.account_number = None
        self.had_trial_status = None
        self.trial_end_date = None
        self.before_trial_status = None
        self.time = None
        self.is_signal_allowed = None

        if not self.load_user():
            self.add_user(id, full_name, tag)
            self.load_user()

    def load_user(self):
        user_data = self.find_user_with_id(self.id)

        if user_data is None:
            return False

        self.full_name = user_data["full_name"]
        self.tag = user_data["tag"]
        self.language = user_data["language"]
        self.status = user_data["status"]
        self.account_number = user_data["account_number"]
        self.had_trial_status = user_data["had_trial_status"]
        self.trial_end_date = user_data["trial_end_date"]
        self.before_trial_status = user_data["before_trial_status"]
        self.time = user_data["time"]
        self.is_signal_allowed = user_data["get_next_signal"]
        return True

    @staticmethod
    def find_user_with_id(id):
        try:
            sql_query = f"SELECT * FROM {user_table} WHERE id = {id}"

            df = read_sql_query(sql_query, db_connection)

            if len(df) == 0:
                return None

            user_dict = {
                "id": df["id"][0],
                "full_name": df["name"][0],
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
            debug_error(error, "Error find user with id")
            return None

    def add_user(self, id, full_name, tag):
        cursor = db_connection.cursor()

        try:
            cursor.execute(f"SELECT * FROM {user_table} WHERE id = ?", (id,))
            user_exists = cursor.fetchone()

            if user_exists is None:
                cursor.execute(f'''
                    INSERT INTO {user_table} (
                        id, name, tag, language, status,
                        account_number, had_trial_status, trial_end_date,
                        before_trial_status, time, get_next_signal
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                ''', (
                    id, full_name, tag, startLanguage, UserStatusType.none_status.value,
                    0, False, None, "none", datetime_to_str(now_time()), False
                ))
                db_connection.commit()
        except sqlite3.Error as error:
            debug_error(error, f"Error add user with {id}")

    def set_language(self, new_language):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {user_table} SET language = ? WHERE id = ?", (new_language, self.id))
            db_connection.commit()
            self.language = new_language
        except sqlite3.Error as error:
            debug_error(error, f"Error change language {self.id}")

    def has_status(self, status: UserStatusType):
        return self.status == status.value

    def set_status(self, status: UserStatusType):
        cursor = db_connection.cursor()
        cursor.execute(f"UPDATE {user_table} SET status = ? WHERE id = ?", (status.value, self.id))
        db_connection.commit()
        self.status = status.value

    def remove(self):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f'''
                SELECT name, account_number, status FROM {user_table}
                WHERE id = ? AND status = ?
            ''', (self.id, UserStatusType.deposit_status.value))
            user = cursor.fetchone()

            if user:
                cursor.execute(f'''UPDATE {user_table} SET status = ?
                    WHERE id = ? AND status = ?
                ''', (UserStatusType.none_status.value, self.id, UserStatusType.deposit_status.value))
                db_connection.commit()
                self.status = UserStatusType.none_status.value
                return True
            else:
                return False
        except sqlite3.Error as error:
            debug_error(error, f"Error delete user with id {id}")
            return False

    def set_trial(self):
        cursor = db_connection.cursor()
        try:
            trial_end_date = market_info.get_trial_end_date()
            cursor.execute(f'''
                UPDATE {user_table}
                SET had_trial_status = 1, before_trial_status = status, status = ?, trial_end_date = ?
                WHERE id = ?
            ''', (UserStatusType.trial_status.value, trial_end_date, self.id))
            db_connection.commit()

            self.before_trial_status = self.status
            self.status = UserStatusType.trial_status.value
            self.trial_end_date = trial_end_date
            self.had_trial_status = True

        except sqlite3.Error as error:
            debug_error(error, f"Error set trial {self.id}")

    def has_tag(self):
        return self.tag != "none"

    def set_tag(self, tag):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {user_table} SET tag = ? WHERE id = ?", (tag, self.id))
            db_connection.commit()
            self.tag = tag
        except sqlite3.Error as error:
            debug_error(error, f"Error set tag")

    def set_account_number(self, account_number):
        try:
            cursor = db_connection.cursor()
            cursor.execute(f"UPDATE {user_table} SET account_number = ? WHERE id = ?", (account_number, self.id))
            db_connection.commit()
            self.account_number = account_number
        except sqlite3.Error as e:
            debug_error(e, error_name=f"Error update account {self.id}")

    def set_allow_signal(self, flag):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f"UPDATE {user_table} SET get_next_signal = ? WHERE id = ?", (flag, self.id))
            db_connection.commit()
            self.is_signal_allowed = flag
        except sqlite3.Error as error:
            debug_error(error, f"Error set_next_signal_status")

    @staticmethod
    def get_users_ids_with_status(status: UserStatusType):
        try:
            sql_query = f"SELECT * FROM {user_table} WHERE status = '{status.value}'"
            users_df = read_sql_query(sql_query, db_connection)
            return users_df["id"].values.tolist()
        except sqlite3.Error as error:
            debug_error(error, f"Error get users with status '{status.value}'")
            return []

    @staticmethod
    def get_user_with_status(status: UserStatusType):
        users_ids_with_status = User.get_users_ids_with_status(status)

        has_users_with_status = len(users_ids_with_status) > 0
        result_user = users_ids_with_status[0] if has_users_with_status else None

        return has_users_with_status, result_user

    def remove_trial(self):
        cursor = db_connection.cursor()
        try:
            cursor.execute(f'''
                UPDATE {user_table}
                SET status = before_trial_status, before_trial_status = ?
                WHERE id = ?
            ''', (UserStatusType.none_status.value, self.id))
            db_connection.commit()
            self.status = self.before_trial_status
            self.before_trial_status = UserStatusType.none_status.value
        except sqlite3.Error as error:
            debug_error(error, f"Error remove trial {self.id}")


def set_user_time(user_id, new_time):
    cursor = db_connection.cursor()
    try:
        cursor.execute(f"UPDATE {user_table} SET time = ? WHERE id = ?", (new_time, user_id))
        db_connection.commit()
    except sqlite3.Error as error:
        debug_error(error, f"Error set user time {user_id}")


def get_users_groups_ids(groups_count, users_in_group_count, delay_second):
    statuses = [UserStatusType.deposit_status.value, UserStatusType.trial_status.value]
    sql_query = f"""
        SELECT * FROM {user_table} 
        WHERE (status IN {tuple(statuses)} OR id IN {tuple(config.tester_ids)}) AND get_next_signal = {True} 
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


def get_users_strings():
    cursor = db_connection.cursor()

    users_strings_list = []
    users_data = []

    try:
        cursor.execute(f'''
            SELECT id, name, account_number, tag, status, trial_end_date
            FROM {user_table}
            WHERE status IN (?, ?)
        ''', (UserStatusType.deposit_status.value, UserStatusType.trial_status.value))

        rows = cursor.fetchall()
        user_number = 1

        for row in rows:
            telegram_id, telegram_name, account_number, tag, status, trial_end_date = row
            if status == UserStatusType.deposit_status.value:
                users_data.append((telegram_id, telegram_name, account_number))
                users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status}")
            elif status == UserStatusType.trial_status.value:
                formatted_end_date = secs_to_date(trial_end_date)
                users_data.append((telegram_id, telegram_name, account_number))
                users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status} | {formatted_end_date}")
            user_number += 1
        return users_strings_list, users_data
    except sqlite3.Error as error:
        debug_error(error, f"Error get users string")
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
