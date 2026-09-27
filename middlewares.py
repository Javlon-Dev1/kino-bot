from typing import Callable, Awaitable, Any
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject, Message, CallbackQuery
from aiogram.exceptions import TelegramBadRequest

from config import ADMIN_IDS
import database as db
import keyboards as kb


async def is_subscribed(bot, user_id: int) -> tuple[bool, list[dict]]:
    """Returns (fully_subscribed, list_of_missing_channels)."""
    channels = await db.get_channels()
    missing = []
    for ch in channels:
        try:
            member = await bot.get_chat_member(chat_id=ch["chat_id"], user_id=user_id)
            if member.status in ("left", "kicked"):
                missing.append(ch)
        except TelegramBadRequest:
            # bot can't see membership (e.g. not admin in that channel) — skip check for it
            continue
    return (len(missing) == 0, missing)


class SubscriptionMiddleware(BaseMiddleware):
    async def __call__(
        self,
        handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
        event: TelegramObject,
        data: dict[str, Any],
    ) -> Any:
        user = data.get("event_from_user")
        if user is None:
            return await handler(event, data)

        if user.id in ADMIN_IDS:
            return await handler(event, data)

        bot = data["bot"]
        ok, missing = await is_subscribed(bot, user.id)
        if not ok:
            text = "❗️ Botdan foydalanish uchun quyidagi kanallarga obuna bo'ling, so'ng \"Tekshirish\" tugmasini bosing:"
            if isinstance(event, Message):
                await event.answer(text, reply_markup=kb.subscribe_kb(missing))
            elif isinstance(event, CallbackQuery):
                await event.answer()
                await event.message.answer(text, reply_markup=kb.subscribe_kb(missing))
            return  # stop propagation

        return await handler(event, data)
