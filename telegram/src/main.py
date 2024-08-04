import asyncio
import logging
from typing import Callable, Any, Awaitable

from aiogram import Bot, Dispatcher, BaseMiddleware
from aiogram.filters import CommandStart
from aiogram.types import Message, CallbackQuery

from routers.linode import spawn_router
from settings import BOT_API_KEY, ALLOWED_CHAT_IDS

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)


class ChatIDRestrictionMiddleware(BaseMiddleware):
    def __init__(self, allowed_chat_ids):
        super().__init__()
        self.allowed_chat_ids = allowed_chat_ids

    async def __call__(
        self,
        handler: Callable[[Message | CallbackQuery, dict[str, Any]], Awaitable[Any]],
        event: Message | CallbackQuery,
        data: dict[str, Any],
    ) -> Any:
        if isinstance(event, Message):
            chat_id = event.chat.id
        elif isinstance(event, CallbackQuery) and isinstance(event.message, Message):
            chat_id = event.message.chat.id
        else:
            return

        if str(chat_id) not in self.allowed_chat_ids:
            return

        return await handler(event, data)


dp = Dispatcher()
dp.message.middleware(ChatIDRestrictionMiddleware(ALLOWED_CHAT_IDS))
dp.callback_query.middleware(ChatIDRestrictionMiddleware(ALLOWED_CHAT_IDS))


@dp.message(CommandStart())
async def command_start_handler(message: Message) -> None:
    await message.answer(
        "Hi there! /spawn to spawn a server. /list to list running servers"
    )


async def main() -> None:
    bot = Bot(BOT_API_KEY)
    dp.include_router(spawn_router)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
