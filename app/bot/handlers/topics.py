from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import CallbackQuery, InlineKeyboardButton, InlineKeyboardMarkup, Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository

router = Router(name="topics")


def _enrich_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔍 Обогатить темы", callback_data="enrich_all_topics")]
        ]
    )


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
    all_topics = []
    for material in materials:
        topics = await topic_repo.get_by_material_id(material.id)
        if not topics:
            continue
        title = material.title or f"Material {str(material.id)[:8]}"
        lines.append(f"<b>{title}</b> (status: {material.status.value})")
        for topic in topics:
            enriched_mark = " ✅" if topic.enriched_at else ""
            lines.append(f"  • {topic.name} [{topic.subject.value}]{enriched_mark}")
            total_topics += 1
            all_topics.append(topic)
        lines.append("")

    if total_topics == 0:
        await message.answer(
            "Темы ещё извлекаются. Подожди немного и попробуй снова.\n"
            "Используй /study чтобы начать занятие, когда темы будут готовы."
        )
        return

    unenriched = sum(1 for t in all_topics if t.enriched_at is None)
    lines.append(f"Всего тем: {total_topics}")
    if unenriched:
        lines.append(f"Не обогащено: {unenriched} (✅ — обогащено)")

    await message.answer(
        "\n".join(lines),
        parse_mode="HTML",
        reply_markup=_enrich_keyboard() if unenriched else None,
    )


@router.callback_query(F.data == "enrich_all_topics")
async def callback_enrich_all(callback: CallbackQuery, session: AsyncSession) -> None:
    tg_user = callback.from_user
    await callback.answer()

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(tg_user.id)
    if user is None:
        await callback.message.answer("Сначала используй /start для регистрации.")
        return

    material_repo = MaterialRepository(session)
    topic_repo = TopicRepository(session)

    materials = await material_repo.get_by_user_id(user.id)
    queued = 0
    for material in materials:
        topics = await topic_repo.get_by_material_id(material.id)
        for topic in topics:
            if topic.enriched_at is None:
                from app.tasks.topic_extraction_tasks import enrich_topic_task
                enrich_topic_task.delay(str(topic.id))
                queued += 1

    if queued == 0:
        await callback.message.answer("Все темы уже обогащены ✅")
    else:
        await callback.message.answer(
            f"🔍 Запущено обогащение для {queued} тем.\n"
            "Это займёт 1–2 минуты. Используй /topics чтобы проверить статус."
        )

    # Remove the button after clicking
    await callback.message.edit_reply_markup(reply_markup=None)
