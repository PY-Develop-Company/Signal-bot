import os
import user_module
from user_module import *

manager_username = "@NoMeFU"

tester_ids = [741867026, 693562775]
managers_id = [741867026, 693562775]
manager_url = f"https://t.me/{manager_username[1:]}"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"
none_manager_status = "none"


def get_url(manager_id):
    return f"users/{manager_id}.txt"


async def add_manager(message):
    url = f"users/{message.from_user.id}.txt"
    if f"{message.from_user.id}.txt" in os.listdir("users/"):
        ...
    else:
        data = {"id": message.from_user.id, "status": "none", "do": "none", "language": "none"}
        file_manager.write_file(url, data)


def get_manager_language(id):
    url = get_url(id)
    manager = file_manager.read_file(url)
    return manager["language"]


def set_manager_language(id, language):
    url = get_url(id)
    manager = file_manager.read_file(url)
    manager["language"] = language
    file_manager.write_file(url, manager)


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
    return user_module.get_user_account_number(int(manager["do"]))


def is_manager_status(manager_id, status):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return manager["status"] == status
