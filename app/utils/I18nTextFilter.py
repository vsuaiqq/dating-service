from aiogram.filters import BaseFilter
from aiogram.types import Message
from typing import Callable

class I18nTextFilter(BaseFilter):
    def __init__(self, key: str):
        self.key = key

    async def __call__(self, message: Message, _: Callable) -> bool:
        return message.text == _(self.key)