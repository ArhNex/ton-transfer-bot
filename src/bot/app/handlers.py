from aiogram import F, Router
from aiogram.filters import Command, CommandStart, BaseFilter
from aiogram.fsm.state import StatesGroup, State
from aiogram.fsm.context import FSMContext
from aiogram.enums import ParseMode
from aiogram.types import FSInputFile, Message, CallbackQuery
import app.keyboards as kb
from app.other_stuff import add_user, check_balance, add_payment, authorize_user, get_user_payments, get_user, \
    post_user, get_add_data, is_float, format_dictionary, check_payment, payments_to_users
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from dotenv import load_dotenv
import re
import os

router = Router()
load_dotenv()
PROVIDER_TOKEN = os.getenv("PROVIDER_TOKEN")


def extract_parameter(text):
    pattern = r'^/start(\d+)$'
    match = re.match(pattern, text)
    if match:
        return match.group(1)
    return None


class Withdrawing(StatesGroup):
    getting_num = State()
    getting_sum = State()
    accepting = State()


class Recharging(StatesGroup):
    setting_sum = State()
    getting_wallet = State()
    checking = State()


class UserIDFilter(BaseFilter):
    def __init__(self, user_ids: list):
        self.user_ids = user_ids

    async def __call__(self, message: Message) -> bool:
        for ID in self.user_ids:
            if message.from_user.id == ID:
                return True
        return False


async def send_start_screen(message: Message):
    # photo_data = FSInputFile(".venv/123.jpg")
    text = (f"Welcome, @{message.from_user.username}\n\n"
            f"*We charge a 5% commission on net profits for the maintenance.")
    await message.answer(text=text, reply_markup=kb.main)


@router.message(CommandStart())
async def cmd_start(message: Message):
    print("LOL")
    add_user(message.from_user.id)
    await send_start_screen(message)


@router.message(F.text.lower() == "profile")
async def profile(message: Message):
    info = get_user(message.from_user.id)
    print(info)
    await message.answer(f'My TON balance: {info["balance"]} TON\nDeposits: {info["deposits"]} TON', reply_markup=kb.my_payments)


@router.callback_query(F.data == "my_payments")
async def my_payments(callback: CallbackQuery):
    payments = get_user_payments(telegram_id=callback.from_user.id)
    payments = payments["payments"]
    c = 0
    all_payments = list()
    for payment in payments:
        c += 1
        payment["fake_id"] = c
        all_payments.append(payment)
    all_payments = [format_dictionary(x, ["id", "user_id"], "fake_id") for x in all_payments]
    all_payments = '\n'.join(all_payments)
    await callback.answer()
    await callback.message.answer(f"Your payments:\n{all_payments}", reply_markup=kb.main, parse_mode=ParseMode.MARKDOWN_V2)


@router.message(F.text.lower() == "referrals")
async def referrals(message: Message):
    user_id = message.from_user.id
    start_link = f"t.me/{os.getenv('BOT_NICKNAME')}?start={user_id}"
    message_text = f"\n{start_link}\n\nJoin our Telegram game and become a real Top G!🥊"

    share_button = InlineKeyboardButton(
        text="Share",
        switch_inline_query=message_text
    )

    keyboard = InlineKeyboardMarkup(inline_keyboard=[[share_button]])

    await message.answer(
        "Share your referral link to get bonuses!🎁",
        reply_markup=keyboard
    )


@router.message(F.text.lower() == 'to main')
async def to_main(message: Message, state: FSMContext):
    await state.clear()
    await send_start_screen(message)


@router.message(F.text.lower() == 'withdraw funds')
async def withdraw(message: Message, state: FSMContext):
    await state.set_state(Withdrawing.getting_num)
    await message.answer("Enter your address of wallet", reply_markup=kb.to_main)


@router.message(Withdrawing.getting_num)
async def get_num(message: Message, state: FSMContext):
    await state.update_data(wallet=message.text)
    balance = get_user(telegram_id=message.from_user.id)
    balance = balance["balance"]
    await message.answer(f"Enter the amount you wish to withdraw\nYour balance: {balance}", reply_markup=kb.to_main)
    await state.set_state(Withdrawing.getting_sum)


@router.message(Withdrawing.getting_sum)
async def get_sum(message: Message, state: FSMContext):
    additional = get_add_data()
    tax = additional["tax"]
    if (is_float(message.text)) and (check_balance(message.from_user.id, float(message.text))):
        val = float(message.text) - round(float(message.text) * tax, 2)
        await state.update_data(amount=val)
        await state.set_state(Withdrawing.accepting)
        await message.answer(
            f'You will receive {val}. Click "YES" or "NO" to complete operation.',
            reply_markup=kb.yes_no)
    else:
        await message.answer("Enter a valid amount")


@router.message(Withdrawing.accepting)
async def accept(message: Message, state: FSMContext):
    id = message.from_user.id
    data = await state.get_data()
    if message.text.lower() == "yes":

        user = get_user(telegram_id=id)
        ans = payments_to_users(user_id=user["id"], telegram_id=id, wallet=data["wallet"], amount=data["amount"])
        if ans["status"] == "ok":
            # balance = user["balance"]
            withdrawals = user["withdrawals"]
            # add_payment(message.from_user.id, data["wallet"], data["amount"])
            time = get_add_data()
            time = time["payment_auto_complete_time"]
            await message.answer(f"{data['amount']} will be credited to you within {time} hours")
            post_user(telegram_id=id, withdrawals=round(withdrawals + float(data['amount']),2), f="change_user")

    elif message.text.lower() == "no":
        await message.answer("Operation was canceled")
    await state.clear()
    await send_start_screen(message)


@router.message(F.text.lower() == 'recharge balance')
async def recharge(message: Message, state: FSMContext):
    await state.set_state(Recharging.setting_sum)
    await message.answer("Enter the amount to recharge", reply_markup=kb.to_main)


@router.message(Recharging.setting_sum)
async def set_sum(message: Message, state: FSMContext):
    await state.update_data(amount=message.text)
    if not ("," in message.text or "." in message.text):
        val = message.text
        if val.isdigit():
            if int(val) > 0:
                await state.set_state(Recharging.getting_wallet)
                a = get_add_data()
                text = f"Send to wallet number\: `{a['owner_wallet']}`\nAmount\: {message.text}\nThen send the your wallet address"
                c = text.find(".")
                text = text[:c] + "\\" + text[c:]
                await message.answer(text, reply_markup=kb.to_main, parse_mode=ParseMode.MARKDOWN_V2)
            else:
                await message.answer("Specify the correct amount")
        else:
            await message.answer("Specify the correct amount")
    else:
        await message.answer("Enter an integer TON")


@router.message(Recharging.getting_wallet)
async def get_hash(message: Message, state: FSMContext):
    await state.update_data(wallet=message.text)
    if message.text.isascii():
        await state.set_state(Recharging.checking)
        await message.answer("To complete the account recharge, click the Check button",
                             reply_markup=kb.check_button)
    else:
        await message.answer("Enter the correct wallet address", reply_markup=kb.to_main)


@router.callback_query(Recharging.checking)
async def check(callback: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    if not data["wallet"]:
        await callback.answer(f"An error occurred. Enter the ton address wallet")
        await state.set_state(Recharging.getting_wallet)

    else:
        id = callback.from_user.id
        amount = float(data["amount"])
        wallet = str(data["wallet"])
        user_id = authorize_user(telegram_id=id)
        res = check_payment(user_id=user_id, telegram_id=id, wallet=wallet, amount=amount)
        print(res)
        if res["status"] == "success":
            user = get_user(telegram_id=id)
            deposits = float(user["deposits"])
            post_user(telegram_id=id, deposits=deposits + amount, f="change_user")
            await callback.answer(f"{data['amount']} has been credited to you")
            await callback.message.delete()
            await send_start_screen(callback.message)
            await state.clear()
        else:
            await callback.answer(f"An error occurred. We didn't receive your payment click the “Check” button again,"
                                  f" if it doesn't help please contact support")
            await state.set_state(Recharging.checking)


@router.callback_query(F.data == "check")
async def check(callback: CallbackQuery, state: FSMContext):
    await callback.answer("Check was successful", show_alert=True)
