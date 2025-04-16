from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_confirm_disable_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("confirm_disable_profile_button"))],
            [KeyboardButton(text=_("cancel_disable_profile_button"))]
        ],
        resize_keyboard=True
    )
