from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_start_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("start_button"))]
        ],
        resize_keyboard=True
    )
