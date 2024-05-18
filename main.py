import logging
import multiprocessing
import asyncio

import config

from tv_signals.price_updater import FCSForexPriceUpdater
from tv_signals.price_parser import PriceData, update_prices
from tv_signals import signal_maker, price_parser
from tv_signals.signal_types import get_signal_by_type
from tv_signals.signals_table import SignalsTable
from manager_module import *
from menu_text import *
from tv_signals.analized_signals_table import AnalyzedSignalsTable

from utils import interval_convertor
from utils.time import *

from aiogram import Bot, Dispatcher
from aiogram.utils.exceptions import BotBlocked, UserDeactivated
from tv_signals.interval import Interval
from utils.interval_convertor import my_interval_to_int

from my_debuger import debug_error, debug_info, debug_temp

from user_status_type import UserStatusType

current_price_updater = FCSForexPriceUpdater(config.FOREX_DATA_TOKEN, 12000)
logging.basicConfig(level=logging.INFO)
bot = Bot(token=config.BOT_TOKEN)
dp = Dispatcher(bot)

last_user_list_message = dict()
last_user_manage_message = dict()

start_img_path = "img/logo.jpg"

last_check_time = now_time()


def get_stats_for_days(start_time, days_count):
    limit_time_secs = datetime_to_secs(start_time - timedelta(days=days_count))
    start_time_secs = datetime_to_secs(start_time)
    profits = SignalsTable.get_profit_data_in_period(start_time_secs, limit_time_secs)
    profits = [prof[0] for prof in profits]

    profit_count = profits.count(1)
    loss_count = profits.count(0)

    return profit_count, loss_count


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
    except BotBlocked:
        pass
    except UserDeactivated:
        pass
    except Exception as e:
        debug_error(e)

    return None


async def send_message_to_users(users_ids: [], text):
    send_signal_message_tasks = []
    for user_id in users_ids:
        t = asyncio.create_task(send_message_to_user(user_id, text))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def send_photo_text_message_to_user(user_instance, img_path, text=" ", markup=None, args=[]):
    if await get_chat_id(user_instance.id) == 0:
        return
    if user_instance.language == "none":
        return

    if len(args) > 0:
        input_text = args.copy()
        for i, arg in enumerate(args):
            input_text[i] = languageFile[user_instance.language][arg]
        text = text.format(*input_text)
    try:
        with open(img_path, "rb") as file:
            if markup is None:
                await bot.send_photo(user_instance.id, photo=file, caption=text)
            else:
                await bot.send_photo(user_instance.id, photo=file, caption=text, reply_markup=markup)
    except BotBlocked:
        pass
    except UserDeactivated:
        pass
    except Exception as e:
        debug_error(e)


async def send_photo_text_message_to_users(users_ids: [], img_path, text=" ", args=[]):
    send_signal_message_tasks = []
    for user_id in users_ids:
        user_instance = create_user(user_id, None, None, None)
        t = asyncio.create_task(send_photo_text_message_to_user(user_instance, img_path, text, args=args))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


async def open_menu(message, menu_markup, answer_text="none"):
    await message.answer(answer_text, reply_markup=menu_markup)


async def show_users_list_to_user(user_instance, is_next=True):
    print_str = languageFile[user_instance.language]["users_list_title_text"] + "\n"

    users_to_show = []
    if is_next:
        users_to_show = next_user_strings(config.users_for_print_count, user_instance.id)
    else:
        users_to_show = prev_user_strings(config.users_for_print_count, user_instance.id)

    for user_to_show in users_to_show:
        print_str += "\n" + user_to_show

    if len(users_to_show) == 0:
        print_str = languageFile[user_instance.language]["no_users_list_title_text"]
    return await send_message_to_user(user_instance.id, print_str, get_users_markup(user_instance.language))


def create_user(msg_user):
    if msg_user.id in config.managers_ids:
        user_instance = ManagerUser(msg_user.id, msg_user.full_name, msg_user.username)
    else:
        user_instance = User(msg_user.id, msg_user.full_name, msg_user.username)

    return user_instance


@dp.message_handler(commands="start")
async def start_command(message):
    msg_user = message.from_user
    user_id = msg_user.id

    user_instance = create_user(msg_user)

    if user_instance.language == startLanguage:
        await open_menu(message, get_select_language_markup(), "Select language:")
        return

    if user_instance.has_status(UserStatusType.wait_id_input_status):
        user_instance.set_status(UserStatusType.none_status)

    if user_instance.id in config.managers_ids:
        markup = get_manager_markup(user_instance.language)
    else:
        markup = get_markup_with_status(user_id, user_instance.language, user_instance.status)

    if user_instance.has_status(UserStatusType.deposit_status):
        msg_text = languageFile[user_instance.language]["start_vip_text"]
    elif user_instance.has_status(UserStatusType.id_status):
        msg_text = languageFile[user_instance.language]["accept_id_message_text"]
    elif user_instance.has_status(UserStatusType.wait_deposit_status):
        msg_text = languageFile[user_instance.language]["wait_deposit_status"]
    elif user_instance.has_status(UserStatusType.wait_id_status):
        msg_text = languageFile[user_instance.language]["wait_id_status"]
    else:
        msg_text = languageFile[user_instance.language]["start_text"]

    await send_photo_text_message_to_user(user_instance, start_img_path, msg_text, markup)


@dp.message_handler(commands="language")
async def open_language_command(message):
    user_instance = create_user(message.from_user)
    if user_instance.has_status(UserStatusType.wait_id_input_status):
        user_instance.set_status(UserStatusType.none_status)
    user_instance.set_language(startLanguage)
    await open_menu(message, get_select_language_markup(), "Select language:")


@dp.message_handler(commands="start_test")
async def start_test_command(message):
    if message.from_user.id in config.tester_ids:
        if message.from_user.id in config.tester_ids:
            msg = message.text.split(" ")[-1]
            if msg.isdigit():
                with open("users/test.txt", "w") as file:
                    file.write(str(float(msg) + datetime_to_secs(now_time())))


@dp.message_handler(commands="stop_test")
async def stop_test_command(message):
    if message.from_user.id in config.tester_ids:
        with open("users/test.txt", "w") as file:
            file.write("0")


@dp.message_handler(commands="checkDeposit")
async def check_deposit_command(message):
    user_instance = create_user(message.from_user)
    if user_instance.id in config.managers_ids:
        return

    if user_instance.has_status(UserStatusType.id_status):
        await message.answer(languageFile[user_instance.language]["wait_deposit_status"])
        user_instance.set_status(UserStatusType.wait_deposit_status)


@dp.callback_query_handler(text_contains="removeuser_")
async def remove_user_command(call: types.CallbackQuery):
    await remove_last_user_list_message(call.message.chat.id)
    user_instance = ManagerUser(call.message.chat.id, None, None)

    user_id = int(call.data.split("_")[-1])
    is_user_with_id_exists = not User.find_user_with_id(user_id) is None

    if is_user_with_id_exists:
        user_to_remove = User(user_id, None, None)
        if user_to_remove.has_status(UserStatusType.trial_status):
            await bot.send_message(user_instance.id, languageFile[user_instance.language]["cant_remove_trial_user_text"])
        else:
            is_user_removed = user_to_remove.remove()
            user_string = f"{user_to_remove.full_name} | {user_to_remove.account_number} | {user_to_remove.status}"
            if is_user_removed:
                await bot.send_message(user_instance.id, languageFile[user_instance.language][
                    "removed_user_text"] + f"\n " + user_string)
                await bot.send_message(user_to_remove.id, text=languageFile[user_to_remove.language]["delete_vip_user_text"],
                                       reply_markup=get_no_vip_markup(user_to_remove.language))
                await bot.send_message(user_to_remove.id, text=languageFile[user_to_remove.language][
                                                         "contact_manager_text"] + "\n" + config.manager_url)
            else:
                await bot.send_message(user_instance.id,
                                       languageFile[user_instance.language]["cant_remove_user_text"])
    else:
        await bot.send_message(user_instance.id, languageFile[user_instance.language]["error_no_user"])

    await call.answer(call.data)
    await remove_last_user_manage_message(user_instance.id)


@dp.message_handler(commands="trial")
async def get_trial_command(message):
    user_instance = User(message.from_user.id, message.from_user.full_name, message.from_user.username)
    if user_instance.has_status(UserStatusType.deposit_status) or user_instance.id in config.managers_ids:
        await send_message_to_user(user_instance.id, languageFile[user_instance.language]["cant_get_trial_error_text"])
        return
    elif user_instance.had_trial_status:
        await send_message_to_user(user_instance.id, languageFile[user_instance.language]["already_had_trial_text"])
        return
    else:
        user_instance.set_trial()
        markup = get_markup_with_status(user_instance.id, user_instance.language, user_instance.status)
        await send_message_to_user(user_instance.id, languageFile[user_instance.language]["started_trial_text"], markup)


@dp.message_handler(commands="users")
async def users_list_command(message):
    global last_user_list_message
    if message.from_user.id in config.managers_ids:
        await remove_last_user_list_message(message.from_user.id)
        await remove_last_user_manage_message(last_user_manage_message.get(message.chat.id))

        u = ManagerUser(message.from_user.id, message.from_user.full_name, message.from_user.username)
        sent_msg = await show_users_list_to_user(u)
        update_last_user_list_message(sent_msg)


@dp.message_handler(content_types=["text"])
async def handle_media(message: types.Message):
    user_id = message.from_user.id
    user_instance = create_user(message.from_user)

    # LANGUAGE
    if message.text not in [select_language_eng, select_language_ru,
                            select_language_hin] and not user_instance.has_language():
        await open_language_command(message)
        return
    if message.text in [select_language_eng, select_language_ru,
                        select_language_hin] and not user_instance.has_language():
        user_instance.set_language(message.text)
        markup = get_markup_with_status(user_instance.id, user_instance.language, user_instance.status)

        await open_menu(message, markup, languageFile[user_instance.language]["selected_language_success_text"])
        await start_command(message)
        return

    # TRIAL
    if message.text == languageFile[user_instance.language]["get_trial_button_text"]:
        await get_trial_command(message)
        return

    # MANAGER
    if user_instance.id in config.managers_ids:
        if message.text == languageFile[user_instance.language]["user_management_button"]:
            await users_list_command(message)
        elif message.text == languageFile[user_instance.language]["search_id_request"]:
            is_user_exists, wait_status_user_id = User.get_user_with_status(UserStatusType.wait_id_status)
            if is_user_exists:
                user_instance.set_do(wait_status_user_id)
                user_instance.set_status(ManagerStatusType.search_id_manager_status)
                await open_menu(message, get_accept_reject_markup(user_instance.language), user_instance.get_do_account_number())
            else:
                await message.answer(languageFile[user_instance.language]["no_id_requests_text"])
        elif message.text == languageFile[user_instance.language]["search_deposit_request"]:
            is_user_exists, wait_deposit_status_user_id = User.get_user_with_status(UserStatusType.wait_deposit_status)
            if is_user_exists:
                user_instance.set_do(wait_deposit_status_user_id)
                user_instance.set_status(ManagerStatusType.search_deposit_manager_status)
                await open_menu(message, get_accept_reject_markup(user_instance.language), user_instance.get_do_account_number())
            else:
                await message.answer(languageFile[user_instance.language]["no_deposit_requests_text"])
        elif message.text == languageFile[user_instance.language]["stats_button"]:
            await open_menu(message, get_statistics_period_markup(user_instance.language),
                            languageFile[user_instance.language]["selects_stats_period_text"])
        else:
            is_accept_button = message.text == languageFile[user_instance.language]["accept_button"]
            is_reject_button = message.text == languageFile[user_instance.language]["reject_button"]
            if is_accept_button or is_reject_button:
                is_search_id_status = user_instance.has_status(ManagerStatusType.search_id_manager_status)
                is_search_deposit_status = user_instance.has_status(ManagerStatusType.search_deposit_manager_status)

                status = UserStatusType.none_status
                message_to_user = ""

                user_under_do = User(user_instance.do, None, None)

                if is_accept_button and is_search_id_status:
                    status = UserStatusType.id_status
                    message_to_user = languageFile[user_under_do.language]["accept_id_message_text"]
                elif is_reject_button and is_search_id_status:
                    status = UserStatusType.none_status
                    message_to_user = languageFile[user_under_do.language]["reject_id_message_text"]
                elif is_accept_button and is_search_deposit_status:
                    status = UserStatusType.deposit_status
                    message_to_user = languageFile[user_under_do.language]["accept_deposit_message_text"]
                elif is_reject_button and is_search_deposit_status:
                    status = UserStatusType.id_status
                    message_to_user = languageFile[user_under_do.language]["reject_deposit_message_text"]

                user_under_do.set_status(status)
                markup = get_markup_with_status(user_under_do.id, user_under_do.language, user_under_do.status)
                await send_message_to_user(user_under_do.id, message_to_user, markup)

                await open_menu(message, get_manager_markup(user_instance.language),
                                languageFile[user_instance.language]["process_finishing_text"])
                user_instance.set_do("none")
                user_instance.set_status(ManagerStatusType.none_manager_status)
    # USER
    else:  # answer for user
        # TAG
        if not user_instance.has_tag():
            user_instance.set_tag(message.from_user.username)

        if message.text == languageFile[user_instance.language]["contact_manager"]:
            await message.answer(languageFile[user_instance.language]["contact_manager_text"] + "\n" + config.manager_url)
        elif user_instance.has_status(UserStatusType.wait_id_input_status):
            # get id
            if message.text.isdigit() and len(message.text) == 8:
                user_instance.set_status(UserStatusType.wait_id_status)
                user_instance.set_account_number(message.text)
                await open_menu(message, get_half_vip_markup(user_instance.language),
                                languageFile[user_instance.language]["wait_id_status"])
            else:
                await message.reply(languageFile[user_instance.language]["error_id_text"])
        elif message.text == languageFile[user_instance.language]["vip_status_info"]:
            if user_instance.has_status(UserStatusType.deposit_status):
                await open_menu(message, get_vip_markup(user_instance.language),
                                languageFile[user_instance.language]["you_have_vip_text"])
            else:
                await message.answer(languageFile[user_instance.language]["for_vip_text"])
        elif message.text == languageFile[user_instance.language]["check_id_text"]:
            if user_instance.has_status(UserStatusType.deposit_status):
                await open_menu(message, get_vip_markup(user_instance.language),
                                languageFile[user_instance.language]["you_have_vip_text"])
            else:
                user_instance.set_status(UserStatusType.wait_id_input_status)
                await open_menu(message, get_empty_markup(), languageFile[user_instance.language]["wait_id_text"])
        elif message.text == languageFile[user_instance.language]["get_signal_button_text"]:
            if not user_instance.is_signal_allowed:
                user_instance.set_allow_signal(True)
                await message.answer(languageFile[user_instance.language]["start_searching_signal_text"])
            else:
                await message.answer(languageFile[user_instance.language]["already_waiting_signal_text"])


@dp.callback_query_handler(text="next_users")
async def next_users_callback(call: types.CallbackQuery):
    global last_user_list_message
    await remove_last_user_list_message(call.message.chat.id)
    await remove_last_user_manage_message(call.message.chat.id)

    u = ManagerUser(call.message.chat.id, None, None)
    sent_msg = await show_users_list_to_user(u)
    update_last_user_list_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text="previous_users")
async def previous_users_callback(call: types.CallbackQuery):
    global last_user_list_message
    await remove_last_user_list_message(call.message.chat.id)
    await remove_last_user_manage_message(call.message.chat.id)

    u = ManagerUser(call.message.chat.id, None, None)
    sent_msg = await show_users_list_to_user(u, is_next=False)
    update_last_user_list_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text="manage_user")
async def manage_user_callback(call: types.CallbackQuery):
    global last_user_manage_message
    user_instance = ManagerUser(call.message.chat.id, None, None)

    await remove_last_user_manage_message(user_instance.id)

    users_data = get_current_users_data(user_instance.id)
    buttons = []
    for user_data in users_data:
        buttons.append(types.InlineKeyboardButton(text=user_data[0], callback_data=f"removeuser_{user_data[1]}"))

    keyboard = types.InlineKeyboardMarkup(row_width=5).add(*buttons)
    sent_msg = await bot.send_message(call.message.chat.id, text=languageFile[user_instance.language][
        "select_user_id_to_ban_text"], reply_markup=keyboard)

    update_last_user_manage_message(sent_msg)
    await call.answer(call.data)


@dp.callback_query_handler(text_contains="show_stats_")
async def manage_user_callback(call: types.CallbackQuery):
    stats_type = call.data.split("_")[-2]
    days_count = int(call.data.split("_")[-1])
    start_time = now_time()
    period_str = stats_type

    user_instance = ManagerUser(call.message.chat.id, None, None)

    if stats_type == "n":
        period_str = f"{days_count} days"
    elif stats_type == "yesterday":
        start_time -= timedelta(hours=start_time.hour, minutes=start_time.minute, seconds=start_time.second)
    elif stats_type == "today":
        days_count = timedelta(hours=start_time.hour, minutes=start_time.minute,
                               seconds=start_time.second).total_seconds() / 60 / 60 / 24

    profit_count, loss_count = get_stats_for_days(start_time, days_count)
    signals_count = profit_count + loss_count

    if signals_count == 0:
        percent = 50
        alter_percent = 50
    else:
        percent = round(profit_count / (profit_count + loss_count) * 100)
        alter_percent = 100 - percent

    await bot.send_message(call.message.chat.id,
                           text=languageFile[user_instance.language]["statistics_text"].format(
                               period_str, f"{percent}:{alter_percent}", profit_count, loss_count))
    await call.answer(call.data)


def handle_signal_msg_controller(analyzed_signal_id, signal, msg, pd: PriceData, open_position_price, deal_time,
                                 start_analyze_time):
    async def handle_signal_msg(analyzed_signal_id, signal, msg, pd: PriceData, open_position_price, deal_time,
                                start_analyze_time):
        t1 = str_to_datetime(start_analyze_time)
        user_signal_delay = (deal_time + 3) * 60

        users_groups = get_users_groups_ids(config.send_msg_repeat_count, config.send_msg_group_count, user_signal_delay)

        for i in range(0, config.send_msg_repeat_count):
            await send_photo_text_message_to_users(users_groups[i], signal.photo_path, msg, args=["signal_min_text"])
            await asyncio.sleep(config.send_msg_delay)

        t2 = now_time()
        delay = t2 - t1
        debug_info("after_send_delay" + " " + str(delay))

        try:
            debug_msg = "delay: " + str(delay) + "; analize_time: " + str(t1) + "; send_msg_time: " + str(t2)
            await send_message_to_users(config.managers_ids, debug_msg)
        except Exception as e:
            debug_error(e)

        debug_temp(f"open signal {pd.symbol} {pd.interval}")
        close_signal_message, is_profit, open_price, close_price, open_price_date, close_price_date = await signal_maker.close_position(
            open_position_price, signal, pd, deal_time, current_price_updater)
        img_path = "./img/profit.jpg" if is_profit else "./img/loss.jpg"

        for i in range(0, config.send_msg_repeat_count):
            await send_photo_text_message_to_users(users_groups[i], img_path, close_signal_message,
                                                   args=["signal_deal_text", "signal_min_text"])
            await asyncio.sleep(config.send_msg_delay)

        for group in users_groups:
            for user in group:
                u = User(user, None, None)
                u.set_allow_signal(False)

        debug_temp(f"close signal {pd.symbol} {pd.interval}")
        send_close_msg_time = now_time()
        SignalsTable.add_sended_signal(analyzed_signal_id, t2, send_close_msg_time, open_price, close_price, is_profit, open_price_date, close_price_date)

    asyncio.run(handle_signal_msg(analyzed_signal_id, signal, msg, pd, open_position_price, deal_time, start_analyze_time))


async def check_trial_users():
    users_ids = User.get_users_ids_with_status(UserStatusType.trial_status)
    # try:
    for user_id in users_ids:
        u = User(user_id, None, None)
        if market_info.is_trial_ended(u.trial_end_date):
            u.remove_trial()

            markup = get_markup_with_status(user_id, u.language, u.status)
            await send_message_to_user(user_id, languageFile[u.language]["ended_trial_text"], markup)
            if u.has_status(UserStatusType.none_status):
                await send_message_to_user(user_id, languageFile[u.language]["for_vip_text"])
            elif u.has_status(UserStatusType.id_status):
                await send_message_to_user(user_id, languageFile[u.language]["accept_id_message_text"])
            elif u.has_status(UserStatusType.deposit_status):
                await send_message_to_user(user_id, languageFile[u.language]["start_vip_text"])
            elif u.has_status(UserStatusType.wait_deposit_status):
                await send_message_to_user(user_id, languageFile[u.language]["wait_deposit_status"])
            elif u.has_status(UserStatusType.wait_id_status):
                await send_message_to_user(user_id, languageFile[u.language]["wait_id_status"])
    # except Exception as e:
    #     debug_error(e, "check_trial_users_ERROR")


def is_stop_send_signals():
    result = False
    try:
        with open("users/test.txt", "r") as file:
            cont = file.read().split(".")[0]
            if cont.isdigit():
                cont = float(cont)
                if cont > datetime_to_secs(now_time()):
                    debug_info(f"wait for signal {str(cont)} {str(datetime_to_secs(now_time()))}")
                    result = True
    except Exception as e:
        debug_error(e)
    return result


def signals_message_sender_controller():
    async def signals_message_sender_function():
        while True:
            await check_trial_users()

            await asyncio.sleep(config.SEARCH_ANALYZED_SIGNALS_DELAY)

            if is_stop_send_signals():
                continue
            if not market_info.is_market_working():
                debug_info("market not working...")
                AnalyzedSignalsTable.set_all_checked()
                continue

            debug_temp("search signals to send...")

            unchecked_signals_df = AnalyzedSignalsTable.get_unchecked_signals()
            real_signals_df = unchecked_signals_df[unchecked_signals_df["has_signal"] == True]
            if len(real_signals_df) == 0:
                continue

            df = real_signals_df.sample(n=1)
            df = df.reset_index(drop=True)

            signal = get_signal_by_type(df["signal_type"][0])
            pd = PriceData(df["symbol"][0], df["exchange"][0], interval_convertor.str_to_my_interval(df["interval"][0]))

            multiprocessing.Process(target=handle_signal_msg_controller,
                                    args=(df["id"][0], signal, df["msg"][0], pd, df["open_price"][0], int(df["deal_time"][0]),
                                          df["start_analize_time"][0]), daemon=True).start()

            debug_temp(f"wait for new signal search... ({config.signal_search_delay} s)")
            await asyncio.sleep(config.signal_search_delay)

            AnalyzedSignalsTable.set_all_checked()

    asyncio.run(signals_message_sender_function())


class IntervalGroup:
    def __init__(self, main, parent, additional=[]):
        self.additional = additional
        self.main = main
        self.parent = parent


class AnalyzePair:
    def __init__(self, interval_group: IntervalGroup, symbol: str, exchange: str):
        self.wait_minutes = my_interval_to_int(interval_group.main)

        self.main_pd = PriceData(symbol, exchange, interval_group.main)
        self.parent_pds = [PriceData(symbol, exchange, interval_group.parent[i]) for i in range(len(interval_group.parent))]
        self.additional_pds = [PriceData(symbol, exchange, interval_group.additional[i]) for i in range(len(interval_group.additional))]

    def get_all_pds(self):
        return list(set([self.main_pd, *self.parent_pds]))


def analyze_loop(analyze_pairs: [AnalyzePair], pds: [PriceData], symbols: [str], exchanges: [str], periods: [str]):
    from threading import Thread, Lock

    async def analyze_loop_child():
        print("init")
        AnalyzedSignalsTable.set_all_checked()
        lock = Lock()

        while True:
            debug_info("analyze loop...")
            if is_new_day():
                current_price_updater.reset_req_count()
            if not market_info.is_market_working():
                is_updated = update_prices(symbols, exchanges, [periods[0]], current_price_updater)
                debug_info("analyze loop end... market is sleeping")
            else:
                debug_info("update_prices...")
                is_updated = update_prices(symbols, exchanges, periods, current_price_updater)
                debug_info("updated_prices...")

                if is_updated:
                    debug_info("is_updated...")
                    tasks = []
                    for analyze_pair in analyze_pairs:
                        debug_info(f"analyze {analyze_pair.main_pd.symbol, analyze_pair.main_pd.interval}")
                        t = Thread(target=signal_maker.analyze_currency_data_controller, args=(analyze_pair, lock))
                        t.start()
                        tasks.append(t)

                    debug_info("analyze wait tasks...")
                    for t in tasks:
                        t.join()
                    debug_info("analyze loop end...")
                else:
                    debug_error(Exception(), "not updated prices")

            await asyncio.sleep(5 * 60)
    asyncio.run(analyze_loop_child())


def main():
    from aiogram import executor

    multiprocessing.freeze_support()

    intervals = [Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute, Interval.in_1_hour, Interval.in_2_hour]
    currencies = price_parser.get_currencies()

    groups = [IntervalGroup(Interval.in_5_minute, [Interval.in_15_minute, Interval.in_1_hour],
                            additional=[Interval.in_1_minute, Interval.in_5_minute, Interval.in_5_minute]),
              IntervalGroup(Interval.in_5_minute, [Interval.in_30_minute, Interval.in_2_hour],
                            additional=[Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute])]

    analyze_pairs = [AnalyzePair(groups[group_index], currency[0], currency[1]) for currency in currencies for
                     group_index in range(len(groups))]
    pds = [PriceData(currency[0], currency[1], interval) for currency in currencies for interval in intervals]

    symbols = [currency[0] for currency in currencies]
    exchanges = [currency[1] for currency in currencies]
    periods = ["1m", "5m", "15m", "30m", "1h", "2h"]
    multiprocessing.Process(target=analyze_loop, args=(analyze_pairs, pds, symbols, exchanges, periods)).start()
    multiprocessing.Process(target=signals_message_sender_controller).start()

    executor.start_polling(dp, skip_updates=True)


if __name__ == '__main__':
    intervals = [Interval.in_1_minute, Interval.in_5_minute, Interval.in_15_minute, Interval.in_30_minute, Interval.in_1_hour, Interval.in_2_hour]
    currencies = price_parser.get_currencies()
    symbols = [currency[0] for currency in currencies]
    exchanges = [currency[1] for currency in currencies]
    periods = ["1m", "5m", "15m", "30m", "1h", "2h"]
    # for period in periods:
    #     is_ok, res, url = current_price_updater.download_price_data(symbols, period, 1)
    #     with open(f"data_{period}.json", "w+") as f:
    #         f.write(url + str(res))
    main()
