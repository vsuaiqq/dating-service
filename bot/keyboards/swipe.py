from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_swipe_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text="👎"), KeyboardButton(text="👍")],
            [KeyboardButton(text="❓")],
            [KeyboardButton(text=_("back_button"))]
        ], 
        resize_keyboard=True
    )