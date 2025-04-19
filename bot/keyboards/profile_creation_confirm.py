from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_profile_creation_confirm_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("save_profile_button"))],
        ],
        resize_keyboard=True
    )
