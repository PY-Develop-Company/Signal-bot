from aiogram import types
from file_manager import *


def getLanguageFile(path="language.json"):
    return read_file(path)


languageFile = getLanguageFile()


select_language_text = "Select language:"
select_language_eng = "english"
select_language_ru = "руский"
select_language_hin = "हिंदी"


accept_id_message_text = """🎉Поздравляем ваш ID подтвержден🎉. 

Чтобы получить доступ к сигналам внесите депозит💵 и отправьте заявку📄 боту.
Для отправки проверки на депозит нажмите:
 /checkDeposit """
accept_deposit_message_text = """🎉Поздравляем ваш депозит внесен🎉. 
Теперь вы имеете полный доступ к сигналам"""

reject_id_message_text = """Ты ОПЯТЬ неправильно зарегистрировал аккаунт,
 и его нет в списке нашей базы трейдеров ❌ 

 попробуйте снова, нажмите /start что бы продолжит"""

reject_deposit_message_text = """Ваш депозит не внесен😵. 
Проверьте действительно ли вы его внесли и отправьте запрос на проверку снова
Для отправки проверки на депозит нажмите:
/checkDeposit """

accept_button = "ПОДТВЕРДИТЬ"
reject_button = "ОТКЛОНИТЬ"

search_id_request = "ПОДТВЕРДИТЬ ID"
search_deposit_request = "ПОДТВЕРДИТЬ ДЕПОЗИТЫ"
check_text = "Какой выдать статус пользователю"
registration_text = "Введите свой ID :"

start_img_path = "img/logo.jpg"
start_text = """Приветствую тебя трейдер 👋

В моём закрытом сообществе, я ежедневно выдаю более 1ООО торговых прогнозов 🕯 с полной аналитикой валютной пары и проходимостью от 92% 📊"""

for_vip_text = """
Для получения доступа к сигналам:


👉 зарегистрируйте аккаунт по этой ссылке - https://po8.cash/register?utm_source=affiliate&a=9SRywDUYVVMaYz&ac=oborot&code=50START🌎

👉 отправьте заявку на проверку номера аккаунта (для этого нажмите кнопку ПРОВЕРИТЬ ID и отправьте нормер аккаунта)

👉 подождите пока наш менеджер подтвердит вашу заявку

👉 внесите депозит в размере от 50$

👉 отправьте заявку на проверку депозита (для этого нажмите кнопку ПРОВЕРИТЬ ДЕПОЗИТ)

👉 подождите пока наш менеджер подтвердит вашу заявку и предоставит доступ к сигналам

"""

you_have_vip_text = "У вас уже активный VIP статус"
get_vip_text = """Поздравляю, ваша заявка принята, вам предоставлен VIP-статус 
для начала работы нажмите: /check """
reject_vip_text = "К сожалению, ваша заявка не принята"

wait_id_text = """После регистрации в твоём профиле, отображается личный номер аккаунта ⚙️

Отправь сюда сообщением номер своего аккаунта, и алгоритм в автоматическом режиме проверит правильность регистрации 🌗"""

check_deposit_text = "ПРОВЕРИТЬ ДЕПОЗИТ"
check_id_text = "ПРОВЕРИТЬ ID"
error_no_user = "❗Ошибка (пользователь с даним ID не найден)"
error_id_text = """❗Ошибка (ID должен состоять из 8 цифр)
Попробуйте отправить еще раз: 
"""

contact_manager = "ПОДДЕРЖКА"
contact_manager_text = "Данные менеджера: "

vip_status_info = "ДОСТУП К СИГНАЛАМ"
no_id_requests_text = "Все заявки на проверку ID обработаны"
no_deposit_requests_text = "Все заявки на проверки депозита обработаны"

wait_command_text = "Ожидание команды:"

user_management_button = "ПОКАЗАТЬ ПОЛЬЗОВАТЕЛЕЙ"
select_user_id_to_ban_text = "Выберите номер пользователя:                       "
users_list_title_text = "Пользователи:"
no_users_list_title_text = "Нет пользователей!"
removed_user_text = "Статус пользователя был изменен:"
cant_remove_user_text = "Статус пользователя уже изменен!"

next_text = "Далее"
previous_text = "Назад"
ban_user_text = "Убрать VIP статус"


def getSelectLanguageMarkap():
    select_language_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(select_language_eng), types.KeyboardButton(select_language_ru),
         types.KeyboardButton(select_language_hin)]
    ])
    return select_language_markup


def GetManagerMarkup():
    manager_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
        [types.KeyboardButton(search_id_request), types.KeyboardButton(search_deposit_request),
         types.KeyboardButton(user_management_button)]
    ])
    return manager_markup


accept_reject_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(accept_button), types.KeyboardButton(reject_button)]
])
vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(contact_manager)]
])
not_vip_markup = types.ReplyKeyboardMarkup(resize_keyboard=True, keyboard=[
    [types.KeyboardButton(vip_status_info), types.KeyboardButton(check_id_text), types.KeyboardButton(contact_manager)]
])

users_markup = types.InlineKeyboardMarkup(row_width=2).add(
    types.InlineKeyboardButton(text=previous_text, callback_data="previous_users"),
    types.InlineKeyboardButton(text=next_text, callback_data="next_users"),
    types.InlineKeyboardButton(text=ban_user_text, callback_data="manage_user"))
