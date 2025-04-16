from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("my_profile_button"))],
            [KeyboardButton(text=_("disable_profile_button"))]
        ],
        resize_keyboard=True
    )