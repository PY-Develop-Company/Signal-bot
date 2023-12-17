import json
import os
import time

file_error = "FILE_READ_ERROR"
retry_wait_time = 3

def write_file(url, data):
    while True:
        try:
            with open(url, "w", encoding="utf-8-sig") as file:
                file.write(json.dumps(data, ensure_ascii=False))

            break
        except PermissionError as e:
            print(file_error, e)
            time.sleep(retry_wait_time)


def read_file(url):
    while True:
        try:
            with open(url, 'r', encoding="utf-8-sig") as file:
                result = json.loads(file.read())
            return result
        except PermissionError as e:
            print(file_error, e)
            time.sleep(retry_wait_time)


def is_file_exists(url):
    return os.path.exists(url)


def delete_file_if_exists(url):
    while True:
        try:
            if is_file_exists(url):
                os.remove(url)

            break
        except PermissionError as e:
            print(file_error, e)
            time.sleep(retry_wait_time)
