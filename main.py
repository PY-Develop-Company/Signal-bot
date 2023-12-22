import random
import time
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
from pandas import DataFrame, read_csv, to_datetime, concat

API_TOKEN = "6538527964:AAGQzoisiQ7HNNpwfxuhEP771tLEV9msRJA"  # main API TOKEN

manager = None
shared_list = None

logging.basicConfig(level=logging.INFO)
bot = Bot(token=API_TOKEN)
dp = Dispatcher(bot)
signal_search_delay = 60
signal_for_user_delay = 300

callbacks_wait_time = 600

users_for_print_count = 15

send_msg_delay = 0.1
repeat_count = 50
send_msg_users_group_count = 20

last_user_list_message = dict()
last_user_manage_message = dict()

signals_stats_path = "signals/signals.csv"
start_img_path = "img/logo.jpg"

last_check_time = market_info.get_time()


def update_last_user_list_message(message):
    global last_user_list_message
    last_user_list_message.update({message.chat.id: message})


async def remove_last_user_list_message(user_id):
    global last_user_list_message
    message = last_user_list_message.get(user_id, None)

    if message is not None:
        try:
            await bot.delete_message(user_id, message.message_id)
            last_user_list_message.update({user_id: None})
        except:
            pass


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


async def send_photo_text_message_to_user(user_id, img_path, text=" ", markup=None, args=[]):
    if await get_chat_id(user_id) == 0:
        return
    if get_user_language(user_id) == "none":
        return

    if len(args) > 0:
        input_text = args.copy()
        for i, arg in enumerate(args):
            input_text[i] = languageFile[get_user_language(user_id)][arg]
        text = text.format(*input_text)
    try:
        with open(img_path, "rb") as file:
            if markup is None:
                await bot.send_photo(user_id, photo=file, caption=text)
            else:
                await bot.send_photo(user_id, photo=file, caption=text, reply_markup=markup)
    except Exception as e:
        print("Error: bot is blocked by user", e)


async def send_photo_text_message_to_users(users_ids: [], img_path, text=" ", args=[]):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_photo_text_message_to_user(user_id, img_path, text, args=args))
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
                await send_message_to_user(id, languageFile[get_user_language(id)]["get_vip_text"])
            elif account_number == none_status:
                await send_message_to_user(id, languageFile[get_user_language(id)]["reject_vip_text"])
            break
    file_manager.write_file(user_db_path, data)


async def show_users_list_to_user(user_id, is_next=True):
    print_str = languageFile[get_user_language(user_id)]["users_list_title_text"] + "\n"

    users_to_show = []
    if is_next:
        users_to_show = next_user_strings(users_for_print_count, user_id)
    else:
        users_to_show = prev_user_strings(users_for_print_count, user_id)

    for user_to_show in users_to_show:
        print_str += "\n" + user_to_show

    if len(users_to_show) == 0:
        print_str = languageFile[get_user_language(user_id)]["no_users_list_title_text"]
    return await send_message_to_user(user_id, print_str, get_users_markup(get_user_language(user_id)))


@dp.message_handler(commands="start")
async def start_command(message):
    if message.from_user.id in managers_id:
        await add_manager(message)
    else:
        add_user(message.from_user.id, message.from_user.first_name, message.from_user.last_name, message.from_user.username)

    if get_user_language(message.from_user.id) == startLanguage:
        await open_menu(message, get_select_language_markap(), "Select language:")
        return

    if message.from_user.id in managers_id:
        markup = get_manager_markup(get_user_language(message.from_user.id))
    else:
        markup = get_markup_with_status(message.from_user.id, get_user_status(message.from_user.id))

    if has_user_status(message.from_user.id, deposit_status):
        msg_text = languageFile[get_user_language(message.from_user.id)]["start_vip_text"]
    else:
        msg_text = languageFile[get_user_language(message.from_user.id)]["start_text"]
    await send_photo_text_message_to_user(message.from_user.id, start_img_path, msg_text, markup)


@dp.message_handler(commands="language")
async def open_language_command(message):
    set_user_language(message.from_user.id, startLanguage)
    await open_menu(message, get_select_language_markap(), "Select language:")


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
        await message.answer(languageFile[get_user_language(message.from_user.id)]["wait_deposit_status"])
        await update_status_user(message.from_user.id, wait_deposit_status)


@dp.callback_query_handler(text_contains="removeuser_")
async def remove_user_command(call: types.CallbackQuery):
    await remove_last_user_list_message(call.message.chat.id)

    user_id = int(call.data.split("_")[-1])
    have_user_with_id = find_user_with_id(user_id)

    if have_user_with_id:
        status = get_user_status(user_id)
        if status == trial_status:
            await bot.send_message(call.message.chat.id, languageFile[get_user_language(call.message.chat.id)]["cant_remove_trial_user_text"])
        else:
            is_user_removed, user_string = remove_user_with_id(user_id)
            if is_user_removed:
                await bot.send_message(call.message.chat.id, languageFile[get_user_language(call.message.chat.id)]["removed_user_text"] + f"\n " + user_string)
                await bot.send_message(user_id, text=languageFile[get_user_language(user_id)]["delete_vip_user_text"], reply_markup=get_no_vip_markup(get_user_language(user_id)))
                await bot.send_message(user_id, text=languageFile[get_user_language(user_id)]["contact_manager_text"] + "\n" + manager_url)
            else:
                await bot.send_message(call.message.chat.id, languageFile[get_user_language(call.message.chat.id)]["cant_remove_user_text"])
    else:
        await bot.send_message(call.message.chat.id, languageFile[get_user_language(call.message.chat.id)]["error_no_user"])

    await call.answer(call.data)
    await remove_last_user_manage_message(call.message.chat.id)


@dp.message_handler(commands="trial")
async def get_trial_command(message):
    userLanguage = get_user_language(message.from_user.id)
    if has_user_status(message.from_user.id, deposit_status) or message.from_user.id in managers_id:
        await send_message_to_user(message.from_user.id, languageFile[userLanguage]["cant_get_trial_error_text"])
        return
    elif had_trial_status(message.from_user.id):
        await send_message_to_user(message.from_user.id, languageFile[userLanguage]["already_had_trial_text"])
        return
    else:
        set_trial_to_user(message.from_user.id)
        markup = get_markup_with_status(message.from_user.id, get_user_status(message.from_user.id))
        await send_message_to_user(message.from_user.id, languageFile[userLanguage]["started_trial_text"], markup)


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
    user_id = message.from_user.id
    user_language = get_user_language(user_id)
    if get_user_tag(message.from_user.id) == "none":
        await set_user_tag(message.from_user.id, message.from_user.username)

    # LANGUAGE
    if message.text not in [select_language_eng, select_language_ru, select_language_hin] and user_language == "none":
        await open_language_command(message)
        return
    if message.text in [select_language_eng, select_language_ru, select_language_hin] and user_language == "none":
        set_user_language(user_id, message.text)
        user_language = get_user_language(user_id)
        markup = get_markup_with_status(user_id, get_user_status(user_id))

        await open_menu(message, markup, languageFile[user_language]["selected_language_success_text"])
        await start_command(message)
        return

    # TRIAL
    if message.text == languageFile[user_language]["get_trial_button_text"]:
        await get_trial_command(message)
        return

    # MANAGER
    if user_id in managers_id:
        if message.text == languageFile[user_language]["user_management_button"]:
            await users_list_command(message)
        elif message.text == languageFile[user_language]["search_id_request"]:
            is_user_exists, wait_status_user_id = await get_user_with_status(wait_id_status)
            if is_user_exists:
                update_manager_do(user_id, wait_status_user_id)
                await update_manager_status(user_id, search_id_manager_status)
                await open_menu(message, get_accept_reject_markup(user_language), get_manager_user_acount(user_id))
            else:
                await message.answer(languageFile[user_language]["no_id_requests_text"])
        elif message.text == languageFile[user_language]["search_deposit_request"]:
            is_user_exists, wait_deposit_status_user_id = await get_user_with_status(wait_deposit_status)
            if is_user_exists:
                update_manager_do(user_id, wait_deposit_status_user_id)
                await update_manager_status(user_id, search_deposit_manager_status)
                await open_menu(message, get_accept_reject_markup(user_language), get_manager_user_acount(user_id))
            else:
                await message.answer(languageFile[user_language]["no_deposit_requests_text"])
        else:
            is_accept_button = message.text == languageFile[user_language]["accept_button"]
            is_reject_button = message.text == languageFile[user_language]["reject_button"]
            if is_accept_button or is_reject_button:
                is_search_id_status = is_manager_status(user_id, search_id_manager_status)
                is_search_deposit_status = is_manager_status(user_id, search_deposit_manager_status)

                user_under_do = get_manager_do(user_id)
                status = none_status
                message_to_user = ""

                if is_accept_button and is_search_id_status:
                    status = id_status
                    message_to_user = languageFile[get_user_language(user_under_do)]["accept_id_message_text"]
                elif is_reject_button and is_search_id_status:
                    status = none_status
                    message_to_user = languageFile[get_user_language(user_under_do)]["reject_id_message_text"]
                elif is_accept_button and is_search_deposit_status:
                    status = deposit_status
                    message_to_user = languageFile[get_user_language(user_under_do)]["accept_deposit_message_text"]
                elif is_reject_button and is_search_deposit_status:
                    status = id_status
                    message_to_user = languageFile[get_user_language(user_under_do)]["reject_deposit_message_text"]

                await update_status_user(user_under_do, status)
                await send_message_to_user(user_under_do, message_to_user, get_markup_with_status(user_under_do, status))

                await open_menu(message, get_manager_markup(user_language), languageFile[user_language]["process_finishing_text"])
                update_manager_do(user_id, "none")
                await update_manager_status(user_id, none_manager_status)
    # USER
    else:  # answer for user
        if message.text == languageFile[user_language]["contact_manager"]:
            await message.answer(languageFile[user_language]["contact_manager_text"] + "\n" + manager_url)
        elif has_user_status(user_id, wait_id_input_status):
            # get id
            if message.text.isdigit() and len(message.text) == 8:
                await update_status_user(user_id, wait_id_status)
                await update_account_user(user_id, message.text)
                await open_menu(message, get_half_vip_markup(user_language), languageFile[user_language]["wait_id_status"])
            else:
                await message.reply(languageFile[user_language]["error_id_text"])
        elif message.text == languageFile[user_language]["vip_status_info"]:
            if has_user_status(user_id, deposit_status):
                await open_menu(message, get_vip_markup(user_language), languageFile[user_language]["you_have_vip_text"])
            else:
                await message.answer(languageFile[user_language]["for_vip_text"])
        elif message.text == languageFile[user_language]["check_id_text"]:
            if has_user_status(user_id, deposit_status):
                await open_menu(message, get_vip_markup(user_language), languageFile[user_language]["you_have_vip_text"])
            else:
                await update_status_user(user_id, wait_id_input_status)
                await open_menu(message, get_empty_markup(), languageFile[user_language]["wait_id_text"])


@dp.callback_query_handler(text="next_users")
async def next_users_callback(call: types.CallbackQuery):
    global last_user_list_message
    await remove_last_user_list_message(call.message.chat.id)
    await remove_last_user_manage_message(call.message.chat.id)

    sent_msg = await show_users_list_to_user(call.message.chat.id)
    update_last_user_list_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text="previous_users")
async def previous_users_callback(call: types.CallbackQuery):
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
    sent_msg = await bot.send_message(call.message.chat.id, text=languageFile[get_user_language(call.message.chat.id)]["select_user_id_to_ban_text"], reply_markup=keyboard)

    update_last_user_manage_message(sent_msg)
    await call.answer(call.data)


def handle_signal_msg_controller(signal, msg, pd: PriceData, open_position_price, deal_time, start_analize_time, shared_list):
    async def handle_signal_msg(signal, msg, pd: PriceData, open_position_price, deal_time, start_analize_time, shared_list):
        t1 = datetime.strptime(start_analize_time, '%Y-%m-%d %H:%M:%S')
        t2 = market_info.get_time()
        print("before_send_delay", t2 - t1)

        users_groups = await get_users_group_ids(repeat_count, send_msg_users_group_count, signal_for_user_delay)
        t2 = market_info.get_time()
        print("created_users_delay", t2 - t1)

        for i in range(0, repeat_count):
            await send_photo_text_message_to_users(users_groups[i], signal.photo_path, msg, args=["signal_min_text"])
            await asyncio.sleep(send_msg_delay)

        print([len(users_groups[i]) for i in range(repeat_count)])
        send_open_message_time = market_info.get_time()
        delay = send_open_message_time - t1

        print("after_send_delay", delay)
        debug_msg = "delay: " + str(delay) + "; analize_time: " + str(t1) + "; send_msg_time: " + str(send_open_message_time)

        try:
            await send_message_to_users(managers_id, debug_msg)
        except Exception as e:
            print(e)

        close_signal_message, is_profit, open_price, close_price = await signal_maker.close_position(open_position_price, signal, pd, bars_count=deal_time)
        shared_list[is_profit] += 1
        img_path = "./img/profit.jpg" if is_profit else "./img/loss.jpg"

        for i in range(0, repeat_count):
            await send_photo_text_message_to_users(users_groups[i], img_path, close_signal_message, args=["signal_deal_text", "signal_min_text"])
            await asyncio.sleep(send_msg_delay)

        while True:
            send_close_message_time = market_info.get_time()
            columns = ["currency", "interval", "open_time", "close_time", "signal_type", "open_price", "close_price", "is_profit"]
            data = [[pd.symbol, pd.interval, send_open_message_time, send_close_message_time, signal.type, open_price, close_price, is_profit]]
            try:
                if not os.path.exists(signals_stats_path):
                    df = DataFrame(data=[], columns=columns)
                    df.to_csv(signals_stats_path)
                df = read_csv(signals_stats_path, index_col=[0])
                df_new = DataFrame(data=data, columns=columns)
                df = concat([df, df_new], axis=0, ignore_index=True)
                df.to_csv(signals_stats_path)
                break
            except Exception as e:
                await asyncio.sleep(10)
                print(f"ERROR Can`t write signal result to {signals_stats_path}", e)

    asyncio.run(handle_signal_msg(signal, msg, pd, open_position_price, deal_time, start_analize_time, shared_list))


async def print_stats(df, stats_name):
    profit_count = len(df[df["is_profit"] == True])
    lose_count = len(df[df["is_profit"] == False])
    text = f"Total {stats_name} statistics:\n\tprofits: {profit_count};\n\tloses: {lose_count};\n"
    await send_message_to_users(managers_id, text)


async def try_send_stats():
    global last_check_time
    try:
        time_now = market_info.get_time()
        df = read_csv(signals_stats_path)
        df["close_time"] = to_datetime(df["close_time"])
        df["close_time_year"] = df["close_time"].apply(lambda row: row.year)
        df["close_time_week"] = df["close_time"].apply(lambda row: row.isocalendar()[1])
        df["close_time_date"] = df["close_time"].apply(lambda row: row.date())
        df["close_time_hour"] = df["close_time"].apply(lambda row: row.hour)

        if time_now.day != last_check_time.day and time_now.hour != last_check_time.hour:
            print("send hour stats")
            hour_df = df[(df["close_time_date"] == last_check_time.date()) & (df["close_time_hour"] == last_check_time.hour)]
            if len(hour_df) > 0:
                await print_stats(hour_df, f"day ({last_check_time.date()}) hour ({last_check_time.hour})")
        if time_now.day != last_check_time.day:
            print("send day stats")
            day_df = df[df["close_time_date"] == last_check_time.date()]
            if len(day_df) > 0:
                await print_stats(day_df, f"day ({last_check_time.date()})")
        if time_now.isocalendar()[1] != last_check_time.isocalendar()[1]:
            print("send week stats", last_check_time.isocalendar()[1])
            week_df = df[(df["close_time_week"] == last_check_time.isocalendar()[1]) & (df["close_time_year"] == last_check_time.year)]
            if len(week_df) > 0:
                start_week_day = last_check_time.date() - timedelta(days=6)
                await print_stats(week_df, f"week ({start_week_day} to {last_check_time.date()})")

        last_check_time = time_now
    except Exception as e:
        print("Error while sending stats", e)


async def check_trial_users():
    users_ids = get_users_with_status(trial_status)
    for user_id in users_ids:
        userLanguage = get_user_language(user_id)
        if market_info.is_trial_ended(get_user_trial_end_date(user_id)):
            remove_trial_from_user(user_id)

            markup = get_markup_with_status(user_id, get_user_status(user_id))
            await send_message_to_user(user_id, languageFile[userLanguage]["ended_trial_text"], markup)
            await send_message_to_user(user_id, languageFile[userLanguage]["for_vip_text"])


def signals_message_sender_controller(prices_data, intervals, unit_pd, prices_data_all, shared_list):
    async def signals_message_sender_function(main_prices_data, intervals, unit_pd, prices_data_all, shared_list):
        price_parser.create_parce_currencies_with_intervals_callbacks(prices_data_all)
        last_send_message_check = time.time()
        for pd in prices_data_all:
            pd.reset_chart_data()
        signal_maker.reset_signals_files(main_prices_data)

        need_to_reset_seis = False
        reset_seis_wait_time = 600

        while True:
            t1 = time.perf_counter()
            try:
                await check_trial_users()
            except Exception as e:
                print("check_trial_users_ERROR", e)
            t2 = time.perf_counter()
            print("new delay", t2-t1)
            await try_send_stats()
            need_to_reset_seis = last_send_message_check + reset_seis_wait_time < time.time()
            if need_to_reset_seis:
                price_parser.create_parce_currencies_with_intervals_callbacks(prices_data_all)
                last_send_message_check = time.time()
                signal_maker.reset_signals_files(main_prices_data)
                continue

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
                print("4Error", e)
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

            time_now = market_info.get_time()
            pd = PriceData(df.symbol[0], df.exchange[0], interval_convertor.str_to_interval(df.interval[0]))
            path = f"sended_signals/time{time_now.hour}_{time_now.minute}_{pd.symbol}_{interval_convertor.interval_to_string(pd.interval).replace('.', '')}"
            df.to_csv(path)

            multiprocessing.Process(target=handle_signal_msg_controller,
                                    args=(signal, df.msg[0], pd, df.open_price[0], int(df.deal_time[0]),
                                          df.start_analize_time[0], shared_list), daemon=True).start()

            await asyncio.sleep(signal_search_delay)

            signal_maker.reset_signals_files(main_prices_data)

    asyncio.run(signals_message_sender_function(prices_data, intervals, unit_pd, prices_data_all, shared_list))


if __name__ == '__main__':
    from aiogram import executor

    multiprocessing.freeze_support()

    manager = multiprocessing.Manager()
    shared_list = manager.list()
    shared_list.append(0)
    shared_list.append(0)

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

    for currency in currencies:
        for interval in intervals:
            prices_data.append(PriceData(currency[0], currency[1], interval))

    ind = -1
    for currency_index in range(len(currencies)):
        for main_interval_index in range(len(main_intervals)):
            main_pd = PriceData(currencies[currency_index][0], currencies[currency_index][1], main_intervals[main_interval_index])
            main_pds.append(main_pd)
            parent_pds.append([])
            ind += 1
            for p_i in parent_intervals[main_interval_index]:
                parent_pds[ind].append(PriceData(currencies[currency_index][0], currencies[currency_index][1], p_i))

    for pd in prices_data:
        pd.remove_chart_data()

    unit_pd = main_pds[0]
    multiprocessing.Process(target=signals_message_sender_controller, args=(main_pds, main_intervals, unit_pd, prices_data, shared_list, )).start()

    analize_pairs = []
    for i in range(len(main_pds)):
        i_main_pd = main_pds[i]
        i_parent_pds = parent_pds[i]
        analize_pair = (i_main_pd, i_parent_pds, unit_pd)
        analize_pairs.append(analize_pair)
    multiprocessing.Process(target=signal_maker.analize_currency_data_controller, args=(analize_pairs, )).start()

    executor.start_polling(dp, skip_updates=True)
