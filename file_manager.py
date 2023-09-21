import json


def write_file(url, data):
    with open(url, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))


def read_file(url):
    with open(url, 'r', encoding="utf-8") as file:
        result = json.loads(file.read())
    return result