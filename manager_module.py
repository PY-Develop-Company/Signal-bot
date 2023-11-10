import file_manager
from user_module import *

manager_username = "@bwg_Golden"
tester_ids = [741867026, 693562775]
managers_id = [5964166439, 741867026, 693562775, 6916117863]
manager_url = f"https://t.me/{manager_username[1:]}"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"
none_manager_status = "none"


def get_url(manager_id):
    return f"users/{manager_id}.txt"


async def add_manager(message):
    url = f"users/{message.from_user.id}.txt"
    data = {"id": message.from_user.id, "status": "none", "do": "none"}
    file_manager.write_file(url, data)


def update_manager_do(manager_id, do):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    manager["do"] = do
    file_manager.write_file(url, manager)


async def update_manager_status(manager_id, status):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    manager["status"] = status
    file_manager.write_file(url, manager)


def get_manager_do(manager_id):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return manager["do"]


def get_manager_user_acount(manager_id):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return get_user_account_number(int(manager["do"]))


def is_manager_status(manager_id, status):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return manager["status"] == status
