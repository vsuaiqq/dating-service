from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_main_keyboard(is_active: bool, _):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("my_profile_button"))],
            [KeyboardButton(text=_("edit_profile_button"))],
            [KeyboardButton(text=_("disable_profile_button"))] if is_active else [KeyboardButton(text=_("enable_profile_button"))]
        ],
        resize_keyboard=True
    )