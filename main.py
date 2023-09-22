import time
import indicators_reader
from aiogram import Bot, Dispatcher, types
import logging
import price_parser
import signal_maker
from pandas import Timedelta
from tvDatafeed import TvDatafeedLive, Interval
import asyncio
import multiprocessing
from datetime import datetime
from user_module import *

API_TOKEN = "6340912636:AAHACm2V2hDJUDXng0y0uhBRVRFJgqrok48"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

db_path = "users/db.txt"

manager_username = "@indddij"
managers_id = [2091413236, 5359645780]
manager_url = f"https://t.me/{manager_username[1:]}"

accept_id_message_text = """Поздравляем ваш ID подтвержден. Чтобы получить доступ к сигналам внесите депозит и отправьте заявку боту.
Для отправки проверки на депозит нажмите:
 /checkDeposit """
accept_deposit_message_text = """Поздравляем ваш депозит внесен. Теперь вы имеете полный доступ к сигналам"""
reject_id_message_text = """К сожалению ваш ID не подтвержден. Проверьте правильно ли вы его указали и попробуйте снова

нажмите /start что бы продолжит"""
reject_deposit_message_text = """Ваш депозит не внесен. Проверьте действительно ли вы его внесли и отправьте запрос на проверку снова
Для отправки проверки на депозит нажмите:
/checkDeposit"""

accept_button = "ПОДТВЕРДИТЬ"
reject_button = "ОТКЛОНИТЬ"

search_id_request = "ПОДТВЕРДИТЬ ID"
search_deposit_request = "ПОДТВЕРДИТЬ ДЕПОЗИТЫ"
check_text = "Какой выдать статус пользователю"
registration_text = "Введите свой ID :"

start_img_path = "img/logo.jpg"
start_text = """Приветствую тебя трейдер 👋

В моём закрытом сообществе, я ежедневно выдаю более 1ООО торговых прогнозов 🕯 с полной аналитикой валютной пары и проходимостью от 92% 📊"""

photo_long_path = "img/long.jpg"
photo_short_path = "img/short.jpg"

for_vip_text = "Для получения VIP выполните следующие условия:"
you_have_vip_text = "У вас уже активный VIP статус"
get_vip_text = """Поздравляю, ваша заявка принята, вам предоставлен VIP-статус 
для начала работы нажмите: /check """
reject_vip_text = "К сожалению, ваша заявка не принята"

search_id_manager_status = "пошук ID статус"
search_deposit_manager_status = "пошук депозиту статус"

wait_id = "Отправте свой ID"

check_deposit_text = "ПРОВЕРИТЬ ДЕПОЗИТ"
check_id_text = "ПРОВЕРИТЬ ID"
error_id_text = """❗Ошибка (ID должен состоять из 8 цифр)
Попробуйте отправить еще раз: 
"""

contact_manager = "ПОДДЕРЖКА"
contact_manager_text = "Данные менеджера: "
none_manager_status = "none"

vip_status_info = "ДОСТУП К СИГНАЛАМ"
no_id_requests_text = "Все заявки на проверку ID обработаны"
no_deposit_requests_text = "Все заявки на проверки депозита обработаны"

wait_comand_text = "Ожидание команды:"


async def get_chat_id(user_id):
    try:
        chat = await bot.get_chat(user_id)
        return chat.id
    except Exception as e:
        print(f"Error: {e}")
        return 0


def get_deposit_users_ids():
    data = file_manager.read_file(db_path)
    vip_users = []
    for user in data:
        if has_user_status(user['id'], deposit_status):
            vip_users.append(user['id'])
    return vip_users


def update_manager_do(message, do):
    url = f"users/{message.from_user.id}.txt"
    manager = file_manager.read_file(url)
    manager["do"] = do
    file_manager.write_file(url, manager)


async def update_manager_status(message, status):
    url = f"users/{message.from_user.id}.txt"
    manager = file_manager.read_file(url)
    manager["status"] = status
    file_manager.write_file(url, manager)


def check_manager_do(message):
    url = f"users/{message.from_user.id}.txt"
    manager = file_manager.read_file(url)
    return manager["do"]


def check_manager_status(message, status):
    url = f"users/{message.from_user.id}.txt"
    manager = file_manager.read_file(url)
    return manager["status"] == status


async def send_message_to_user(user_id, text):
    if await get_chat_id(user_id) is None:
        ...
    else:
        await bot.send_message(user_id, text, disable_notification=False)


async def update_status_user(id, status):
    data = file_manager.read_file(db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['status'] = status
            if status == deposit_status:
                await send_message_to_user(id, get_vip_text)
            elif status == none_status:
                await send_message_to_user(id, reject_vip_text)
            break
        else:
            ...
    file_manager.write_file(db_path, data)


async def update_acount_user(id, acount_number):
    data = file_manager.read_file(db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['acount_number'] = acount_number
            if user['status'] == deposit_status:
                await send_message_to_user(id, get_vip_text)
            elif acount_number == none_status:
                await send_message_to_user(id, reject_vip_text)
            break
        else:
            ...
    file_manager.write_file(db_path, data)


async def search_user_with_status(message, status):
    data = file_manager.read_file(db_path)
    for user in data:
        user_id = user['id']
        if status == wait_id_status:
            is_status = has_user_status(user_id, status)
            if is_status:
                return True, user_id
        if status == wait_deposit_status:
            is_status = has_user_status(user_id, status)
            if is_status:
                return True, user_id
    return False, None


async def manager_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(search_id_request)
    item2 = types.KeyboardButton(search_deposit_request)
    markup.add(item1, item2)
    await message.answer(wait_comand_text, reply_markup=markup)


async def reg_id_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(deposit_status)
    item2 = types.KeyboardButton(contact_manager)
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
    item2 = types.KeyboardButton(check_id_text)
    item3 = types.KeyboardButton(contact_manager)
    markup.add(item1, item2, item3)
    await message.answer(wait_comand_text, reply_markup=markup)


async def accept_id_and_deposit_menu(message):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    item1 = types.KeyboardButton(accept_button)
    item2 = types.KeyboardButton(reject_button)
    markup.add(item1, item2)
    await message.answer(wait_comand_text, reply_markup=markup)


async def add_manager(message):
    url = f"users/{message.from_user.id}.txt"
    data = {"id": message.from_user.id, "status": "none", "do": "none"}
    file_manager.write_file(url, data)


async def photo_text_message(user_id, img_path, text=" "):
    if img_path == start_img_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text, parse_mode="HTML")
    elif img_path == photo_long_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text)
    elif img_path == photo_short_path:
        await bot.send_photo(user_id, photo=open(img_path, "rb"), caption=text, parse_mode="HTML")


@dp.message_handler(commands="start")
async def create_user(message):
    await photo_text_message(message.from_user.id, start_img_path, start_text)
    if message.from_user.id in managers_id:
        await add_manager(message)
        await manager_menu(message)
    elif has_user_status(message.from_user.id, deposit_status):
        await vip_main_menu(message)
    else:
        add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name)
        await not_vip_main_menu(message)


@dp.message_handler(commands="checkDeposit")
async def check_deposit(message):
    if has_user_status(message.from_user.id,id_status):
        await message.answer(wait_deposit_status)
        print(0)
        await update_status_user(message.from_user.id, wait_deposit_status)


@dp.message_handler(commands="check")
async def create_user(message):
    if has_user_status(message.from_user.id, deposit_status):
        await vip_main_menu(message)
    else:
        await not_vip_main_menu(message)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    # manager part
    if message.from_user.id in managers_id:
        if message.text == search_id_request:
            is_user_exists, user_id = await search_user_with_status(message, wait_id_status)
            if is_user_exists:
                update_manager_do(message, user_id)
                await update_manager_status(message, search_id_manager_status)
                await message.answer(check_manager_do(message))
                await accept_id_and_deposit_menu(message)
            else:
                await message.answer(no_id_requests_text)
        elif message.text == search_deposit_request:
            is_user_exists, user_id = await search_user_with_status(message, wait_deposit_status)
            if is_user_exists:
                update_manager_do(message, user_id)
                await update_manager_status(message, search_deposit_manager_status)
                await message.answer(check_manager_do(message))
                await accept_id_and_deposit_menu(message)
            else:
                await message.answer(no_deposit_requests_text)
        else:
            if message.text == accept_button or message.text == reject_button:
                if message.text == accept_button and check_manager_status(message, search_id_manager_status):
                    await update_status_user(check_manager_do(message), id_status)
                    await send_message_to_user(check_manager_do(message), accept_id_message_text)
                elif message.text == reject_button and check_manager_status(message, search_id_manager_status):
                    await update_status_user(check_manager_do(message), none_status)
                    await send_message_to_user(check_manager_do(message), reject_id_message_text)
                    await not_vip_main_menu(message)
                elif message.text == accept_button and check_manager_status(message, search_deposit_manager_status):
                    await update_status_user(check_manager_do(message), deposit_status)
                    await send_message_to_user(check_manager_do(message), accept_deposit_message_text)
                elif message.text == reject_button and check_manager_status(message, search_deposit_manager_status):
                    await update_status_user(check_manager_do(message), id_status)
                    await send_message_to_user(check_manager_do(message), reject_deposit_message_text)
                await manager_menu(message)
                update_manager_do(message, "none")
                await update_manager_status(message, none_manager_status)
    #user part
    elif has_user_status(message.from_user.id, wait_id):
        #get id
        if message.text.isdigit() and len(message.text) == 8 and has_user_status(message.from_user.id, wait_id):
            await update_status_user(message.from_user.id, wait_id_status)
            await update_acount_user(message.from_user.id, message.text)
            await message.answer(wait_id_status)
            await vip_main_menu(message)
        else:
            await message.reply(error_id_text)
    else:#answer for user
        if message.text == vip_status_info:
            if has_user_status(message.from_user.id, deposit_status):
                await message.answer(you_have_vip_text)
                await vip_main_menu(message)
            else:
                await message.answer(for_vip_text)
        elif message.text == check_id_text:
            if has_user_status(message.from_user.id, deposit_status):
                await message.answer(you_have_vip_text)
                await vip_main_menu(message)
            else:
                await message.answer(wait_id)
                await update_status_user(message.from_user.id, wait_id)
        elif message.text == contact_manager:
            await message.answer(contact_manager_text)
            await message.answer(manager_url)
        else:
            if has_user_status(message.from_user.id, deposit_status):
                await vip_main_menu(message)
            else:
                await not_vip_main_menu(message)


def open_signal_check_thread(interval):
    async def open_signal_check(interval):
        while True:
            print(datetime.now())
            vip_users_ids = get_deposit_users_ids()
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
                            await photo_text_message(user_id, photo_long_path,
                                                     signal_maker.get_open_position_signal_message(open_signal[1],
                                                                                                   symbol,
                                                                                                   timedelta_interval))
                        if open_signal[1] == signal_maker.sell_signal:
                            await photo_text_message(user_id, photo_short_path,
                                                     signal_maker.get_open_position_signal_message(open_signal[1],
                                                                                                   symbol,
                                                                                                   timedelta_interval))
                        # message = await bot.send_message(
                        #     user_id,
                        #     signal_maker.get_open_position_signal_message(open_signal[1], symbol, timedelta_interval),
                        #     disable_notification=False,
                        #     parse_mode="HTML"
                        # )

                    p = multiprocessing.Process(target=close_signal_check_thread,
                                                args=(
                                                    open_position_price, data.close, vip_users_ids, open_signal[1],
                                                    symbol,
                                                    timedelta_interval))
                    p.start()
                    # print("send messages data time", datetime.now())
            delay_minutes = (data.datetime[0] - data.datetime[1]) / Timedelta(minutes=1)
            time.sleep(delay_minutes * 60)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(open_signal_check(interval))


def close_signal_check_thread(open_position_price, close_prices_search_info, vip_users_ids, open_signal, symbol,
                              interval):
    async def close_signal_check(open_position_price, close_prices_search_info, vip_users_ids, open_signal, symbol,
                                 interval):
        close_signal = await signal_maker.close_position(open_position_price, close_prices_search_info, open_signal,
                                                         symbol, interval, bars_count=3)
        for user_id in vip_users_ids:
            await bot.send_message(
                user_id,
                close_signal,
                disable_notification=False,
                parse_mode="HTML"
            )

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(
        close_signal_check(open_position_price, close_prices_search_info, vip_users_ids, open_signal, symbol, interval))


def update_currency_file_consumer(seis, data):
    price_data = price_parser.get_price_data_seis(seis)
    interval = indicators_reader.get_interval_string(indicators_reader.get_interval(price_data.datetime[0] - price_data.datetime[1]))

    symbol = price_data.symbol[0].split(":")[1]
    print(symbol, interval)
    price_parser.save_currency_file(price_data, symbol, interval)


def test_core_controller(intervals):
    async def test_core_function(intervals):
        # print("test_core_function")
        while True:
            for currency in price_parser.get_currencies()[0:1]:
                # print("check", currency)
                for currency_interval in intervals:
                    # print("currency_interval", currency_interval)
                    is_file_changed, priceData = price_parser.is_currency_file_changed(currency[0], str(currency_interval).replace(".", ""))
                    if is_file_changed:

                        symbol = priceData.symbol[0].split(":")
                        symbol = symbol[1][:3] + "/" + symbol[1][3:]
                        date_format = '%Y-%m-%d %H:%M:%S'

                        interval = datetime.strptime(priceData.datetime[0], date_format) - datetime.strptime(priceData.datetime[1], date_format)
                        has_signal, open_signal_type = signal_maker.check_signal(priceData, interval, successful_indicators_count=4)
                        if has_signal:
                            for user_id in get_deposit_users_ids():
                                if await get_chat_id(user_id) is None:
                                    continue

                                photo_path = photo_long_path
                                if open_signal_type == signal_maker.buy_signal:
                                    photo_path = photo_long_path
                                elif open_signal_type == signal_maker.sell_signal:
                                    photo_path = photo_short_path

                                await photo_text_message(user_id, photo_path,
                                                         signal_maker.get_open_position_signal_message(
                                                             open_signal_type,
                                                             symbol,
                                                             interval))

            print("test_core_function loop")
            await asyncio.sleep(2)

    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    loop.run_until_complete(test_core_function(intervals))


if __name__ == '__main__':
    from aiogram import executor

    # intervals = [Interval.in_15_minute, Interval.in_5_minute, Interval.in_1_minute]
    intervals = [Interval.in_1_minute]
    currencies = price_parser.get_currencies()
    # price_parser.create_save_currencies_files(currencies, intervals)
    tvl = TvDatafeedLive()
    for currency in currencies[:1]:
        # print(currency[0])
        seis1 = tvl.new_seis(currency[0], currency[1], Interval.in_1_minute)
        consumer1 = tvl.new_consumer(seis1, update_currency_file_consumer)
        # seis5 = tvl.new_seis(currency[0], currency[1], Interval.in_5_minute)
        # consumer5 = tvl.new_consumer(seis5, update_currency_file_consumer)
        # seis15 = tvl.new_seis(currency[0], currency[1], Interval.in_15_minute)
        # consumer15 = tvl.new_consumer(seis15, update_currency_file_consumer)

    # p1 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_1_minute,))
    # p2 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_15_minute,))
    # p3 = multiprocessing.Process(target=open_signal_check_thread, args=(Interval.in_5_minute,))
    test_core = multiprocessing.Process(target=test_core_controller, args=(intervals, ))
    # # # # p1.start()
    # # # # p2.start()
    # # # # p3.start()
    test_core.start()

    executor.start_polling(dp, skip_updates=True)
