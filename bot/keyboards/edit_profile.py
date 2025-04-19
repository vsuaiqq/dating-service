from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

def get_edit_profile_keyboard(_) -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[
            [KeyboardButton(text=_("edit_name_button"))],
            [KeyboardButton(text=_("edit_age_button"))],
            [KeyboardButton(text=_("edit_gender_button"))],
            [KeyboardButton(text=_("edit_interesting_gender_button"))],
            [KeyboardButton(text=_("edit_city_button"))],
            [KeyboardButton(text=_("edit_about_button"))],
            [KeyboardButton(text=_("edit_media_button"))],
            [KeyboardButton(text=_("back_button"))]
        ],
        resize_keyboard=True
    )
