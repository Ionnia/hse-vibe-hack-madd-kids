from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository

router = Router(name="topics")


@router.message(Command("topics"))
async def cmd_topics(message: Message, session: AsyncSession) -> None:
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(tg_user.id)
    if user is None:
        await message.answer("Сначала используй /start для регистрации.")
        return

    material_repo = MaterialRepository(session)
    topic_repo = TopicRepository(session)

    materials = await material_repo.get_by_user_id(user.id)
    if not materials:
        await message.answer("У тебя пока нет учебных материалов. Отправь текст, фото или голосовое!")
        return

    lines = ["<b>Твои учебные темы</b>\n"]
    total_topics = 0
    for material in materials:
        topics = await topic_repo.get_by_material_id(material.id)
        if not topics:
            continue
        title = material.title or f"Material {str(material.id)[:8]}"
        lines.append(f"<b>{title}</b> (status: {material.status.value})")
        for topic in topics:
            lines.append(f"  • {topic.name} [{topic.subject.value}]")
            total_topics += 1
        lines.append("")

    if total_topics == 0:
        await message.answer(
            "Темы ещё извлекаются. Подожди немного и попробуй снова.\n"
            "Используй /study чтобы начать занятие, когда темы будут готовы."
        )
        return

    lines.append(f"Всего тем: {total_topics}")
    await message.answer("\n".join(lines), parse_mode="HTML")
