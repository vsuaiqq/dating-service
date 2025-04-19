from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_media_finish_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("finish_media_button"))],
            [KeyboardButton(text=_("back_button"))]
        ],
        resize_keyboard=True
    )
