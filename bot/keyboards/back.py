from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_back_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("back_button"))]
        ],
        resize_keyboard=True
    )
