import requests as r
from dotenv import load_dotenv
import os
import json
from datetime import datetime
from random import random

load_dotenv()
KEY = os.getenv("KEY")
PUBLIC_LINK = os.getenv("PUBLIC_LINK")


def is_float(n):
    try:
        float(n)
        return True
    except:
        return False


def get_user(telegram_id):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }

    data = {"telegram_id": telegram_id}
    response = r.get(f'{PUBLIC_LINK}get_user', headers=headers, params=data)
    response_json = json.loads(response.text)
    return response_json


def get_users():
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    response = r.get(f"{PUBLIC_LINK}get_users", headers=headers)
    response_json = json.loads(response.text)
    return response_json


def post_user(telegram_id, balance=None, f="add_user"):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }

    data = {"telegram_id": telegram_id}
    if balance:
        data["balance"] = balance
    print(data)
    res = r.post(f'{PUBLIC_LINK}{f}', headers=headers, data=json.dumps(data))
    print(res.text)


def add_user(tg_id):
    user = get_user(telegram_id=tg_id)
    if user["status"] == "error":
        post_user(telegram_id=tg_id, f="add_user")


def check_balance(tg_id, balance):
    user = get_user(telegram_id=tg_id)
    if (user["status"] == "error") or (user["balance"] < balance):
        return False
    return True


def create_add_data():
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    data = {"owner_wallet": 4234564, "tax": 0.5, "payment_time": 24}
    r.post(f'{PUBLIC_LINK}create_add_data', headers=headers, data=json.dumps(data))


def get_add_data():
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    response = r.get(f'{PUBLIC_LINK}get_add_data', headers=headers)
    response_json = json.loads(response.text)
    return response_json


def change_add_data(data):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    r.post(f'{PUBLIC_LINK}change_add_data', headers=headers, data=json.dumps(data))


def add_payment(tg_id, wallet_num, amount):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    data = {
        "telegram_id": tg_id,
        "wallet_address": str(wallet_num),
        "amount": amount,
        "status": "In progress"
    }
    r.post(f'{PUBLIC_LINK}add_payment', headers=headers, data=json.dumps(data))


def delete_payment(id = None):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    data = {"id": id}
    response = r.post(f'{PUBLIC_LINK}delete_payment', headers=headers, data=json.dumps(data))


def change_payment(id, pstatus):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    data = {"id": id, "status": pstatus}
    respone = r.post(f'{PUBLIC_LINK}change_payment', headers=headers, data=json.dumps(data))


def get_payments():
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    response = r.get(f'{PUBLIC_LINK}get_payments', headers=headers)
    response_json = json.loads(response.text)
    return response_json


def get_user_payments(telegram_id=None, wallet_num=None, id=None):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }
    if telegram_id:
        data = {"telegram_id": telegram_id}
    if wallet_num:
        data = {"wallet_adress": str(wallet_num)}
    if id:
        data = {"user_id": id}

    response = r.get(f'{PUBLIC_LINK}get_user_payments', headers=headers, params=data)
    response_json = json.loads(response.text)
    return response_json


def find_dict_by(data, target_id, by):
    for item in data:
        if item[by] == target_id:
            return item
    return None


def format_dictionary(data, trash=[], main="id"):
    for i in trash:
        if i in data.keys():
            data.pop(i)
    try:
        main_value = data.pop(main)
    except:
        main_value = "---"
    if "auto_complete_time" in data.keys():
        data[
            "auto_complete_time"] = f'[{datetime.fromisoformat(data["auto_complete_time"]).strftime("%Y-%m-%d %H:%M")}]'

    if "mes_id" in data.keys():
        data.pop("mes_id")
    result = f"{main_value} " + "\n\t".join([f"{key}: {value}" for key, value in data.items()])
    return "```" + result + "```"


def sort_dict(data):
    sorted_data = sorted(data, key=lambda x: x['user_id'])
    return sorted_data


def authorize_user(telegram_id: int):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }

    data = {"telegram_id": telegram_id}
    response = r.post(f'{PUBLIC_LINK}authorize', headers=headers, data=json.dumps(data))
    response_json = response.json()
    return response_json


def check_payment(user_id: int, telegram_id: int, wallet: str, amount: float):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }

    data = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "wallet_address": wallet,
        "amount": amount
    }
    response = r.post(f'{PUBLIC_LINK}check_payment', headers=headers, data=json.dumps(data))
    response_json = json.loads(response.text)
    return response_json


def payments_to_users(user_id: int, telegram_id: int, wallet: str, amount: float):
    headers = {
        'Token': KEY,
        'Accept': "*/*",
        'Content-Type': 'application/json'
    }

    data = {
        "user_id": user_id,
        "telegram_id": telegram_id,
        "wallet_address": wallet,
        "amount": amount
    }
    response = r.post(f'{PUBLIC_LINK}send_ton_to_client', headers=headers, data=json.dumps(data))
    response_json = json.loads(response.text)
    return response_json



