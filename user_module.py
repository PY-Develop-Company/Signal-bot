import asyncio
from my_time import secs_to_date
import file_manager
import manager_module
import market_info
from datetime import timedelta
from my_time import datetime_to_str, now_time, str_to_datetime

user_db_path = "users/db.txt"
startLanguage = "none"

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
    data = file_manager.read_file(user_db_path)
    users_with_id = [user for user in data if user['id'] == id]

    if len(users_with_id) > 0:
        user = users_with_id[0]
        return user
    return None


def get_user_time(id):
    user = find_user_with_id(id)

    if not(user is None):
        return str_to_datetime(user['time'])
    return None


def set_user_time(id, new_time):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            user['time'] = new_time
            file_manager.write_file(user_db_path, data)
            return


async def get_users_groups_ids(groups_count, users_in_group_count, delay_second):
    while True:
        try:
            DB = file_manager.read_file(user_db_path)
            break
        except Exception as e:
            print("Error", e)
            await asyncio.sleep(0.5)

    statuses = [deposit_status, trial_status]
    signal_users = []
    for user in DB:
        if user["status"] in statuses or user["id"] in manager_module.tester_ids:
            user['time'] = str_to_datetime(user['time'])
            signal_users.append(user)

    sorted_users = sorted(signal_users, key=lambda x: x['time'])
    all_users_count = groups_count * users_in_group_count
    if len(sorted_users) > all_users_count:
        sorted_users = sorted_users[:all_users_count]

    result_users_groups = []
    group = []
    for user in sorted_users:
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
    users_data = file_manager.read_file(user_db_path)
    for i, user_data in enumerate(users_data):
        if int(user_data['id']) == id and users_data[i]['status'] == deposit_status:
            users_data[i]['status'] = none_status
            data = users_data[i]['name'] + " | " + str(users_data[i]['acount_number']) + " | " + users_data[i]['status']
            file_manager.write_file(user_db_path, users_data)
            return True, data
    return False, ""


def get_users_strings():
    data = file_manager.read_file(user_db_path)
    users_strings_list = []
    user_number = 1

    users_data = []
    for i, user in enumerate(data):
        status = user['status']
        telegram_id = user['id']
        telegram_name = user['name']
        account_number = user['acount_number']
        tag = user['tag']
        if status == deposit_status:
            users_data.append((telegram_id, telegram_name, account_number))
            users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status}")
            user_number += 1
        elif status == trial_status:
            end_date = user['trial_end_date']
            users_data.append((telegram_id, telegram_name, account_number))
            users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status} | {secs_to_date(end_date)}")
            user_number += 1

    return users_strings_list, users_data


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
            current_users_pointer_min_dict.update({manager_id: current_users_pointer_max_dict.get(manager_id) - users_for_print_count + 1})
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
            current_users_pointer_max_dict.update({manager_id: current_users_pointer_min_dict.get(manager_id) + users_for_print_count - 1})
            break

    current_users_data_dict.update({manager_id: new_current_users_data})
    return strings


def get_current_users_data(manager_id):
    return current_users_data_dict.get(manager_id, [])


def has_user_status(id, status):
    user = find_user_with_id(id)

    if not(user is None) and user['status'] == status:
        return True
    return False


def get_user_language(id):
    if id in manager_module.managers_id:
        return manager_module.get_manager_language(id)
    else:
        user = find_user_with_id(id)
        if not (user is None):
            return user['language']
    return None


def set_user_language(id, new_language):
    if id in manager_module.managers_id:
        manager_module.set_manager_language(id, new_language)
    else:
        data = file_manager.read_file(user_db_path)
        for user in data:
            if user['id'] == id:
                 user['language'] = new_language
        file_manager.write_file(user_db_path, data)


# def set_next_signal_status(id, flag):
#     data = file_manager.read_file(user_db_path)
#     for user in data:
#         if user['id'] == id:
#              user['get_next_signal'] = flag
#     file_manager.write_file(user_db_path, data)
#
#
# def get_next_signal_status(id):
#     user = find_user_with_id(id)
#     if not (user is None):
#         return user['get_next_signal']
#     return None


def get_users_with_status(status):
    data = file_manager.read_file(user_db_path)
    users_with_status = [user["id"] for user in data if user["status"] == status]
    return users_with_status


def had_trial_status(id):
    user = find_user_with_id(id)
    if not (user is None):
        return user['had_trial_status']
    return None


def set_trial_to_user(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user["had_trial_status"] = True
            user['before_trial_status'] = user['status']
            user['status'] = trial_status
            user['trial_end_date'] = market_info.get_trial_end_date()
            break
    file_manager.write_file(user_db_path, data)


def remove_trial_from_user(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['status'] = user['before_trial_status']
            user['before_trial_status'] = none_status
            break
    file_manager.write_file(user_db_path, data)


def get_user_trial_end_date(id):
    data = file_manager.read_file(user_db_path)
    users = [user['trial_end_date'] for user in data if user['id'] == id]

    if len(users) > 0:
        return users[0]
    return None


def add_user(id, first_name, last_name, tag):
    data = file_manager.read_file(user_db_path)
    user_exists = any(user['id'] == id for user in data)
    if user_exists:
        ...
    else:
        full_name = f"{first_name} {last_name}"
        bufer_user = {
            "id": id,
            "name": full_name,
            "tag": tag,
            "language": startLanguage,
            "status": none_status,
            "acount_number": 0,
            "had_trial_status": False,
            "trial_end_date": None,
            "before_trial_status": "none",
            "time": datetime_to_str(now_time())
        }
        data.append(bufer_user)
        file_manager.write_file(user_db_path, data)


async def update_status_user(id, status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['status'] = status
            break
    file_manager.write_file(user_db_path, data)


async def set_user_tag(id, tag):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['tag'] = tag
            break
    file_manager.write_file(user_db_path, data)


async def get_user_with_status(status):
    data = file_manager.read_file(user_db_path)
    users = [user for user in data if user['status'] == status]

    if len(users) > 0:
        return True, users[0]['id']
    return False, None


def get_user_status(id):
    user = find_user_with_id(id)
    if not (user is None):
        return user['status']
    return None


def get_user_tag(id):
    user = find_user_with_id(id)
    if not (user is None):
        return user['tag']
    return None


def get_user_account_number(id):
    user = find_user_with_id(id)
    if not (user is None):
        return user['acount_number']
    return None


def have_user_with_id(id):
    user = find_user_with_id(id)
    return not (user is None)


async def main():
    await get_users_groups_ids(50, 20, 60*5)


if __name__ == "__main__":
    asyncio.run(main())
