import os
import time
import threading
from aiogram import Bot, Dispatcher, types, exceptions
import logging
import json
import price_parser
import signal_maker
from pandas import Timedelta
from tvDatafeed import TvDatafeedLive, Interval
import asyncio
import multiprocessing
from datetime import datetime

API_TOKEN = "6340912636:AAHACm2V2hDJUDXng0y0uhBRVRFJgqrok48"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

db_path = "users/db.txt"

manager_username = "@indddij"
managers_id = [2091413236]
manager_url = f"https://t.me/{manager_username[1:]}"

start_search_manager = "Подтверждение VIP-аккаунтов"
check_text = "Какой выдать статус пользователю"

start_img_path="img/logo.jpg"
start_text = """Приветствую тебя трейдер 👋

В моём закрытом сообществе, я ежедневно выдаю более 1ООО торговых прогнозов 🕯 с полной аналитикой валютной пары и проходимостью от 92% 📊"""

photo_long_path="img/long.jpg"
photo_short_path="img/short.jpg"

for_vip_text = "Для получения VIP выполните следующие условия:"
you_have_vip_text = "У вас уже активный VIP статус"
get_vip_text = """Поздравляю, ваша заявка принята, вам предоставлен VIP-статус 
для начала работы нажмите: /check """
reject_vip_text = "К сожалению, ваша заявка не принята"

vip_status = "Предоставить VIP статус"
none_status = "Отказать в VIP статусе"
wait_status = 'Ожидание проверки статуса'

contact_manager = "ПОДДЕРЖКА"
contact_manager_text="Данные менеджера :"
apply_for_vip_status = "ПРОВЕРИТЬ ID"
vip_status_info = "ДОСТУП К СИГНАЛАМ"
no_VIP_requests_text = "Все заявки в VIP обработаны"

wait_comand_text = "Ожидание команды:"


async def get_chat_id(user_id):
    try:
        chat_member = await bot.get_chat(user_id)
        chat_id = chat_member.id
        return chat_id
    except Exception as e:
        print(f"Error: {e}")
        return None


def get_vip_users_ids():
    data = read_file(db_path)
    vip_users = []
    for user in data:
        if has_user_status(user['id'], vip_status):
            vip_users.append(user['id'])
    return vip_users


def update_status(message, status):
    url = f"users/{message.from_user.id}.txt"
    data ={"id":message.from_user.id, "status": status}
    write_file(url,data)


def write_file(url, data):
    with open(url, "w", encoding="utf-8") as file:
        file.write(json.dumps(data, ensure_ascii=False))


def read_file(url):
    with open(url, 'r', encoding="utf-8") as file:
        result = json.loads(file.read())
    return result


async def update_manager_status(message, status):
    url = f"users/{message.from_user.id}.txt"
    manager = read_file(url)
    manager["do"] = status
    write_file(url, manager)


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


async def send_message_to_user(user_id, text):
    if await get_chat_id(user_id) is None:
        ...
    else:
        await bot.send_message(user_id, text, disable_notification=False)


async def update_status_user(id, status):
    data = read_file(db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['status'] = status
            if status == vip_status:
                await send_message_to_user(id, get_vip_text)
            elif status == none_status:
                await send_message_to_user(id, reject_vip_text)
            break
        else:
            ...
    write_file(db_path, data)


async def search_no_vip(message):
    data = read_file(db_path)
    for user in data:
        user_status = user['status'] == wait_status
        if user_status:
            user_id = user['id']
            await update_manager_status(message, user_id)
            return user_id
        else:
            ...
    return no_VIP_requests_text


async def manager_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(start_search_manager)
    markup.add(item1)
    await message.answer(wait_comand_text, reply_markup=markup)


async def accept_vip_accounts_menu(message):
    request_db = await search_no_vip(message)
    if request_db == no_VIP_requests_text:
        await manager_menu(message)
    else:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        item1 = types.KeyboardButton(vip_status)
        item2 = types.KeyboardButton(none_status)
        markup.add(item1, item2)
        await message.answer(wait_comand_text, reply_markup=markup)


async def vip_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(contact_manager)
    markup.add(item1)
    await message.answer(wait_comand_text, reply_markup=markup)
    pass


async def not_vip_main_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(vip_status_info)
    item2 = types.KeyboardButton(apply_for_vip_status)
    item3 = types.KeyboardButton(contact_manager)
    markup.add(item1, item2, item3)
    await message.answer(wait_comand_text, reply_markup=markup)


async def add_user(message):
    data = read_file(db_path)
    user_exists = any(user['id'] == message.from_user.id for user in data)
    if user_exists:
        ...
    else:
        full_name = f"{message.from_user.first_name} {message.from_user.last_name}"
        bufer_user = {"id": message.from_user.id, "name": full_name, "status": "none", "acount_number": 0}
        data.append(bufer_user)
        write_file(db_path, data)


async def add_manager(message):
    url = f"users/{message.from_user.id}.txt"
    data = {"id": message.from_user.id, "do": "none"}
    write_file(url, data)


async def photo_text_message(user_id, img_path, text=" "):
    if text == " ":
        ...
    elif img_path == start_img_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text, parse_mode="HTML")
    elif img_path == photo_long_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text, parse_mode="HTML")
    elif img_path == photo_short_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text, parse_mode="HTML")


@dp.message_handler(commands="start")
async def create_user(message):
    # os.makedirs(f"users/{message.from_user.id}", exist_ok=True)
    await photo_text_message(message.from_user.id, start_img_path, start_text)
    if message.from_user.id in managers_id:
        await add_manager(message)
        await manager_menu(message)
    elif has_user_status(message.from_user.id, vip_status):
        await vip_main_menu(message)
    else:
        await add_user(message)
        await not_vip_main_menu(message)


@dp.message_handler(commands="check")
async def create_user(message):
    if has_user_status(message.from_user.id, vip_status):
        await vip_main_menu(message)
    else:
        await not_vip_main_menu(message)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    if message.from_user.id in managers_id:
        if message.text == start_search_manager:
            await message.answer(await search_no_vip(message))
            await accept_vip_accounts_menu(message)
        else:
            test = await check_manager_status(message)
            status = none_status
            if message.text == vip_status:
                status = vip_status
            elif message.text == none_status:
                status = none_status
            await update_status_user(test, status)
            await manager_menu(message)
    elif message.text == vip_status_info:
        if has_user_status(message.from_user.id, vip_status):
            await message.answer(you_have_vip_text)
            await vip_main_menu(message)
        else:
            await message.answer(for_vip_text)
    elif message.text == apply_for_vip_status:
        if has_user_status(message.from_user.id, vip_status):
            await message.answer(you_have_vip_text)
            await vip_main_menu(message)
        else:
            await message.answer(wait_status)
            await update_status_user(message.from_user.id, wait_status)
    elif message.text == contact_manager:
        await message.answer(contact_manager_text)
        await message.answer(manager_url)
    else:
        if has_user_status(message.from_user.id, vip_status):
            await vip_main_menu(message)
        else:
            await not_vip_main_menu(message)


def open_signal_check_thread(interval):
    async def open_signal_check(interval):
        while True:
            print(datetime.now())
            vip_users_ids = get_vip_users_ids()
            for currency in price_parser.get_currencies():
                # print("read data time", datetime.now())
                data = price_parser.get_price_data(symbol=currency[0], exchange=currency[1], interval=interval)
                # print(data.datetime[0])

                timedelta_interval = data.datetime[0] - data.datetime[1]
                symbol = data.symbol[0].split(":")
                symbol = symbol[1][:3] + "/" + symbol[1][3:]
                open_signal = signal_maker.check_signal(data, interval, successful_indicators_count=4)
                if open_signal[0]:
                    open_position_price = data.close[0]
                    print(open_signal[1])
                    for user_id in vip_users_ids:
                        if await get_chat_id(user_id) is None:
                            continue
                        if open_signal[1] == signal_maker.buy_signal:
                            await photo_text_message(user_id, photo_long_path, signal_maker.get_open_position_signal_message(open_signal[1], symbol, timedelta_interval))
                        if open_signal[1] == signal_maker.sell_signal:
                            await photo_text_message(user_id, photo_short_path, signal_maker.get_open_position_signal_message(open_signal[1], symbol, timedelta_interval))
                            # message = await bot.send_message(
                        #     user_id,
                        #     signal_maker.get_open_position_signal_message(open_signal[1], symbol, timedelta_interval),
                        #     disable_notification=False,
                        #     parse_mode="HTML"
                        # )

                    p = multiprocessing.Process(target=close_signal_check_thread,
                                                args=(open_position_price, data.close, vip_users_ids, open_signal[1], symbol, timedelta_interval))
                    p.start()
                    # print("send messages data time", datetime.now())
            delay_minutes = (data.datetime[0] - data.datetime[1]) / Timedelta(minutes=1)
            time.sleep(delay_minutes * 60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(open_signal_check(interval))


def close_signal_check_thread(open_position_price, close_prices, vip_users_ids, open_signal, symbol, interval):
    async def close_signal_check(open_position_price, close_prices, vip_users_ids, open_signal, symbol, interval):
        close_signal = await signal_maker.close_position(open_position_price, close_prices, open_signal, symbol, interval, bars_count=3)
        for user_id in vip_users_ids:
            await bot.send_message(
                user_id,
                close_signal,
                disable_notification=False,
                parse_mode="HTML"
            )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(close_signal_check(open_position_price, close_prices, vip_users_ids, open_signal, symbol, interval))

async def text2(open_signal, symbol, timedelta_interval, user_id):
    if open_signal[1] == signal_maker.buy_signal:
        await photo_text_message(user_id, photo_long_path,
                                 signal_maker.get_open_position_signal_message(open_signal[1], symbol,
                                                                               timedelta_interval))
    if open_signal[1] == signal_maker.sell_signal:
        await photo_text_message(user_id, photo_long_path,
                                 signal_maker.get_open_position_signal_message(open_signal[1], symbol,
                                                                               timedelta_interval))
async def test(open_signal, symbol, timedelta_interval):
    for user_id in get_vip_users_ids():
        if await get_chat_id(user_id) is None:
            continue
        try:
            await asyncio.wait_for(text2(open_signal, symbol, timedelta_interval, user_id), timeout=30)
        except asyncio.TimeoutError:
            print("Timeout in main!")


def consumer_func1(seis, data):
    data = price_parser.get_price_data_seis(seis)
    open_signal = signal_maker.check_signal(data, seis.interval, successful_indicators_count=1)
    print(open_signal)
    if open_signal[0]:
        timedelta_interval = data.datetime[0] - data.datetime[1]
        symbol = data.symbol[0].split(":")
        symbol = symbol[1][:3] + "/" + symbol[1][3:]
        open_position_price = data.close[0]
        print(open_signal[1])
        asyncio.run(test(open_signal, symbol, timedelta_interval))


if __name__ == '__main__':
    # while True:
    #     print(datetime.now())
    #     time.sleep(1)
    from aiogram import executor
    p1 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_1_minute,))
    p2 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_15_minute,))
    p3 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_5_minute,))

    p1.start()
    p2.start()
    p3.start()

    # tvl = TvDatafeedLive()

    # currencies = price_parser.get_currencies()
    # for currency in currencies:
    #     seis = tvl.new_seis(currency[0], currency[1], Interval.in_1_minute)
    #     consumer = tvl.new_consumer(seis, consumer_func1)
    #     seis1 = tvl.new_seis(currency[0], currency[1], Interval.in_5_minute)
    #     consumer1 = tvl.new_consumer(seis1, consumer_func1)
    #     seis2 = tvl.new_seis(currency[0], currency[1], Interval.in_15_minute)
    #     consumer2 = tvl.new_consumer(seis2, consumer_func1)
    #     print("customer:", consumer)

    executor.start_polling(dp, skip_updates=True)
