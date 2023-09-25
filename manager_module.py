import file_manager

manager_username = "@bwg_Golden"
managers_id = [5964166439]
manager_url = f"https://t.me/{manager_username[1:]}"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"


def get_url(manager_id):
    return f"users/{manager_id}.txt"


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


def check_manager_do(manager_id):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return manager["do"]


def check_manager_status(manager_id, status):
    url = get_url(manager_id)
    manager = file_manager.read_file(url)
    return manager["status"] == status

