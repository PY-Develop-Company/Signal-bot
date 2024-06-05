from icecream import ic


def is_valid_id_format(id_str: str) -> bool:
    is_pocket_option = len(id_str) == 8 and id_str.isdigit()
    is_iq_cent = id_str[:4].upper() == "ICUP" and id_str[4:].isdigit()
    is_binarium = len(id_str) == 7 and id_str.isdigit()

    return is_pocket_option or is_iq_cent or is_binarium


if __name__ == "__main__":
    ic(is_valid_id_format("ICUP017156227519240"))

    ic(is_valid_id_format("ICUP12345678"))

    ic(is_valid_id_format("ICU017156227519240"))
    ic(is_valid_id_format("ICUP 017156227519240"))
    ic(is_valid_id_format("ICON017156227519240"))

    ic(is_valid_id_format("ICUP0171562275192400"))
    ic(is_valid_id_format("ICUP01715622751924"))
    ic(is_valid_id_format("ICUP-01715622751924"))
    ic(is_valid_id_format("ICUP-017156227519240"))

    ic(is_valid_id_format("ICUP0171562275192.40"))
    ic(is_valid_id_format("ICUP0171562275192.4"))
