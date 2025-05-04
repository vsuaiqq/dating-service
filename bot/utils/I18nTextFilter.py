from aiogram.filters import BaseFilter
from aiogram.types import Message
from utils.i18n import get_translator

class I18nTextFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message) -> bool:
        _ = get_translator(message.from_user)
        return message.text == _(self.key)
