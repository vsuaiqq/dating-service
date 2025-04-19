from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Dict, Any
from pprint import pprint
from utils.i18n import get_translator

class I18nTextFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        lang_code = getattr(message.from_user, 'language_code', 'en')
        _ = get_translator(lang_code).gettext
        return message.text == _(self.key)
