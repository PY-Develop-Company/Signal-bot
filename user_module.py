import file_manager
import manager_module
import market_info

user_db_path = "users/db.txt"
startLanguage="none"

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


def remove_user_with_id(id):
    users_data = file_manager.read_file(user_db_path)
    for i, user_data in enumerate(users_data):
        if int(user_data['id']) == id:
            if users_data[i]['status'] == deposit_status:
                users_data[i]['status'] = none_status
                data = users_data[i]['name'] + " | " + str(users_data[i]['acount_number']) + " | " + users_data[i]['status']
                file_manager.write_file(user_db_path, users_data)
                return True, data
    return False, ""


def get_users_strings():
    data = file_manager.read_file(user_db_path)
    print(data)
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
            users_strings_list.append(f"{user_number}. @{tag} | {telegram_name} | {account_number} | {status} | {market_info.secs_to_date(end_date)}")
            user_number += 1

    return users_strings_list, users_data


def get_current_users_data(manager_id):
    return current_users_data_dict.get(manager_id, [])


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

    print("user_strs", users_strings_list)

    counter = 1
    strings = []

    if current_users_pointer_max_dict.get(manager_id, -1) + 1 >= len(users_strings_list):
        current_users_pointer_max_dict.update({manager_id: -1})
    range_val = range(current_users_pointer_max_dict.get(manager_id, -1) + 1, len(users_strings_list))
    print(range_val)
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


def has_user_status(id, status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id and user['status'] == status:
            return True
    return False


def getUserLanguage(id):
    if id in manager_module.managers_id:
        return manager_module.getManagerLanguage(id)
    else:
        data = file_manager.read_file(user_db_path)
        for user in data:
            if user['id'] == id:
                return user['language']


def setUserLanguage(id, newLanguage):
    if id in manager_module.managers_id:
        manager_module.setManagerLanguage(id, newLanguage)
    else:
        data = file_manager.read_file(user_db_path)
        for user in data:
            if user['id'] == id:
                 user['language'] = newLanguage
        file_manager.write_file(user_db_path, data)


def get_users_with_status(status):
    data = file_manager.read_file(user_db_path)
    users_with_status = []
    for user in data:
        id = user['id']
        if has_user_status(id, status):
            users_with_status.append(id)
    return users_with_status


def had_trial_status(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return user['had_trial_status']


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
    for user in data:
        if user["id"] == id:
            return user["trial_end_date"]


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
            "before_trial_status": "none"
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


async def setUserTag(id, tag):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['tag'] = tag
            break
    file_manager.write_file(user_db_path, data)



async def get_user_with_status(status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        user_id = user['id']
        is_status = has_user_status(user_id, status)
        if is_status:
            return True, user_id
    return False, None


def get_user_status(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return user["status"]
    return None


def get_user_Tag(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return user["tag"]
    return None


def get_user_account_number(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return user["acount_number"]
    return None


def find_user_with_id(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return True
    return False

