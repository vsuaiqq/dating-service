from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_skip_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("skip_button"))],
            [KeyboardButton(text=_("back_button"))]
        ],
        resize_keyboard=True
    )
