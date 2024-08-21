from pydantic import BaseModel


class User(BaseModel):
    id: int | None = None
    telegram_id: int | None = None
    balance: float | None = None


class UserAuthorize(BaseModel):
    telegram_id: int | None = None


class Additional(BaseModel):
    owner_wallet: str | None = None
    tax: float | None = None
    payment_time: int | None = None


class Payment(BaseModel):
    id: int | None = None
    telegram_id: int | None = None
    user_id: int | None = None
    wallet_address: str | None = None
    amount: float | None = None
    status: str | None = "In progress"
