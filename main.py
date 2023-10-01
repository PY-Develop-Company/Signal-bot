import time

import indicators_reader
from aiogram import Bot, Dispatcher, types
import logging
import price_parser
import signal_maker
from tvDatafeed import Interval
import asyncio
import multiprocessing
from multiprocessing import Value, Array
import threading
from datetime import datetime
from user_module import *
from manager_module import *
from menu_text import *

# API_TOKEN = "6340912636:AAHACm2V2hDJUDXng0y0uhBRVRFJgqrok48"
API_TOKEN = "6538527964:AAHUUHZHYVnNFbYAPoMn4bRUMASKR0h9qfA"
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)

manager_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(search_id_request), types.KeyboardButton(search_deposit_request)]
])
accept_reject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(accept_button), types.KeyboardButton(reject_button)]
])
vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(contact_manager)]
])
not_vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(vip_status_info), types.KeyboardButton(check_id_text), types.KeyboardButton(contact_manager)]
])


async def get_chat_id(user_id):
    try:
        chat = await bot.get_chat(user_id)
        return chat.id
    except Exception as e:
        return 0


async def send_message_to_user(user_id, text):
    if await get_chat_id(user_id) == 0:
        return

    await bot.send_message(user_id, text, disable_notification=False)


async def send_message_to_users(users_ids: [], text):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_message_to_user(user_id, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def send_photo_text_message_to_user(user_id, img_path, text=" "):
    if await get_chat_id(user_id) == 0:
        return

    with open(img_path, "rb") as file:
        await bot.send_photo(user_id, photo=file, caption=text)


async def send_photo_text_message_to_users(users_ids: [], img_path, text=" "):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_photo_text_message_to_user(user_id, img_path, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def open_menu(message, menu_markup, answer_text=wait_command_text):
    await message.answer(answer_text, reply_markup=menu_markup)


async def update_account_user(id, account_number):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['acount_number'] = account_number
            if user['status'] == deposit_status:
                print(1)
                await send_message_to_user(id, get_vip_text)
            elif account_number == none_status:
                print(2)
                await send_message_to_user(id, reject_vip_text)
            break
    file_manager.write_file(user_db_path, data)


@dp.message_handler(commands="start")
async def start_command(message):
    await send_photo_text_message_to_user(message.from_user.id, start_img_path, start_text)
    if message.from_user.id in managers_id:
        await add_manager(message)
        await open_menu(message, manager_markup)
    elif has_user_status(message.from_user.id, deposit_status):
        await open_menu(message, vip_markup)
    else:
        add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name)
        await open_menu(message, not_vip_markup)


@dp.message_handler(commands="checkDeposit")
async def check_deposit_command(message):
    if message.from_user.id in managers_id:
        return

    if has_user_status(message.from_user.id, id_status):
        await message.answer(wait_deposit_status)
        await update_status_user(message.from_user.id, wait_deposit_status)


@dp.message_handler(commands="check")
async def check_command(message):
    if message.from_user.id in managers_id:
        return

    has_user_deposit_status = has_user_status(message.from_user.id, deposit_status)
    markup = vip_markup if has_user_deposit_status else not_vip_markup
    await open_menu(message, markup)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    # manager part
    if message.from_user.id in managers_id:
        if message.text == search_id_request:
            is_user_exists, user_id = await get_user_with_status(wait_id_status)
            if is_user_exists:
                update_manager_do(message.from_user.id, user_id)
                await update_manager_status(message.from_user.id, search_id_manager_status)
                await message.answer(get_manager_user_acount(message.from_user.id))
                await open_menu(message, accept_reject_markup)
            else:
                await message.answer(no_id_requests_text)
        elif message.text == search_deposit_request:
            is_user_exists, user_id = await get_user_with_status(wait_deposit_status)
            if is_user_exists:
                update_manager_do(message.from_user.id, user_id)
                await update_manager_status(message.from_user.id, search_deposit_manager_status)
                await message.answer(get_manager_user_acount(message.from_user.id))
                await open_menu(message, accept_reject_markup)
            else:
                await message.answer(no_deposit_requests_text)
        else:
            is_accept_button = message.text == accept_button
            is_reject_button = message.text == reject_button
            if is_accept_button or is_reject_button:
                is_search_id_status = is_manager_status(message.from_user.id, search_id_manager_status)
                is_search_deposit_status = is_manager_status(message.from_user.id, search_deposit_manager_status)

                user_under_do = get_manager_do(message.from_user.id)
                status = none_status
                message_to_user = ""

                if is_accept_button and is_search_id_status:
                    status = id_status
                    message_to_user = accept_id_message_text
                elif is_reject_button and is_search_id_status:
                    status = none_status
                    message_to_user = reject_id_message_text
                elif is_accept_button and is_search_deposit_status:
                    status = deposit_status
                    message_to_user = accept_deposit_message_text
                elif is_reject_button and is_search_deposit_status:
                    status = id_status
                    message_to_user = reject_deposit_message_text
                await update_status_user(user_under_do, status)

                await send_message_to_user(user_under_do, message_to_user)

                await open_menu(message, manager_markup)
                update_manager_do(message.from_user.id, "none")
                await update_manager_status(message.from_user.id, none_manager_status)
    # user part
    elif has_user_status(message.from_user.id, wait_id_input_status):
        # get id
        if message.text.isdigit() and len(message.text) == 8:
            await update_status_user(message.from_user.id, wait_id_status)
            await update_account_user(message.from_user.id, message.text)
            await message.answer(wait_id_status)
            await open_menu(message, vip_markup)
        else:
            await message.reply(error_id_text)
    else:  # answer for user
        if message.text == vip_status_info:
            if has_user_status(message.from_user.id, deposit_status):
                await message.answer(you_have_vip_text)
                await open_menu(message, vip_markup)
            else:
                await message.answer(for_vip_text)
        elif message.text == check_id_text:
            if has_user_status(message.from_user.id, deposit_status):
                await message.answer(you_have_vip_text)
                await open_menu(message, vip_markup)
            else:
                await update_status_user(message.from_user.id, wait_id_input_status)
                await message.answer(wait_id_text)
        elif message.text == contact_manager:
            await message.answer(contact_manager_text)
            await message.answer(manager_url)
        else:
            if has_user_status(message.from_user.id, deposit_status):
                await open_menu(message, vip_markup)
            else:
                await open_menu(message, not_vip_markup)


async def close_signal_message_check_function(open_position_price, vip_users_ids, open_signal, symbol, exchange, interval):
    close_signal_message, is_profit = await signal_maker.close_position(open_position_price, open_signal, symbol, exchange, interval, bars_count=3)
    print("closing", symbol, interval)
    await send_message_to_users(vip_users_ids, close_signal_message)
    return is_profit


def signal_message_check_controller(currency, interval, profit_dict):
    async def signal_message_check_function(currency, interval, start_check_time, profit_dict):
        is_file_changed, price_data_frame = price_parser.is_currency_file_changed(currency[0], interval)
        if is_file_changed:
            symbol = currency[0][:3] + "/" + currency[0][3:]

            interval = price_data_frame.datetime[0] - price_data_frame.datetime[1]
            has_signal, signal_type, debug_text = signal_maker.check_signal(
                price_data_frame, interval, successful_indicators_count=2)

            if has_signal:
                deposit_users_ids = get_deposit_users_ids()

                msg = signal_type.get_msg(symbol, interval)

                await send_photo_text_message_to_users(deposit_users_ids, signal_type.photo_path, msg + debug_text)
                delay_text = f"\n {currency} {interval} задержка: {datetime.now() - start_check_time}"
                await send_message_to_users(deposit_users_ids, delay_text)

                open_position_price = price_data_frame.close[0]
                is_profit = await close_signal_message_check_function(open_position_price, deposit_users_ids, signal_type, symbol, currency[1], interval)
                profit_dict[is_profit] += 1
                price_parser.update_last_check_date(currency[0], interval)

    async def signal_message_check_loop(currency, interval, profit_dict):
        while True:
            start_check_time = datetime.now()
            await signal_message_check_function(currency, interval, start_check_time, profit_dict)
            await asyncio.sleep(2)

    asyncio.run(signal_message_check_loop(currency, interval, profit_dict))


if __name__ == '__main__':
    from aiogram import executor

    profit_dict = Array('i', [0, 0])
    #
    currencies = [("BTCUSD", "COINBASE")] #("ETHUSD", "COINBASE")]  #price_parser.get_currencies()
    intervals = [Interval.in_1_minute]
    price_parser.create_parce_currencies_with_intervals_callbacks(currencies, intervals)
    #
    for interval in intervals:
        for currency in currencies:
            multiprocessing.Process(target=signal_message_check_controller, args=(currency, interval, profit_dict,)).start()

    executor.start_polling(dp, skip_updates=True)
