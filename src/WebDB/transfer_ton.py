from pytonlib import TonlibClient
import requests
from pathlib import Path
from wallet import wallet, wallet_addr
from tonsdk.utils import to_nano


async def get_seqno():
    url= "https://toncenter.com/api/v3/wallet"
    data = {"address": wallet_addr}
    req = requests.get(url=url, params=data)
    data = req.json()
    try:
        return data["seqno"]
    except:
        return "not init wallet"


async def send_ton(address_client: str, amount: float, payload: str = "Tate"):
    url = 'https://ton.org/global.config.json'
    config = requests.get(url).json()

    keystore_dir = './ton_keystore'
    Path(keystore_dir).mkdir(parents=True, exist_ok=True)
    client = TonlibClient(ls_index=1, config=config, keystore=keystore_dir, tonlib_timeout=15)
    await client.init()
    try:
        seqno = await get_seqno()
        if seqno:
            transfer_query = wallet.create_transfer_message(to_addr=address_client,
                                                        amount=to_nano(amount, 'ton'), seqno=seqno, payload=payload)
            transfer_message = transfer_query["message"].to_boc(False)
            await client.raw_send_message(transfer_message)
            return {"status": "success"}
        else:
            return {"status": "error", "error": seqno}
    except Exception as e:
        return {"status": "error", "error": str(e)}

