import file_manager

user_db_path = "users/db.txt"

current_users_pointer_max = -1
current_users_pointer_min = -1

current_users_data = []

# STATUSES
deposit_status = "status ДЕПОЗИТ"
id_status = "status ID"
none_status = "status none"
wait_id_status = 'Ожидайте проверку ID ⏳'
wait_id_input_status = 'Ожидание ввода проверки ID 🔖'
wait_deposit_status = 'Ожидание проверки депозита 💵'


def remove_user_with_id(id):
    users_data = file_manager.read_file(user_db_path)
    for i, user_data in enumerate(users_data):
        if int(user_data['id']) == id and users_data[i]['status'] == deposit_status:
            users_data[i]['status'] = none_status
            data = users_data[i]['name'] + " | " + users_data[i]['acount_number'] + " | " + users_data[i]['status']
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
        if status == deposit_status:
            telegram_id = user['id']
            telegram_name = user['name']
            account_number = user['acount_number']
            users_data.append((telegram_id, telegram_name, account_number))
            users_strings_list.append(f"{user_number}. {telegram_name} \a| {account_number} \a| {status}")
            user_number += 1

    return users_strings_list, users_data


def get_current_users_data():
    return current_users_data


def prev_user_strings(users_for_print_count):
    global current_users_pointer_min, current_users_pointer_max, current_users_data
    users_strings_list, users_data = get_users_strings()

    counter = 1
    strings = []

    if current_users_pointer_min - 1 < 0:
        current_users_pointer_min = len(users_strings_list)
    range_val = range(current_users_pointer_min - 1, -1, -1)

    current_users_pointer_max = current_users_pointer_min - 1
    new_current_users_data = []
    for i in range_val:
        strings.append(users_strings_list[i])
        new_current_users_data.append((i+1, *users_data[i]))
        counter = counter + 1
        is_last_user = (i == 0)
        if counter > users_for_print_count or is_last_user:
            current_users_pointer_min = i
            break

    new_current_users_data.reverse()
    strings.reverse()
    current_users_data = new_current_users_data
    return strings


def next_user_strings(users_for_print_count):
    global current_users_pointer_max, current_users_pointer_min, current_users_data
    users_strings_list, users_data = get_users_strings()

    counter = 1
    strings = []

    if current_users_pointer_max + 1 >= len(users_strings_list):
        current_users_pointer_max = -1
    range_val = range(current_users_pointer_max + 1, len(users_strings_list))

    current_users_pointer_min = current_users_pointer_max + 1
    new_current_users_data = []
    for i in range_val:
        strings.append(users_strings_list[i])
        new_current_users_data.append((i+1, *users_data[i]))
        counter = counter + 1
        is_last_user = (i == len(users_strings_list) - 1)
        if counter > users_for_print_count or is_last_user:
            current_users_pointer_max = i
            break

    current_users_data = new_current_users_data
    return strings


def has_user_status(id, status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id and user['status'] == status:
            return True
    return False


def getUserLanguage(id):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id:
            return user['language']


def get_users_with_status(status):
    data = file_manager.read_file(user_db_path)
    users_with_status = []
    for user in data:
        id = user['id']
        if has_user_status(id, status):
            users_with_status.append(id)
    return users_with_status


def add_user(id, first_name, last_name):
    data = file_manager.read_file(user_db_path)
    user_exists = any(user['id'] == id for user in data)
    if user_exists:
        ...
    else:
        full_name = f"{first_name} {last_name}"
        bufer_user = {
            "id": id,
            "name": full_name,
            "language":"none",
            "status": "none",
            "acount_number": 0
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


async def get_user_with_status(status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        user_id = user['id']
        is_status = has_user_status(user_id, status)
        if is_status:
            return True, user_id
    return False, None


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
