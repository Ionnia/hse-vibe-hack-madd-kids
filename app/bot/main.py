import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.router import main_router
from app.core.config import settings
from app.core.logging import get_logger
from app.db.session import AsyncSessionLocal

logger = get_logger(__name__)


async def get_session_middleware():
    from aiogram import BaseMiddleware
    from typing import Any, Callable, Awaitable
    from aiogram.types import TelegramObject

    class SessionMiddleware(BaseMiddleware):
        async def __call__(
            self,
            handler: Callable[[TelegramObject, dict[str, Any]], Awaitable[Any]],
            event: TelegramObject,
            data: dict[str, Any],
        ) -> Any:
            async with AsyncSessionLocal() as session:
                data["session"] = session
                try:
                    result = await handler(event, data)
                    await session.commit()
                    return result
                except Exception:
                    await session.rollback()
                    raise
                finally:
                    await session.close()

    return SessionMiddleware()


async def main() -> None:
    if not settings.telegram_token:
        logger.error("TELEGRAM_TOKEN is not set. Cannot start bot.")
        return

    bot = Bot(token=settings.telegram_token)
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    session_middleware = await get_session_middleware()
    dp.message.middleware(session_middleware)
    dp.callback_query.middleware(session_middleware)

    dp.include_router(main_router)

    logger.info("Starting Tutor Bot...")
    await dp.start_polling(bot, drop_pending_updates=True)


if __name__ == "__main__":
    asyncio.run(main())
