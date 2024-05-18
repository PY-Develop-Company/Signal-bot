import configparser
import json

config = configparser.ConfigParser()
config.read("config.ini")

BOT_TOKEN = config["BOT"]["Token"]
FOREX_DATA_TOKEN = config["MARKET"]["Token"]
SEARCH_ANALYZED_SIGNALS_DELAY = config["BOT"].getint("SearchAnalyzedSignalsDelay")

signal_search_delay = config["MESSAGES"].getint("SignalSearchDelay", fallback=60)
reset_seis_wait_time = config["MESSAGES"].getint("ResetSeisWaitTime", fallback=600)

users_for_print_count = config["GENERAL"].getint("UsersForPrintCount", fallback=15)

send_msg_delay = config["GENERAL"].getfloat("SendMsgDelay", fallback=0.1)
send_msg_repeat_count = config["GENERAL"].getint("SendMsgRepeatCount", fallback=50)
send_msg_group_count = config["GENERAL"].getint("SendMsgGroupCount", fallback=20)


manager_username = config["ADMIN"]["ManagerUsername"]
tester_ids = json.loads(config.get("ADMIN", "TesterIds"))
managers_ids = json.loads(config.get("ADMIN", "ManagersIds"))
manager_url = f"https://t.me/{manager_username[1:]}"
