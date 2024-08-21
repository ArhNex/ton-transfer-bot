import datetime
from db import get_engine
from db import Users, Payments, AdditionalData
from sqlalchemy.orm import Session

engine = get_engine()


def add_user(telegram_id, balance=0, inviter=None, deposits_count=0):
    with Session(engine) as session:
        user = Users(telegram_id=telegram_id, balance=balance, inviter=inviter, deposits=deposits_count)
        session.add(user)
        session.commit()


def delete_user(id=None, telegram_id=None):
    with Session(engine) as session:
        if id:
            user = session.query(Users).filter(Users.id == id).first()
        elif telegram_id:
            user = session.query(Users).filter(Users.telegram_id == telegram_id).first()
        else:
            return None
        
        if not user:
            return None
        
        session.delete(user)
        session.commit()


def change_user(id=None, telegram_id=None, balance=None, inviter=None, deposits_count=None):
    with Session(engine) as session:
        if id:
            user = session.query(Users).filter(Users.id == id).first()
        elif telegram_id:
            user = session.query(Users).filter(Users.telegram_id == telegram_id).first()
        else:
            return None
        
        if balance:
            user.balance = balance

        session.commit()


def get_user(id=None, telegram_id=None):
    with Session(engine) as session:
        if id:
            user = session.query(Users).filter(Users.id  == id).first()
        elif telegram_id:
            user = session.query(Users).filter(Users.telegram_id  == telegram_id).first()
        else:
            return None
        
        if not user:
            return None
        
        return {
            "id": user.id,
            "telegram_id": user.telegram_id,
            "balance": user.balance,
        }
    

def get_users():
    with Session(engine) as session:
        users = session.query(Users).all()
        return {"users":[{
                "id": user.id,
                "telegram_id": user.telegram_id,
                "balance": user.balance}
                for user in users]}


def get_add_data():
    with Session(engine) as session:
       add_data  = session.query(AdditionalData).first()
       return  {
            "owner_wallet": add_data.owner_wallet,
            "tax": add_data.tax,
            "payment_auto_complete_time": add_data.payment_auto_complete_time
        }


def change_additional_data(owner_wallet=None, tax=None, payment_time=None):
    with Session(engine) as session:
        additional_data = session.query(AdditionalData).first()
        
        if owner_wallet:
            additional_data.owner_wallet = owner_wallet
        if tax:
            additional_data.tax = tax
        if payment_time:
            additional_data.payment_auto_complete_time = payment_time
        session.commit()


def add_payment(telegram_id=None, user_id=None, amount=None, wallet_address=None, status=None):
    with Session(engine) as session:
        auto_time = get_add_data()
        if user_id:
            pass
        if telegram_id:
            user_id = session.query(Users).filter(Users.telegram_id == telegram_id).first().id

        payment = Payments(user_id=user_id, amout=amount, wallet_address=wallet_address, status=status,
                          auto_complete_time= datetime.datetime.now() + datetime.timedelta(hours=auto_time["payment_auto_complete_time"]))
        session.add(payment)
        session.commit()


def get_user_payments(user_id=None, telegram_id=None):
    with Session(engine) as session:
       if user_id:
           user_payments  = session.query(Payments).filter(Payments.user_id == user_id).all()
       elif telegram_id:
           user = session.query(Users).filter(Users.telegram_id == telegram_id).first()
           user_payments  = session.query(Payments).filter(Payments.user_id == user.id).all()
       else:
           return None
       return {"payments":  [
            {
            "id": payment.id,
            "user_id": payment.user_id,
            "amount": payment.amout,
            "wallet_address": payment.wallet_address,
            "pstatus": payment.status,
            "auto_complete_time": payment.auto_complete_time
            } for payment in user_payments]}


def delete_payment(id=None):
    if not id:
        return None
    with Session(engine) as session:
        payment = session.query(Payments).filter(Payments.id == id).first()
        if not payment:
            return None
        
        session.delete(payment)
        session.commit()


def change_payment(id=None, user_id=None, amount=None, wallet_address=None, status=None):
    with Session(engine) as session:
        if id:
            payment = session.query(Payments).filter(Payments.id == id).first()
        else:
            return None
        
        if not payment:
            return None
        
        if user_id: payment.user_id  = user_id
        if amount: payment.amount  = amount
        if wallet_address: payment.wallet_address  = wallet_address
        if status: payment.status  = status
        session.commit()
