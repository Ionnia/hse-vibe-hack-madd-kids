from aiogram import Router
from aiogram.filters import CommandStart
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos import UserRepository

router = Router(name="start")


@router.message(CommandStart())
async def cmd_start(message: Message, session: AsyncSession) -> None:
    user_repo = UserRepository(session)
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    user = await user_repo.get_or_create(
        telegram_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )
    await session.commit()

    await message.answer(
        f"Привет, {tg_user.first_name}! 👋\n\n"
        "Я твой AI-тьютор. Отправь мне учебный материал — фото, голосовое или текст — "
        "и я извлеку темы и буду гонять тебя по карточкам и упражнениям.\n\n"
        "Отправь /help чтобы посмотреть все команды."
    )
