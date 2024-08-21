from sqlalchemy import Integer, Text, Float, Column, DateTime, create_engine, ForeignKey
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session
import asyncio


class Base(DeclarativeBase):
    pass


engine = create_async_engine("sqlite+aiosqlite:///db.db")
async_session_maker = async_sessionmaker(engine)


class Users(Base):
    __tablename__ = 'users'
    id = Column(Integer, primary_key=True, autoincrement=True)
    telegram_id = Column(Integer, unique=True)
    balance = Column(Float, default=0.0)
    inviter = Column(Integer, ForeignKey('users.id'), nullable=True, default=None)
    deposits = Column(Integer, default=0)
    withdrawals = Column(Float, default=0.0)
    from_refs = Column(Float, default=0.0)


class HashPrevTransaction(Base):
    __tablename__ = 'hashPrevTransaction'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer)
    telegram_id = Column(Integer)
    user_wallet = Column(Text)
    hash = Column(Text)


class Payments(Base):
    __tablename__ = 'payments'
    id = Column(Integer, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey('users.id'))
    amount = Column(Float)
    wallet_address = Column(Text)
    auto_complete_time = Column(DateTime)
    status = Column(Integer)


class AdditionalData(Base):
    __tablename__ = 'additional_data'
    id = Column(Integer, primary_key=True, autoincrement=True)
    owner_wallet = Column(Text, nullable=True)
    tax = Column(Float, default=0)
    payment_auto_complete_time = Column(Integer, default=24)


def get_engine():
    return engine


async def create_db_and_tables():
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def get_async_session():
    async with async_session_maker() as session:
        yield session


async def create_add_data(wallet=None, payment_time=24, tax=0):
    async with engine.begin() as conn:
        additional_data = AdditionalData(
            owner_wallet=wallet,
            payment_auto_complete_time=payment_time,
            tax=tax
        )
        conn.add(additional_data)
        await conn.commit()


async def main():
    await create_db_and_tables()

if __name__ == '__main__':
    if 1:
        asyncio.run(main())
