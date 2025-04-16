from aiogram import BaseMiddleware
from aiogram.types import TelegramObject
from typing import Callable, Awaitable, Dict, Any

from utils.i18n import get_translator

class I18nMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: Dict[str, Any]
    ) -> Any:
        lang_code = getattr(event.from_user, 'language_code', 'en')
        translator = get_translator(lang_code).gettext
        data["_"] = translator
        return await handler(event, data)
