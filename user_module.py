import file_manager

user_db_path = "users/db.txt"

# STATUSES
deposit_status = "status ДЕПОЗИТ"
id_status = "status ID"
none_status = "status none"
wait_id_status = 'Ожидание проверки ID'
wait_deposit_status = 'Ожидание проверки депозита'


def has_user_status(id, status):
    data = file_manager.read_file(user_db_path)
    for user in data:
        if user['id'] == id and user['status'] == status:
            return True
    return False


def get_deposit_users_ids():
    data = file_manager.read_file(user_db_path)
    vip_users = []
    for user in data:
        if has_user_status(user['id'], deposit_status):
            vip_users.append(user['id'])
    return vip_users


def add_user(id, first_name, last_name):
    data = file_manager.read_file(user_db_path)
    user_exists = any(user['id'] == id for user in data)
    if user_exists:
        ...
    else:
        full_name = f"{first_name} {last_name}"
        bufer_user = {"id": id, "name": full_name, "status": "none", "acount_number": 0}
        data.append(bufer_user)
        file_manager.write_file(user_db_path, data)