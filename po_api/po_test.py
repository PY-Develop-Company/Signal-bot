import requests


def send_po_data_test_register():
    url = f"https://randomly-funny-lark.ngrok-free.app/po_callback?reg={True}&ftd={False}&dep={False}&trader_id={'12345679'}&sumdep={100}&totaldep={1000}&reg={1}&a={'FDygxrm7PXf7lB'}"
    requests.get(url)


def send_po_data_test_deposit1():
    url = f"https://randomly-funny-lark.ngrok-free.app/po_callback?reg={False}&ftd={True}&dep={False}&trader_id={'12345678'}&sumdep={100}&totaldep={1000}&reg={1}&a={'FDygxrm7PXf7lB'}"
    requests.get(url)


def send_po_data_test_deposit2():
    url = f"https://randomly-funny-lark.ngrok-free.app/po_callback?reg={False}&ftd={False}&dep={True}&trader_id={'12345678'}&sumdep={100}&totaldep={1000}&reg={1}&a={'FDygxrm7PXf7lB'}"
    requests.get(url)


if __name__ == '__main__':
    send_po_data_test_register()
