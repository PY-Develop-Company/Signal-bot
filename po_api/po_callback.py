from flask import Flask, request, jsonify

import config

from utils.bot_utils import accept_registration_po, accept_deposit_po
from po_api.auto_register_model import Account
from user import User
from menu_text import pocket_option_text

app = Flask(__name__)


@app.route('/po_callback', methods=['GET'])
async def get_po_data():
    args = None
    try:
        args = request.args.to_dict()

        is_registration = args.get('reg').lower() == 'true'
        is_deposit = args.get('ftd').lower() == 'true' or args.get('dep').lower() == 'true'
        trader_id = int(args.get('trader_id'))
        total_deposit = 0 if args.get('totaldep') == '' else float(args.get('totaldep'))

        users: list[User] = User.get_users_with_account_id(trader_id)

        event_type = "registration" if is_registration else ("deposit" if is_deposit else "unknown")
        print(f"received webhook: event type {event_type}, trader_id: {trader_id}, total_deposit: {total_deposit}")
        print(f"\t users: {[u.id for u in users]}")

        if is_registration:
            account = Account(trader_id, pocket_option_text)
            account.create_if_not_exists()
            Account.set_registration(trader_id)
            for u in users:
                await accept_registration_po(u)
                print(f"\t\t accept_registration_po: {u.id}")
        if is_deposit and total_deposit > config.minimal_deposit:
            account = Account(trader_id, pocket_option_text)
            account.create_if_not_exists()
            Account.set_deposit(trader_id)
            for u in users:
                await accept_deposit_po(u)
                print(f"\t\t accept_deposit_po: {u.id}")

        return jsonify({"result": "ok"})
    except Exception as e:
        print("PO_CALLBACK_ERROR:", e, args)
        return jsonify({"result": "error"})


@app.route('/po_callback', methods=['POST'])
def post_po_data():
    answer = "Received POST request. Send GET request to handle webhooks!"
    print(answer)
    return jsonify({"result": answer})


def flask_main():
    app.run()
    print("Successfully started Flask app to receive PocketOption webhooks!")
