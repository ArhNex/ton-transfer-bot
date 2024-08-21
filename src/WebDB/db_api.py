import datetime
import db_change
from fastapi import FastAPI, Request, Depends
from models import *
import db
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from check_transfers import check_ton_wallet
from transfer_ton import send_ton
import os
from dotenv import load_dotenv

tags_metadata = [
    {
        "name": "authorize",
        "description": "Принимает telegram id  если данного пользователя нет,"
                       "то создает и возвращает id пользователя из "
                       "базы данные Users"
    },
    {
        "name": "check_payment",
        "description": "As it turns out it is a withdrawal)Accepts: user's wallet. Checks "
                       "if the user's payment has been received "
                       "returns: payment received and changes the user's balance by adding to the table "
                       "payments information about the transaction"
                       "otherwise: payment don't receive"
    },
    {
        "name": "send_ton_to_client",
        "description": "Принимает: user_id, ton coin wallet"
                       ", количество"
                       "payload сообщение которое пользователь получит в кошельке. "
                       "Если всё успешно то вернёт status ok,"
                       "иначе вернёт ошибку. Изменяет баланс у пользователя и вносит "
                       "изменения в таблицу payments to users"
    },
    {
        "name": "get_wallet_for_receive",
        "description": "Возвращает кошелёк для оплаты пользователю"
    },
    {
        "name": "get_payments_to_users",
        "description": "Возвращает таблицу payments to users"
    }
]


app = FastAPI(
    title="BD",
    version="1.0",
    openapi_tags=tags_metadata
)

load_dotenv()
Token = os.getenv('TOKEN')

status_ok = {"status": "ok"}
status_error = {"status":  "error"}
status_invalid_token = {"status": "error", "error": "Invalid token"}


@app.post("/authorize", tags=["authorize"])
async def authorize(user: UserAuthorize, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        user_id = await get_user_on_id(id=None, telegram_id=user.telegram_id, session=session)
        if user_id:
            return user_id.id
        else:
            try:
                db_user = db.Users(telegram_id=user.telegram_id)
                session.add(db_user)
                await session.commit()
                user_id = await get_user_on_id(id=None, telegram_id=user.telegram_id, session=session)
                if user_id:
                    return user_id.id
            except Exception as e:
                return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


async def get_user_on_id(id=None, telegram_id=None, session=None):
    if id:
        user = select(db.Users).filter(db.Users.id == id)
        user = await session.execute(user)
        try:
            user = user.scalars().one()
            return user
        except Exception as e:
            print(e)
            return None
    elif telegram_id:
        user = select(db.Users).filter(db.Users.telegram_id == telegram_id)
        user = await session.execute(user)
        try:
            user = user.scalars().one()
            return user
        except Exception as e:
            print(e)
            return None
    else:
        return None


@app.post("/add_user")
async def add_user(user: User, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_user = db.Users(telegram_id=user.telegram_id,
                            balance=user.balance)
            session.add(db_user)
            await session.commit()
            return status_ok
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


async def get_add_(session: AsyncSession = Depends(db.get_async_session)):
    try:
        db_data = select(db.AdditionalData)
        db_data = await session.execute(db_data)
        db_data = db_data.scalars().one()
        if not db_data:
            return status_error
        return {**status_ok, **{
            "owner_wallet": db_data.owner_wallet,
            "tax": db_data.tax,
            "payment_auto_complete_time": db_data.payment_auto_complete_time
        }}
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def get_hash_by_usr_id(id=None, telegram_id=None, session=None):
    if id:
        hash = select(db.HashPrevTransaction).filter(db.HashPrevTransaction.user_id == id)
        hash = await session.execute(hash)
        try:
            hash = hash.scalars().one()
            return hash
        except Exception as e:
            print(e)
            return None
    elif telegram_id:
        hash = select(db.HashPrevTransaction).filter(db.HashPrevTransaction.user_id == id)
        hash = await session.execute(hash)
        try:
            hash = hash.scalars().one()
            return hash
        except Exception as e:
            print(e)
            return None
    else:
        return None


async def add_hash(id=None, telegram_id=None, wallet=None,hash=None, session=None):
    try:
        db_hash = db.HashPrevTransaction(user_id=id,
                           telegram_id=telegram_id,
                           user_wallet=wallet,
                           hash=hash)
        session.add(db_hash)
        await session.commit()
        return status_ok
    except Exception as e:
        return {"status": "error", "error": str(e)}


async def change_hash(id=None, telegram_id=None, wallet=None, hash=None, session=None):
    try:
        db_hash = await get_hash_by_usr_id(id=id, telegram_id=telegram_id, session=session)
        if not db_hash:
            res = await add_hash(id=id, telegram_id=telegram_id, wallet=wallet, hash=hash, session=session)
            return res
        else:
            db_hash.user_id = id
            db_hash.telegram_id = telegram_id
            db_hash.user_wallet = wallet
            db_hash.hash = hash
            await session.commit()
            return status_ok

    except Exception as e:
        return {"status": "error", "error": str(e)}


@app.post("/check_payment", tags=["check_payment"])
async def check_payment(payment: Payment, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        db_t = await get_user_on_id(id=payment.user_id, telegram_id=payment.telegram_id, session=session)
        if not db_t:
            return {"status": "error", "error": "user not found"}
        wal = await get_add_(session=session)
        if wal["status"] == "ok":
            res = await check_ton_wallet(wal["owner_wallet"], payment.wallet_address, payment.amount)
            if res["status"] == "success":
                try:
                    db_hash = await get_hash_by_usr_id(id=payment.user_id, telegram_id=payment.telegram_id, session=session)
                    if db_hash:
                        if db_hash.hash == res["hash"]:
                            return {"status": "error", "error": "cant find transaction"}
                        else:
                            answer = await change_hash(id=payment.user_id, telegram_id=payment.telegram_id,
                                        wallet=payment.wallet_address, hash=res["hash"], session=session)
                    else:
                        ans = await add_hash(id=payment.user_id, telegram_id=payment.telegram_id,
                                        wallet=payment.wallet_address, hash=res["hash"], session=session)

                    db_user = await get_user_on_id(id=payment.user_id, session=session)
                    db_user.balance = db_user.balance + payment.amount
                    await session.commit()
                except Exception as e:
                    return {"status": "error", "error": str(e)}

            return res
        else:
            return {"status": "error", "error": "can't find wallet"}
    else:
        return status_invalid_token


@app.post("/send_ton_to_client", tags=["send_ton_to_client"])
async def send_ton_api(send: Payment, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        db_user = await get_user_on_id(id=send.user_id, session=session)
        if not db_user:
            return {"status": "error", "error": "user not found"}
        try:
            needed_balance = send.amount
            if not db_user.balance >= needed_balance:
                return {"status": "error", "error": f"the user doesn't have that much money, user_id: {send.user_id}"}
            else:
                res = await send_ton(address_client=send.wallet_address, amount=needed_balance)
                if res["status"] == "success":
                    db_payments = db.Payments(user_id=send.user_id,
                                             wallet_address=send.wallet_address, amount=needed_balance,
                                             auto_complete_time=datetime.datetime.now() + datetime.timedelta(hours=2),
                                             status="Success")
                    session.add(db_payments)
                    db_user.balance -= needed_balance
                    await session.commit()
                    return status_ok
                else:
                    return res
        except Exception as e:
            return {"status": "error", "error": str(e)}

    else:
        return status_invalid_token


@app.get("/get_wallet_for_receive", tags=["get_wallet_for_receive"])
async def get_wallet_for_receive(request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        wal = await get_add_(session=session)
        if wal["status"] == "ok":
            return {"wallet": wal["owner_wallet"]}
        else:
            return {"status": "error", "error": "wallet can't find."}
    else:
        return status_invalid_token


@app.get("/get_payments_to_users", tags=["get_payments_to_users"])
async def get_payments_to_users(request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            payments = select(db.Payments)
            payments = await session.execute(payments)
            payments = payments.scalars()
            return {**status_ok,
                    **{
                        "Payments to users":[{
                        "id": payment.id,
                        "user_id": payment.user_id,
                        "user_wallet": payment.wallet_address,
                        "amount_ton": payment.amount,
                        "complete_time": payment.auto_complete_time,
                        "status": payment.status}
                        for payment in payments]
                       }}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.get("/get_user")
async def get_user(user_id: int = 0, telegram_id: int = 0,  request: Request = None, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        if not(user_id or telegram_id):
            return {"status": "error", "error": "Нет не телеграмм айди не обычного"}
        try:
            db_user = await get_user_on_id(id=user_id, telegram_id=telegram_id, session=session)

            if not db_user:
                return status_error
            
            return {**status_ok,
                **{
                "id": db_user.id,
                "telegram_id": db_user.telegram_id,
                "balance": db_user.balance,
                "inviter": db_user.inviter,
                "deposits": db_user.deposits,
                "withdrawals": db_user.withdrawals,
                "from_refs": db_user.from_refs
                }
            }        
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.post("/delete_user")
async def delete_user(user: User, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        if not(user.id or user.telegram_id):
            return {"status": "error", "error": "Нет не телеграмм айди не обычного"}
        try:
            db_user = await get_user_on_id(id=user.id, telegram_id=user.telegram_id, session=session)
            if not db_user:
                return status_error
            await session.delete(db_user)
            await session.commit()
            return status_ok
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.post("/change_user")
async def change_user(user: User, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        if not(user.id or user.telegram_id):
            return {"status": "error", "error": "Нет не телеграмм айди не обычного"}
        try:
            db_user = await get_user_on_id(id=user.id, telegram_id=user.telegram_id, session=session)
            if not db_user:
                return status_error
            if user.balance: db_user.balance = user.balance
            if user.inviter: db_user.inviter  = user.inviter
            if user.deposits: db_user.deposits  = user.deposits
            if user.from_refs: db_user.from_refs   = user.from_refs
            if user.withdrawals: db_user.withdrawals   = user.withdrawals
            await session.commit()
            return status_ok
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.get("/get_users")
async def get_users(request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            users = select(db.Users)
            users = await session.execute(users)
            users = users.scalars()
            return {**status_ok,
                    **{
                        "users":[{
                        "id": user.id,
                        "telegram_id": user.telegram_id,
                        "balance": user.balance,
                        "inviter": user.inviter,
                        "deposits": user.deposits,
                        "withdrawals": user.withdrawals,
                        "from_refs": user.from_refs}
                        for user in users]
                       }}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.post("/create_add_data")
async def create_add_data(data: Additional, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            data = db.AdditionalData(
                owner_wallet=data.owner_wallet,
                tax=data.tax,
                payment_auto_complete_time=data.payment_time,
            )
            session.add(data)
            await session.commit()
            return status_ok
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.post("/change_add_data")
async def change_add_data(data: Additional, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_data = select(db.AdditionalData)
            db_data = await session.execute(db_data)
            db_data = db_data.scalars().one()
            if not db_data:
                return status_error
            if data.owner_wallet: db_data.owner_wallet=data.owner_wallet
            if data.tax: db_data.tax=data.tax
            if data.payment_time: db_data.payment_auto_complete_time=data.payment_time
            await session.commit()
            return status_ok
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.get("/get_add_data")
async def get_add_data(request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_data = select(db.AdditionalData)
            db_data = await session.execute(db_data)
            db_data = db_data.scalars().one()
            if not db_data:
                return status_error
            return {**status_ok, **{
            "owner_wallet": db_data.owner_wallet,
            "tax": db_data.tax,
            "payment_auto_complete_time": db_data.payment_auto_complete_time
        }}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token
    

@app.post("/add_payment")
async def add_payment(payment: Payment, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_user  = await get_user_on_id(id=payment.user_id, telegram_id=payment.telegram_id, session=session)
            db_data = select(db.AdditionalData)
            db_data = await session.execute(db_data)
            db_data = db_data.scalars().one()
            if not db_data:
                return status_error
            auto_time = db_data.payment_auto_complete_time
            payment = db.Paymets(user_id=db_user.id,
                                  amount=payment.amount,
                                    wallet_address=payment.wallet_address,
                                      status=payment.status,
                          auto_complete_time= datetime.datetime.now() + datetime.timedelta(hours=auto_time))
            session.add(payment)
            await session.commit()
            return status_ok
        except Exception as e:
            return  {"status":  "error",  "error": str(e)}
    else:
        return status_invalid_token
    

@app.get("/get_user_payments")
async def get_user_payments(user_id: int = 0, telegram_id: int = 0, request: Request = None, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_user = await get_user_on_id(id=user_id, telegram_id=telegram_id, session=session)
            if not db_user:
                return status_error
            
            db_payments = select(db.Payments).filter(db.Payments.user_id == db_user.id)
            db_payments = await session.execute(db_payments)
            db_payments = db_payments.scalars()

            return {**status_ok, **{"payments":  [
            {
            "id": payment.id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "wallet_address": payment.wallet_address,
            "pstatus": payment.status,
            "auto_complete_time": payment.auto_complete_time
            } for payment in db_payments]}}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.get("/get_payments")
async def get_payments(request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_payments  = select(db.Payments)
            db_payments  = await session.execute(db_payments)
            db_payments  = db_payments.scalars()
            if not db_payments:
                db_payments = []

            return {**status_ok, **{"payments":  [
            {
            "id": payment.id,
            "user_id": payment.user_id,
            "amount": payment.amount,
            "wallet_address": payment.wallet_address,
            "pstatus": payment.status,
            "auto_complete_time": payment.auto_complete_time
            } for payment in db_payments]}}
        except Exception as e:
            return {"status": "error", "error": str(e)}
    else:
        return status_invalid_token


@app.post("/delete_payment")
async def delete_payment(payment: Payment, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_payment = select(db.Payments).filter(db.Payments.id == payment.id)
            db_payment = await session.execute(db_payment)
            db_payment = db_payment.scalars().one()
            if not db_payment:
                return status_error
            await session.delete(db_payment)
            await session.commit()
            return status_ok
        except Exception as e:
            return  {"status":  "error",  "error": str(e)}
    else:
        return status_invalid_token


@app.post("/change_payment")
async def change_payment(payment: Payment, request: Request, session: AsyncSession = Depends(db.get_async_session)):
    if request.headers['Token'] == Token:
        try:
            db_payment = select(db.Payments).filter(db.Payments.id == payment.id)
            db_payment = await session.execute(db_payment)
            db_payment = db_payment.scalars().one()
            if not db_payment:
                return status_error
            if payment.user_id:
                db_payment.user_id = payment.user_id
            if payment.amount:
                db_payment.amount = payment.amount
            if payment.wallet_address:
                db_payment.wallet_address = payment.wallet_address
            if payment.status:
                db_payment.status = payment.status

            await session.commit()
            return status_ok
        except Exception as e:
            return {"status":  "error",  "error": str(e)}
    else:
        return status_invalid_token
