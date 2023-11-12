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
import market_info
import asyncio
import multiprocessing
from manager_module import *
from menu_text import *
import interval_convertor
from signals import get_signal_by_type

API_TOKEN = "5767062743:AAF3wfEbw5gkKO6-jARSM29qHbg4PN1a_kA"  # my API
# API_TOKEN = "6340912636:AAHACm2V2hDJUDXng0y0uhBRVRFJgqrok48"  # main API TOKEN
logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
signal_delay = 300

callbacks_wait_time = 600

users_for_print_count = 15


last_user_list_message = dict()
last_user_manage_message = dict()

start_img_path = "img/logo.jpg"

cant_get_trial_error_text = "❗Ошибка (Вам невозможно получить пробную версию)"
already_had_trial_text = "На этом аккаунте уже активировали пробную версию! Это можно сделать только один раз!"
started_trial_text = "Поздравляем! Вы получили пробную версию бота и сможете получать сигналы в течение 3 дней бесплатно."
ended_trial_text = "Ой! У тебя завершилсась пробная версия. Чтобы снова получать сигналы нужно получить VIP статус."


def update_last_user_list_message(message):
    global last_user_list_message
    print("update before", last_user_list_message.get(message.chat.id, None))
    last_user_list_message.update({message.chat.id: message})
    print("update after", last_user_list_message.get(message.chat.id, None))


async def remove_last_user_list_message(user_id):
    global last_user_list_message
    message = last_user_list_message.get(user_id, None)

    print("remove before", last_user_list_message.get(user_id, None))
    if message is not None:
        try:
            await bot.delete_message(user_id, message.message_id)
            last_user_list_message.update({user_id: None})
        except:
            pass
    print("remove after", last_user_list_message.get(user_id, None))


def update_last_user_manage_message(message):
    global last_user_manage_message
    last_user_manage_message.update({message.chat.id: message})


async def remove_last_user_manage_message(user_id):
    global last_user_manage_message
    message = last_user_manage_message.get(user_id, None)

    if message is not None:
        try:
            await bot.delete_message(user_id, message.message_id)
            last_user_manage_message.update({user_id: None})
        except:
            pass


async def get_chat_id(user_id):
    try:
        chat = await bot.get_chat(user_id)
        return chat.id
    except Exception as e:
        return 0


async def send_message_to_user(user_id, text, markup=None):
    if await get_chat_id(user_id) == 0:
        return

    try:
        if markup is None:
            return await bot.send_message(user_id, text, disable_notification=False)
        else:
            return await bot.send_message(user_id, text, disable_notification=False, reply_markup=markup)
    except Exception as e:
        print("Error: bot is blocked by user", e)

    return None


async def send_message_to_users(users_ids: [], text):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_message_to_user(user_id, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def send_photo_text_message_to_user(user_id, img_path, text=" ", markup=None):
    if await get_chat_id(user_id) == 0:
        return

    try:
        with open(img_path, "rb") as file:
            if markup is None:
                await bot.send_photo(user_id, photo=file, caption=text)
            else:
                await bot.send_photo(user_id, photo=file, caption=text, reply_markup=markup)
    except Exception as e:
        print("Error: bot is blocked by user")


async def send_photo_text_message_to_users(users_ids: [], img_path, text=" "):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_photo_text_message_to_user(user_id, img_path, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def open_menu(message, menu_markup, answer_text="none"):
    await message.answer(answer_text, reply_markup=menu_markup)


async def update_account_user(id, account_number):
    data = file_manager.read_file(user_db_path)
    for user in data:
        found_user = user['id'] == id
        if found_user:
            user['acount_number'] = account_number
            if user['status'] == deposit_status:
                await send_message_to_user(id, languageFile[getUserLanguage(id)]["get_vip_text"])
            elif account_number == none_status:
                await send_message_to_user(id, languageFile[getUserLanguage(id)]["reject_vip_text"])
            break
    file_manager.write_file(user_db_path, data)


async def show_users_list_to_user(user_id, is_next=True):
    print_str = languageFile[getUserLanguage(user_id)]["users_list_title_text"] + "\n"

    users_to_show = []
    if is_next:
        users_to_show = next_user_strings(users_for_print_count, user_id)
    else:
        users_to_show = prev_user_strings(users_for_print_count, user_id)

    print(users_to_show)

    for user_to_show in users_to_show:
        print_str += "\n" + user_to_show

    if len(users_to_show) == 0:
        print_str = languageFile[getUserLanguage(user_id)]["no_users_list_title_text"]
    return await send_message_to_user(user_id, print_str, getUsersMarkup(getUserLanguage(user_id)))


@dp.message_handler(commands="start")
async def start_command(message):
    if message.from_user.id in managers_id:
        await add_manager(message)
    else:
        add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name)

    if getUserLanguage(message.from_user.id) == startLanguage:
        await open_menu(message, getSelectLanguageMarkap(), "Select language:")
        return

    # await send_photo_text_message_to_user(message.from_user.id, start_img_path, start_text)
    if message.from_user.id in managers_id:
        markup = getManagerMarkup(getUserLanguage(message.from_user.id))
    elif has_user_status(message.from_user.id, deposit_status):
        markup = getVipMarkup(getUserLanguage(message.from_user.id))
    else:
        markup = getNoVipMarkup(getUserLanguage(message.from_user.id))

    await send_photo_text_message_to_user(message.from_user.id, start_img_path, languageFile[getUserLanguage(message.from_user.id)]["start_text"], markup)


@dp.message_handler(commands="start_test")
async def start_test_command(message):
    if message.from_user.id in tester_ids:
        if message.from_user.id in tester_ids:
            msg = message.text.split(" ")[-1]
            if msg.isdigit():
                with open("users/test.txt", "w") as file:
                    file.write(str(float(msg) + time.time()))


@dp.message_handler(commands="stop_test")
async def stop_test_command(message):
    if message.from_user.id in tester_ids:
        with open("users/test.txt", "w") as file:
            file.write("0")


@dp.message_handler(commands="checkDeposit")
async def check_deposit_command(message):
    if message.from_user.id in managers_id:
        return

    if has_user_status(message.from_user.id, id_status):
        await message.answer(languageFile[getUserLanguage(message.from_user.id)]["wait_deposit_status"])
        await update_status_user(message.from_user.id, wait_deposit_status)


@dp.callback_query_handler(text_contains="removeuser_")
async def remove_user_command(call: types.CallbackQuery):
    await remove_last_user_list_message(call.message.chat.id)

    user_id = int(call.data.split("_")[-1])
    have_user_with_id = find_user_with_id(user_id)
    is_user_removed, user_string = remove_user_with_id(user_id)

    if have_user_with_id:
        if is_user_removed:
            await bot.send_message(call.message.chat.id, languageFile[getUserLanguage(call.message.chat.id)]["removed_user_text"] + f"\n " + user_string)
            await bot.send_message(user_id, text=languageFile[getUserLanguage(user_id)]["delete_vip_user_text"], reply_markup=getNoVipMarkup(getUserLanguage(user_id)))
        else:
            await bot.send_message(call.message.chat.id, languageFile[getUserLanguage(user_id)]["cant_remove_user_text"])
    else:
        await bot.send_message(call.message.chat.id, languageFile[getUserLanguage(user_id)]["error_no_user"])

    await call.answer(call.data)
    await remove_last_user_manage_message(call.message.chat.id)


@dp.message_handler(commands="trial")
async def get_trial_command(message):
    if has_user_status(message.from_user.id, deposit_status) or message.from_user.id in managers_id:
        await send_message_to_user(message.from_user.id, cant_get_trial_error_text)
        return
    elif had_trial_status(message.from_user.id):
        await send_message_to_user(message.from_user.id, already_had_trial_text)
        return
    else:
        await send_message_to_user(message.from_user.id, started_trial_text)
        set_trial_to_user(message.from_user.id)


@dp.message_handler(commands="users")
async def users_list_command(message):
    global last_user_list_message
    if message.from_user.id in managers_id:
        await remove_last_user_list_message(message.chat.id)
        await remove_last_user_manage_message(last_user_manage_message.get(message.chat.id))

        sent_msg = await show_users_list_to_user(message.from_user.id)
        update_last_user_list_message(sent_msg)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    if message.text in [select_language_eng, select_language_ru, select_language_hin] and getUserLanguage(message.from_user.id) == "none":
        setUserLanguage(message.from_user.id, message.text)
        markup = getMarkupWithStatus(message.from_user.id, get_user_status(message.from_user.id))

        await open_menu(message, markup, languageFile[getUserLanguage(message.from_user.id)]["selected_language_success_text"])
        await start_command(message)

        return

    # manager part
    if message.from_user.id in managers_id:
        if message.text == languageFile[getUserLanguage(message.from_user.id)]["user_management_button"]:
            await users_list_command(message)
        elif message.text == languageFile[getUserLanguage(message.from_user.id)]["search_id_request"]:
            is_user_exists, user_id = await get_user_with_status(wait_id_status)
            if is_user_exists:
                update_manager_do(message.from_user.id, user_id)
                await update_manager_status(message.from_user.id, search_id_manager_status)
                await open_menu(message, getAcceptRejectMarkup(getUserLanguage(message.from_user.id)), get_manager_user_acount(message.from_user.id))
            else:
                await message.answer(languageFile[getUserLanguage(message.from_user.id)]["no_id_requests_text"])
        elif message.text == languageFile[getUserLanguage(message.from_user.id)]["search_deposit_request"]:
            is_user_exists, user_id = await get_user_with_status(wait_deposit_status)
            if is_user_exists:
                update_manager_do(message.from_user.id, user_id)
                await update_manager_status(message.from_user.id, search_deposit_manager_status)
                await open_menu(message, getAcceptRejectMarkup(getUserLanguage(message.from_user.id)), get_manager_user_acount(message.from_user.id))
            else:
                await message.answer(languageFile[getUserLanguage(message.from_user.id)]["no_deposit_requests_text"])
        else:
            is_accept_button = message.text == languageFile[getUserLanguage(message.from_user.id)]["accept_button"]
            is_reject_button = message.text == languageFile[getUserLanguage(message.from_user.id)]["reject_button"]
            if is_accept_button or is_reject_button:
                is_search_id_status = is_manager_status(message.from_user.id, search_id_manager_status)
                is_search_deposit_status = is_manager_status(message.from_user.id, search_deposit_manager_status)

                user_under_do = get_manager_do(message.from_user.id)
                status = none_status
                message_to_user = ""

                if is_accept_button and is_search_id_status:
                    status = id_status
                    message_to_user = languageFile[getUserLanguage(user_under_do)]["accept_id_message_text"]
                elif is_reject_button and is_search_id_status:
                    status = none_status
                    message_to_user = languageFile[getUserLanguage(user_under_do)]["reject_id_message_text"]
                elif is_accept_button and is_search_deposit_status:
                    status = deposit_status
                    message_to_user = languageFile[getUserLanguage(user_under_do)]["accept_deposit_message_text"]
                elif is_reject_button and is_search_deposit_status:
                    status = id_status
                    message_to_user = languageFile[getUserLanguage(user_under_do)]["reject_deposit_message_text"]

                await update_status_user(user_under_do, status)
                await send_message_to_user(user_under_do, message_to_user, getMarkupWithStatus(user_under_do, status))

                await open_menu(message, getManagerMarkup(getUserLanguage(message.from_user.id)), languageFile[getUserLanguage(message.from_user.id)]["process_finishing_text"])
                update_manager_do(message.from_user.id, "none")
                await update_manager_status(message.from_user.id, none_manager_status)
    # user part
    elif has_user_status(message.from_user.id, wait_id_input_status):
        # get id
        if message.text.isdigit() and len(message.text) == 8:
            await update_status_user(message.from_user.id, wait_id_status)
            await update_account_user(message.from_user.id, message.text)
            await open_menu(message, getVipMarkup(getUserLanguage(message.from_user.id)),languageFile[getUserLanguage(message.from_user.id)]["wait_id_status"])
        else:
            await message.reply(languageFile[getUserLanguage(message.from_user.id)]["error_id_text"])
    else:  # answer for user
        if message.text == languageFile[getUserLanguage(message.from_user.id)]["vip_status_info"]:
            if has_user_status(message.from_user.id, deposit_status):
                await open_menu(message, getVipMarkup(getUserLanguage(message.from_user.id)), languageFile[getUserLanguage(message.from_user.id)]["you_have_vip_text"])
            else:
                await message.answer(languageFile[getUserLanguage(message.from_user.id)]["for_vip_text"])
        elif message.text == languageFile[getUserLanguage(message.from_user.id)]["check_id_text"]:#питання
            if has_user_status(message.from_user.id, deposit_status):
                await open_menu(message, getVipMarkup(getUserLanguage(message.from_user.id)), languageFile[getUserLanguage(message.from_user.id)]["you_have_vip_text"])
            else:
                await update_status_user(message.from_user.id, wait_id_input_status)
                await message.answer(languageFile[getUserLanguage(message.from_user.id)]["wait_id_text"])
        elif message.text == languageFile[getUserLanguage(message.from_user.id)]["contact_manager"]:#питання
            await message.answer(languageFile[getUserLanguage(message.from_user.id)]["contact_manager_text"])
            await message.answer(manager_url)
        else:
            if has_user_status(message.from_user.id, deposit_status):
                await open_menu(message, getVipMarkup(getUserLanguage(message.from_user.id)),1)
            else:
                ...
                # await open_menu(message, getNoVipMarkup(getUserLanguage(message.from_user.id)),)


@dp.callback_query_handler(text="next_users")
async def next_users_callback(call: types.CallbackQuery):
    global last_user_list_message
    print(10)
    await remove_last_user_list_message(call.message.chat.id)
    await remove_last_user_manage_message(call.message.chat.id)

    sent_msg = await show_users_list_to_user(call.message.chat.id)
    update_last_user_list_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text="previous_users")
async def previous_users_callback(call: types.CallbackQuery):
    print(10)
    global last_user_list_message
    await remove_last_user_list_message(call.message.chat.id)
    await remove_last_user_manage_message(call.message.chat.id)

    sent_msg = await show_users_list_to_user(call.message.chat.id, is_next=False)
    update_last_user_list_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text="manage_user")
async def manage_user_callback(call: types.CallbackQuery):
    global last_user_manage_message

    await remove_last_user_manage_message(call.message.chat.id)

    users_data = get_current_users_data(call.message.chat.id)
    buttons = []
    for user_data in users_data:
        buttons.append(types.InlineKeyboardButton(text=user_data[0], callback_data=f"removeuser_{user_data[1]}"))

    keyboard = types.InlineKeyboardMarkup(row_width=5).add(*buttons)
    sent_msg = await bot.send_message(call.message.chat.id, text=languageFile[getUserLanguage(call.message.chat.id)]["select_user_id_to_ban_text"], reply_markup=keyboard)

    update_last_user_manage_message(sent_msg)
    await call.answer(call.data)


def handle_signal_msg_controller(signal, msg, pd: PriceData, open_position_price, deal_time, start_analize_time):
    async def handle_signal_msg(signal, msg, pd: PriceData, open_position_price, deal_time, start_analize_time):
        deposit_users_ids = get_users_with_status(deposit_status)
        await send_photo_text_message_to_users(deposit_users_ids, signal.photo_path, msg)

        try:
            send_message_time = datetime.strptime(str(datetime.now(pytz.timezone("Europe/Bucharest"))).split(".")[0],
                                                  '%Y-%m-%d %H:%M:%S')
            start_analize_time = datetime.strptime(str(start_analize_time).split(".")[0], '%Y-%m-%d %H:%M:%S')
            delay = send_message_time - start_analize_time
            print("delay", delay)
            await send_message_to_users(managers_id, "delay: " + str(delay) + "; analize_time: " + str(
                start_analize_time) + "; send_msg_time: " + str(send_message_time))
        except Exception as e:
            print(e)

        close_signal_message, is_profit = await signal_maker.close_position(open_position_price, signal, pd,
                                                                            bars_count=deal_time)
        img_path = "./img/profit.jpg" if is_profit else "./img/loss.jpg"
        await send_photo_text_message_to_users(deposit_users_ids, img_path, close_signal_message)

    asyncio.run(handle_signal_msg(signal, msg, pd, open_position_price, deal_time, start_analize_time))


async def check_trial_users():
    users_ids = get_users_with_status(trial_status)
    for user_id in users_ids:
        if market_info.is_trial_ended(get_user_trial_end_date(user_id)):
            remove_trial_from_user(user_id)
            await send_message_to_user(user_id, ended_trial_text)
            await send_message_to_user(user_id, for_vip_text)


def signals_message_sender_controller(prices_data, intervals, unit_pd, prices_data_all):
    async def signals_message_sender_function(main_prices_data, intervals, unit_pd, prices_data_all):
        price_parser.create_parce_currencies_with_intervals_callbacks(prices_data_all)
        last_send_message_check = time.time()
        for pd in prices_data_all:
            pd.reset_chart_data()
        signal_maker.reset_signals_files(main_prices_data)

        need_to_reset_seis = False
        reset_seis_wait_time = 600

        while True:
            # need_to_reset_seis = time.time() - last_callback_update_time > callbacks_wait_time
            need_to_reset_seis = last_send_message_check + reset_seis_wait_time < time.time()
            if need_to_reset_seis:
                price_parser.create_parce_currencies_with_intervals_callbacks(prices_data_all)
                last_send_message_check = time.time()
                signal_maker.reset_signals_files(main_prices_data)
                continue

            await check_trial_users()
            await asyncio.sleep(3)
            try:
                with open("users/test.txt", "r") as file:
                    cont = file.read().split(".")[0]
                    if cont.isdigit():
                        cont = float(cont)
                        if cont > time.time():
                            print("wait for signal", cont, time.time())
                            continue
            except Exception as e:
                print("Error", e)
            print("search signals to send...")
            if not market_info.is_market_working():
                continue

            created_prices_data = []
            for pd in main_prices_data:
                if signal_maker.is_signal_analized(pd):
                    created_prices_data.append(pd)
            if len(created_prices_data) == 0:
                continue

            last_send_message_check = time.time()

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

            time_zone = pytz.timezone("Europe/Bucharest")
            time_now = datetime.now(time_zone)
            pd = PriceData(df.symbol[0], df.exchange[0], interval_convertor.str_to_interval(df.interval[0]))
            path = f"sended_signals/time{time_now.hour}_{time_now.minute}_{pd.symbol}_{interval_convertor.interval_to_string(pd.interval).replace('.', '')}"
            df.to_csv(path)

            multiprocessing.Process(target=handle_signal_msg_controller,
                                    args=(signal, df.msg[0], pd, df.open_price[0], int(df.deal_time[0]),
                                          df.start_analize_time[0]), daemon=True).start()

            await asyncio.sleep(signal_delay)

            signal_maker.reset_signals_files(main_prices_data)

    asyncio.run(signals_message_sender_function(prices_data, intervals, unit_pd, prices_data_all))


if __name__ == '__main__':
    from aiogram import executor

    # multiprocessing.freeze_support()
    # currencies = price_parser.get_currencies()
    #
    # intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute]
    # main_intervals = [Interval.in_1_minute, Interval.in_3_minute, Interval.in_5_minute]
    # parent_intervals = [
    #     [Interval.in_3_minute, Interval.in_5_minute],
    #     [Interval.in_5_minute, Interval.in_15_minute],
    #     [Interval.in_15_minute, Interval.in_30_minute]
    # ]
    # prices_data = []
    #
    # main_pds = []
    # parent_pds = []
    #
    # for currency in currencies:
    #     for interval in intervals:
    #         prices_data.append(PriceData(currency[0], currency[1], interval))
    #
    # ind = -1
    # for currency_index in range(len(currencies)):
    #     for main_interval_index in range(len(main_intervals)):
    #         main_pd = PriceData(currencies[currency_index][0], currencies[currency_index][1], main_intervals[main_interval_index])
    #         main_pds.append(main_pd)
    #         parent_pds.append([])
    #         ind += 1
    #         for p_i in parent_intervals[main_interval_index]:
    #             parent_pds[ind].append(PriceData(currencies[currency_index][0], currencies[currency_index][1], p_i))
    #
    # for pd in prices_data:
    #     pd.remove_chart_data()
    #
    # unit_pd = main_pds[0]
    # multiprocessing.Process(target=signals_message_sender_controller, args=(main_pds, main_intervals, unit_pd, prices_data)).start()
    #
    # analize_pairs = []
    # for i in range(len(main_pds)):
    #     i_main_pd = main_pds[i]
    #     i_parent_pds = parent_pds[i]
    #     analize_pair = (i_main_pd, i_parent_pds, unit_pd)
    #     analize_pairs.append(analize_pair)
    # multiprocessing.Process(target=signal_maker.analize_currency_data_controller, args=(analize_pairs, )).start()

    executor.start_polling(dp, skip_updates=True)
