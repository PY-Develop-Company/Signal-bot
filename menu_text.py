from aiogram import types
from file_manager import *
from user_module import *


def getLanguageFile(path="language.json"):
    return read_file(path)


languageFile = getLanguageFile()


select_language_text = "Select language:"
select_language_eng = "english"
select_language_ru = "русский"
select_language_hin = "हिंदी"


def getTrialButton(language):
    return types.KeyboardButton(languageFile[language]["get_trial_button_text"])


def getSelectLanguageMarkap():
    select_language_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(select_language_eng), types.KeyboardButton(select_language_ru),
         types.KeyboardButton(select_language_hin)]
    ])
    return select_language_markup


def getEmptyMarkup():
    markup = types.ReplyKeyboardRemove()
    return markup


def getManagerMarkup(languageCode):
    manager_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["search_id_request"]), types.KeyboardButton(languageFile[languageCode]["search_deposit_request"])],
        [types.KeyboardButton(languageFile[languageCode]["user_management_button"])]
    ])
    return manager_markup


def getAcceptRejectMarkup(languageCode):
    accept_reject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["accept_button"]), types.KeyboardButton(languageFile[languageCode]["reject_button"])]
    ])
    return accept_reject_markup


def getHalfVipMarkup(languageCode):
    vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [getTrialButton(languageCode)],
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return vip_markup


def getVipMarkup(languageCode):
    vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return vip_markup


def getNoVipMarkup(languageCode):
    not_vip_markup = types.ReplyKeyboardMarkup(row_width=2, resize_keyboard=True, keyboard=[
        [types.KeyboardButton(languageFile[languageCode]["vip_status_info"]), types.KeyboardButton(languageFile[languageCode]["check_id_text"])],
        [getTrialButton(languageCode)],
        [types.KeyboardButton(languageFile[languageCode]["contact_manager"])]
    ])
    return not_vip_markup


def getUsersMarkup(languageCode):
    users_markup = types.InlineKeyboardMarkup(row_width=2).add(
   types.InlineKeyboardButton(text=languageFile[languageCode]["previous_text"], callback_data="previous_users"),
        types.InlineKeyboardButton(text=languageFile[languageCode]["next_text"], callback_data="next_users"),
        types.InlineKeyboardButton(text=languageFile[languageCode]["ban_user_text"], callback_data="manage_user"))
    return users_markup


def getMarkupWithStatus(user_id, status):
    if user_id in manager_module.managers_id:
        return getManagerMarkup(getUserLanguage(user_id))
    else:
        if status in [none_status]:
            return getNoVipMarkup(getUserLanguage(user_id))
        elif status in [deposit_status, trial_status]:
            return getVipMarkup(getUserLanguage(user_id))
        elif status in [wait_id_status, wait_deposit_status, id_status]:
            return getHalfVipMarkup(getUserLanguage(user_id))
        elif status in [wait_id_input_status]:
            return getEmptyMarkup()
