import asyncio

import config

from manager_module import *
from menu_text import *

from aiogram import Bot
from aiogram.utils.exceptions import BotBlocked, UserDeactivated

from my_debuger import debug_error

from user_status_type import UserStatusType

bot = Bot(token=config.BOT_TOKEN)


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


async def get_chat_id(user_id):
    try:
        chat = await bot.get_chat(user_id)
        return chat.id
    except Exception as e:
        return 0


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
        user_instance = create_user(user_id, None, None)
        t = asyncio.create_task(send_photo_text_message_to_user(user_instance, img_path, text, args=args))
        send_signal_message_tasks.append(t)

    await asyncio.gather(*send_signal_message_tasks)


def create_user(id, full_name, username):
    if id in config.managers_ids:
        user_instance = ManagerUser(id, full_name, username)
    else:
        user_instance = User(id, full_name, username)

    return user_instance


async def open_menu(message, menu_markup, answer_text="none"):
    await message.answer(answer_text, reply_markup=menu_markup)


async def accept_registration_po(user: User):
    message_to_user = languageFile[user.language]["accept_id_message_text"]

    user.set_status(UserStatusType.id_status)
    markup = get_markup_with_status(user.id, user.language, user.status)
    await send_message_to_user(user.id, message_to_user, markup)


async def reject_registration_po(user: User):
    message_to_user = languageFile[user.language]["reject_id_message_text"]

    user.set_status(UserStatusType.none_status)
    markup = get_markup_with_status(user.id, user.language, user.status)
    await send_message_to_user(user.id, message_to_user, markup)


async def accept_deposit_po(user: User):
    message_to_user = languageFile[user.language]["accept_deposit_message_text"]

    user.set_status(UserStatusType.deposit_status)
    markup = get_markup_with_status(user.id, user.language, user.status)
    await send_message_to_user(user.id, message_to_user, markup)


async def reject_deposit_po(user: User):
    message_to_user = languageFile[user.language]["reject_deposit_message_text"]

    user.set_status(UserStatusType.id_status)
    markup = get_markup_with_status(user.id, user.language, user.status)
    await send_message_to_user(user.id, message_to_user, markup)
