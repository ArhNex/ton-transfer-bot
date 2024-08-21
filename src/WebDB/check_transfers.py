import requests
import json
from tonsdk.utils import to_nano


async def check_ton_wallet(owner_wallet: str, from_wallet: str, value: float):
    url = "https://toncenter.com/api/v3/messages"
    params = {
        "source": from_wallet,
        "destination": owner_wallet,
        "limit": 1
    }
    vlnano = to_nano(value, 'ton')
    resp = requests.get(url=url, params=params)
    if resp.status_code == 200:
        transactions = resp.json()

        try:
            source = transactions.get("messages", [])[0].get("value", None)
            if int(source) == int(vlnano):
                hash = transactions.get("messages", [])[0].get("hash", None)
                return {"status": "success", "hash": hash}
            return {"status": "error", "error": "can't find transaction"}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return {"status": "error", "error": f"Ошибка при запросе данных: {resp.status_code}"}
