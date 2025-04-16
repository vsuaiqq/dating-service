from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_gender_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("gender_male_button"))],
            [KeyboardButton(text=_("gender_female_button"))]
        ],
        resize_keyboard=True
    )

def get_interesting_gender_keyboard(_):
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("gender_male_button"))],
            [KeyboardButton(text=_("gender_female_button"))],
            [KeyboardButton(text=_("gender_any_button"))]
        ],
        resize_keyboard=True
    )
