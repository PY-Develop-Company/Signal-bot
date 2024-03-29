from aiogram import types
from file_manager import *
from user_module import *


def get_language_file(path="language.json"):
    return read_file(path)


languageFile = get_language_file()


select_language_text = "Select language:"
select_language_eng = "english"
select_language_ru = "русский"
select_language_hin = "हिंदी"


def get_trial_button(language):
    return types.KeyboardButton(languageFile[language]["get_trial_button_text"])


def get_select_language_markup():
    select_language_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(select_language_eng), types.KeyboardButton(select_language_ru),
         types.KeyboardButton(select_language_hin)]
    ])
    return select_language_markup


def get_statistics_period_markup(languageCode):
    stats_markup = types.InlineKeyboardMarkup(row_width=4).add(
        types.InlineKeyboardButton(languageFile[languageCode]["period_today"], callback_data=f"show_stats_today_{1}"),
        types.InlineKeyboardButton(languageFile[languageCode]["period_yesterday"], callback_data=f"show_stats_yesterday_{1}"),
        types.InlineKeyboardButton(languageFile[languageCode]["period_7_days"], callback_data=f"show_stats_n_{7}"),
        types.InlineKeyboardButton(languageFile[languageCode]["period_1_month"], callback_data=f"show_stats_n_{30}"),
        types.InlineKeyboardButton(languageFile[languageCode]["period_1_year"], callback_data=f"show_stats_n_{365}"))
    return stats_markup


def get_empty_markup():
    markup = types.ReplyKeyboardRemove()
    return markup


def get_manager_markup(languageCode):
    manager_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["search_id_request"]), types.KeyboardButton(languageFile[languageCode]["search_deposit_request"])],
        [types.KeyboardButton(languageFile[languageCode]["user_management_button"])],
        [types.KeyboardButton(languageFile[languageCode]["stats_button"])]
    ])
    return manager_markup


def get_accept_reject_markup(languageCode):
    accept_reject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["accept_button"]), types.KeyboardButton(languageFile[languageCode]["reject_button"])]
    ])
    return accept_reject_markup


def get_half_vip_markup(languageCode):
    vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [get_trial_button(languageCode)],
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return vip_markup


def get_vip_markup(languageCode):
    vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return vip_markup


def get_no_vip_markup(languageCode):
    not_vip_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["vip_status_info"]), types.KeyboardButton(languageFile[languageCode]["check_id_text"])],
        [get_trial_button(languageCode)],
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return not_vip_markup


def get_users_markup(languageCode):
    users_markup = types.InlineKeyboardMarkup(row_width=2).add(
   types.InlineKeyboardButton(text=languageFile[languageCode]["previous_text"], callback_data="previous_users"),
        types.InlineKeyboardButton(text=languageFile[languageCode]["next_text"], callback_data="next_users"),
        types.InlineKeyboardButton(text=languageFile[languageCode]["ban_user_text"], callback_data="manage_user"))
    return users_markup


def get_markup_with_status(user_id, status):
    if user_id in manager_module.managers_id:
        return get_manager_markup(get_user_language(user_id))
    else:
        if status in [none_status]:
            return get_no_vip_markup(get_user_language(user_id))
        elif status in [deposit_status, trial_status]:
            return get_vip_markup(get_user_language(user_id))
        elif status in [wait_id_status, wait_deposit_status, id_status]:
            return get_half_vip_markup(get_user_language(user_id))
        elif status in [wait_id_input_status]:
            return get_empty_markup()
