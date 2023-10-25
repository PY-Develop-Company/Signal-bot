import random
import time
from datetime import datetime
import pytz
from aiogram import Bot, Dispatcher, types
import logging
import price_parser
from price_parser import PriceData
import signal_maker
from tvDatafeed import Interval
import asyncio
import multiprocessing
from manager_module import *
from menu_text import *
import interval_convertor
from signals import get_signal_by_type

API_TOKEN = "6340912636:AAHACm2V2hDJUDXng0y0uhBRVRFJgqrok48"  # main API TOKEN
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
signal_delay = 300

callbacks_wait_time = 60

min_time_zone_hours = 10
max_time_zone_hours = 23

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

    try:
        await bot.send_message(user_id, text, disable_notification=False)
    except Exception as e:
        print("Error: bot is blocked by user")


async def send_message_to_users(users_ids: [], text):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_message_to_user(user_id, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def send_photo_text_message_to_user(user_id, img_path, text=" "):
    if await get_chat_id(user_id) == 0:
        return

    try:
        with open(img_path, "rb") as file:
            await bot.send_photo(user_id, photo=file, caption=text)
    except Exception as e:
        print("Error: bot is blocked by user")


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
                await send_message_to_user(id, get_vip_text)
            elif account_number == none_status:
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


def handle_signal_msg_controller(signal, msg, pd: PriceData, open_position_price, deal_time):
    async def handle_signal_msg(signal, msg, pd: PriceData, open_position_price, deal_time):
        deposit_users_ids = get_deposit_users_ids()
        await send_photo_text_message_to_users(deposit_users_ids, signal.photo_path, msg)

        close_signal_message, is_profit = await signal_maker.close_position(open_position_price, signal, pd, bars_count=deal_time)
        img_path = "./img/profit.jpg" if is_profit else "./img/loss.jpg"
        await send_photo_text_message_to_users(deposit_users_ids, img_path, close_signal_message)
    asyncio.run(handle_signal_msg(signal, msg, pd, open_position_price, deal_time))


def is_market_working():
    time_zone = pytz.timezone("Europe/Bucharest")
    time_now = datetime.now(time_zone)

    print(f"time hour {time_now.hour}")
    print(f"max_time_zone_hours {max_time_zone_hours}")
    print(f"min_time_zone_hours {min_time_zone_hours}")
    print(f"bool {min_time_zone_hours <= time_now.hour < max_time_zone_hours}")
    return min_time_zone_hours <= time_now.hour < max_time_zone_hours


def signals_message_sender_controller(prices_data, intervals, unit_pd, prices_data_all):
    async def signals_message_sender_function(prices_data, intervals, unit_pd, prices_data_all):
        signal_maker.reset_signals_files(prices_data)

        last_callback_update_time = time.time()

        while True:
            if time.time() - last_callback_update_time > callbacks_wait_time:
                price_parser.create_parce_currencies_with_intervals_callbacks(prices_data_all)
                last_callback_update_time = time.time()
                continue

            await asyncio.sleep(10)
            if not is_market_working():
                continue

            created_prices_data = []
            for pd in prices_data:
                if signal_maker.is_signal_analized(pd):
                    created_prices_data.append(pd)
            if len(created_prices_data) == 0:
                continue

            dfs_with_signals = []
            for pd in created_prices_data:
                df = signal_maker.read_signal_data(pd)
                if df.has_signal[0]:
                    dfs_with_signals.append(df)

            if len(dfs_with_signals) == 0:
                print("No signals detected. Deleting signal files:")
                for pd in created_prices_data:
                    pd.print()
                signal_maker.reset_signals_files(created_prices_data)
                continue

            df = random.choice(dfs_with_signals)
            signal = get_signal_by_type(df.signal_type[0])

            pd = PriceData(df.symbol[0], df.exchange[0], interval_convertor.str_to_interval(df.interval[0]))

            multiprocessing.Process(target=handle_signal_msg_controller,
                                    args=(signal, df.msg[0], pd, df.open_price[0], int(df.deal_time[0]), ), daemon=True).start()

            await asyncio.sleep(signal_delay)

            signal_maker.reset_signals_files(prices_data)

    asyncio.run(signals_message_sender_function(prices_data, intervals, unit_pd, prices_data_all))


def inf_loop_func():
    while True:
        time.sleep(5)
        print("sleeped")


if __name__ == '__main__':
    from aiogram import executor

    currencies = price_parser.get_currencies()
    intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]
    main_intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute]
    parent_intervals = [
        [Interval.in_3_minute, Interval.in_5_minute],
        [Interval.in_5_minute, Interval.in_15_minute],
        [Interval.in_15_minute, Interval.in_30_minute]
    ]
    prices_data = []

    main_pds = []
    parent_pds = []

    intervals_set = set()
    for interval in main_intervals:
        intervals_set.add(interval)
    for intervals in parent_intervals:
        for interval in intervals:
            intervals_set.add(interval)
    intervals_set = list(intervals_set)
    for currency in currencies:
        for interval in intervals_set:
            prices_data.append(PriceData(currency[0], currency[1], interval))

    ind = -1
    for currency_ind in range(len(currencies)):
        for main_interval_index in range(len(main_intervals)):
            main_pd = PriceData(currencies[currency_ind][0], currencies[currency_ind][1], main_intervals[main_interval_index])
            main_pds.append(main_pd)
            parent_pds.append([])
            ind += 1
            for p_i in parent_intervals[main_interval_index]:
                parent_pds[ind].append(PriceData(currencies[currency_ind][0], currencies[currency_ind][1], p_i))

    price_parser.create_parce_currencies_with_intervals_callbacks(prices_data)

    for pd in prices_data:
        pd.reset_chart_data()

    unit_pd = main_pds[0]
    unit_pd.print()
    analize_pairs = []
    for i in range(len(main_pds)):
        i_main_pd = main_pds[i]
        i_parent_pds = parent_pds[i]
        analize_pair = (i_main_pd, i_parent_pds, unit_pd)
        analize_pairs.append(analize_pair)
    multiprocessing.Process(target=signal_maker.analize_currency_data_controller, args=(analize_pairs, )).start()

    multiprocessing.Process(target=signals_message_sender_controller, args=(main_pds, main_intervals, unit_pd, prices_data)).start()

    executor.start_polling(dp, skip_updates=True)
