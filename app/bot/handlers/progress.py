from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos import ProgressRepository, TopicRepository, UserRepository

router = Router(name="progress")

LEVEL_EMOJI = {
    "unknown": "❓",
    "weak": "🔴",
    "learning": "🟡",
    "good": "🟢",
    "mastered": "⭐",
}


@router.message(Command("progress"))
async def cmd_progress(message: Message, session: AsyncSession) -> None:
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(tg_user.id)
    if user is None:
        await message.answer("Сначала используй /start для регистрации.")
        return

    progress_repo = ProgressRepository(session)
    topic_repo = TopicRepository(session)

    all_progress = await progress_repo.get_by_user(user.id)
    if not all_progress:
        await message.answer("Прогресса пока нет. Используй /study чтобы начать учиться!")
        return

    lines = ["<b>Твой прогресс обучения</b>\n"]
    total_correct = 0
    total_attempts = 0

    for prog in all_progress:
        topic = await topic_repo.get_by_id(prog.topic_id)
        topic_name = topic.name if topic else f"Topic {str(prog.topic_id)[:8]}"
        emoji = LEVEL_EMOJI.get(prog.level.value, "❓")
        accuracy = (
            int(prog.correct_attempts / prog.total_attempts * 100)
            if prog.total_attempts > 0
            else 0
        )
        lines.append(
            f"{emoji} <b>{topic_name}</b>\n"
            f"   Уровень: {prog.level.value} | "
            f"Попыток: {prog.total_attempts} | "
            f"Точность: {accuracy}%"
        )
        total_correct += prog.correct_attempts
        total_attempts += prog.total_attempts

    overall_accuracy = int(total_correct / total_attempts * 100) if total_attempts > 0 else 0
    lines.append(f"\n<b>Итого:</b> {total_attempts} попыток, точность {overall_accuracy}%")

    await message.answer("\n".join(lines), parse_mode="HTML")
