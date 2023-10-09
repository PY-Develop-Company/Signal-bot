import json
import os


def write_file(url, data):
    with open(url, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))


def read_file(url):
    with open(url, 'r', encoding="utf-8") as file:
        result = json.loads(file.read())
    return result


def is_file_exists(url):
    return os.path.exists(url)


def delete_file_if_exists(url):
    if is_file_exists(url):
        os.remove(url)
