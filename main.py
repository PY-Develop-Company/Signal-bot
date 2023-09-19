import os
import time
import threading
from aiogram import Bot, Dispatcher, types
import logging
import json
import parse
import signal_maker
from pandas import Timedelta


API_TOKEN = "6037306867:AAE7op0UnUoe4nzZGPFLUGLPOikMpoI4ADc"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

db_path = "users/db.txt"

manager_username ="@test_nano"
managers_id = [5359645780]
manager_url = f"https://t.me/{manager_username[1:]}"

start_search_manager = "VIP ?"
check_text = "Який видати статус користувачу"

for_vip_text = "Для отримання VIP..."
you_have_vip_text ="У вас вже активний vip"

vip_status ="vip"
nf_vip_status = "nf"
none_status = "none"
wait_status='Очікуємо перевірки'


def update_status(message,status):
    url = f"users/{message.from_user.id}.txt"
    data ={"id":message.from_user.id,"status":status}
    write_file(url,data)


def write_file(url, data):
    with open(url, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))


def read_file(url):
    with open(url, 'r', encoding="utf-8") as file:
        result = json.loads(file.read())
    return result


async def update_manager_status(message,status):
    url = f"users/{message.from_user.id}.txt"
    manager = read_file(url)
    manager["do"]=status
    write_file(url,manager)


async def check_manager_status(message):
    url = f"users/{message.from_user.id}.txt"
    manager = read_file(url)
    return manager["do"]


def has_user_status(user_id, status):
    data = read_file(db_path)
    for user in data:
        if user['id'] == user_id and user['status'] == status:
            return True
    return False


async def update_status_user(id, status):
    data = read_file(db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['status'] = status
            break
        else: ...
    write_file(db_path,data)


async def search_no_vip(message):
    data = read_file(db_path)
    user_id=0
    for user in data:
        user_status = user['status'] == wait_status
        if user_status:
            user_id = user['id']
            await update_manager_status(message,user_id)
            return user_id
        else:
            ...
    return "Всі заявки у vip оброблені"


async def edit_user_menu(message):
    await message.answer(await search_no_vip(message))
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(vip_status)
    item2 = types.KeyboardButton(nf_vip_status)
    item3 = types.KeyboardButton(none_status)
    markup.add(item1,item2,item3)
    await message.answer("Виберіть статус :", reply_markup=markup)


async def manager_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(start_search_manager)
    markup.add(item1)
    await message.answer("Жду команди:", reply_markup=markup)


async def vip_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("связаться с менеджером")
    markup.add(item1)
    await message.answer("Оберіть опцію:", reply_markup=markup)
    pass


async def not_vip_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton("хочу в вип")
    item2 = types.KeyboardButton("проверить")
    item3 = types.KeyboardButton("связаться с менеджером")
    markup.add(item1, item2, item3)
    await message.answer("Оберіть опцію:", reply_markup=markup)


async def add_user(message):
    data = read_file(db_path)
    user_exists = any(user['id'] == message.from_user.id for user in data)
    if user_exists:
        ...
    else:
        full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
        bufer_user = {"id": message.from_user.id, "name": full_name, "status": "none"}
        data.append(bufer_user)
        write_file(db_path, data)


async def add_manager(message):
    url = f"users/{message.from_user.id}.txt"
    data = {"id":message.from_user.id,"do":"none"}
    write_file(url,data)


@dp.message_handler(commands="start")
async def create_user(message):
    # os.makedirs(f"users/{message.from_user.id}", exist_ok=True)
    if message.from_user.id in managers_id:
        await add_manager(message)
        await manager_menu(message)
    elif has_user_status(message.from_user.id, vip_status):
        await vip_main_menu(message)
    else:
        await add_user(message)
        await not_vip_main_menu(message)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    if message.text == start_search_manager and message.from_user.id in managers_id:
        await edit_user_menu(message)

    elif message.text == vip_status and message.from_user.id in managers_id:
        test = await check_manager_status(message)
        print(" >>  ",test)
        await update_status_user(test,vip_status)
    elif message.text == nf_vip_status and message.from_user.id in managers_id:
        ...
    elif message.text == none_status and message.from_user.id in managers_id:
        ...

    elif message.text == "хочу в вип":
        if has_user_status(message.from_user.id, vip_status):
            await message.answer(you_have_vip_text)
            await vip_main_menu(message)
        else:
            await message.answer(for_vip_text)
    elif message.text == "проверить":
        if has_user_status(message.from_user.id,vip_status):
            await message.answer(you_have_vip_text)
            await vip_main_menu(message)
        else:
            await message.answer(wait_status)
            await update_status_user(message.from_user.id,wait_status)
    elif message.text == "связаться с менеджером":
        await message.answer("Контакти менеджера :")
        await message.answer(manager_url)
    else:
        if has_user_status(message.from_user.id,vip_status):
            await vip_main_menu(message)
        else:
            await not_vip_main_menu(message)


def signal_check():
    while True:
        pd = parse.get_price_data()
        signal = signal_maker.check_signal(pd, successful_indicators_count=2)
        if signal[0]:
            print(signal[1])

        delay_minutes = (pd.datetime[0]-pd.datetime[1]) / Timedelta(minutes=1)
        print("delay_minutes ", delay_minutes)
        time.sleep(delay_minutes*60)


if __name__ == '__main__':
    from aiogram import executor
    t1 = threading.Thread(target=signal_check, daemon=False)
    t1.start()

    print(threading.active_count())
    print(threading.enumerate())
    executor.start_polling(dp, skip_updates=True)


