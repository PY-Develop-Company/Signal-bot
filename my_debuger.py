from colorama import init
from termcolor import colored

import traceback

from utils.time import now_time

init()


def debug_info(text):
    print(f"{now_time()} {text}")


def debug_temp(text):
    print(colored(f"{now_time()} {text}", "yellow"))


def debug_tv_data_feed(text):
    print(colored(f"{now_time()} {text}", "green"))


def debug_error(error: Exception, error_name="Error"):
    print(colored(f"{now_time()} {error_name}: " + str(error), "red"))
    # traceback.print_exc()
