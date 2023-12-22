import json
import os

file_error = "FILE_READ_ERROR"
retry_wait_time = 3


def write_file(url, data):
    try:
        with open(url, "w", encoding="utf-8-sig") as file:
            file.write(json.dumps(data, ensure_ascii=False))
    except PermissionError as e:
        print(file_error, e)


def read_file(url):
    try:
        with open(url, 'r', encoding="utf-8-sig") as file:
            result = json.loads(file.read())
        return result
    except PermissionError as e:
        print(file_error, e)
        return ""


def is_file_exists(url):
    return os.path.exists(url)


def delete_file_if_exists(url):
    try:
        if is_file_exists(url):
            os.remove(url)
    except PermissionError as e:
        print(file_error, e)

