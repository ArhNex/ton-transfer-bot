from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import WebAppInfo

main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Withdraw funds"), KeyboardButton(text="Recharge balance")],
    [KeyboardButton(text="Profile")]
], resize_keyboard=True)

to_main = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="To main")]
], resize_keyboard=True)

check_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Check", callback_data="check")]
], resize_keyboard=True)


done_button = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text="Done", callback_data="done")]
])

back_button = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text = "Back")]
], resize_keyboard=True)

yes_no = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Yes"), KeyboardButton(text="No")]
], resize_keyboard=True)


add_data = ReplyKeyboardMarkup(keyboard=[
    [KeyboardButton(text="Wallet"), KeyboardButton(text= "Tax")],
    [KeyboardButton(text="Payment complete time"), KeyboardButton(text = "Complete")],
    [KeyboardButton(text = "Admin menu")]
], resize_keyboard=True)


my_payments = InlineKeyboardMarkup(inline_keyboard=[
    [InlineKeyboardButton(text = "My TON withdrawals", callback_data="my_payments")]
])


