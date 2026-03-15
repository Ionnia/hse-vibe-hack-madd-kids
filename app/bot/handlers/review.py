from uuid import UUID

from aiogram import F, Router
from aiogram.fsm.context import FSMContext
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.bot.handlers.study import StudyState
from app.core.constants import ReviewVerdict
from app.repositories.repos import UserRepository
from app.services.study_orchestrator_service import StudyOrchestratorService

router = Router(name="review")


@router.message(StudyState.waiting_for_answer, F.text)
async def handle_answer(message: Message, session: AsyncSession, state: FSMContext) -> None:
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    data = await state.get_data()
    task_id_str = data.get("task_id")
    if not task_id_str:
        await state.clear()
        await message.answer("Сессия истекла. Используй /study чтобы начать заново.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(tg_user.id)
    if user is None:
        await message.answer("Сначала используй /start для регистрации.")
        await state.clear()
        return

    user_answer = message.text or ""
    orchestrator = StudyOrchestratorService(session)

    try:
        result, progress = await orchestrator.submit_answer(
            user_id=user.id,
            task_id=UUID(task_id_str),
            answer=user_answer,
        )
        await session.commit()
    except Exception as e:
        await message.answer(f"Ошибка при проверке ответа: {e}")
        await state.clear()
        return

    await state.clear()

    verdict_emoji = {
        ReviewVerdict.correct: "✅",
        ReviewVerdict.incorrect: "❌",
        ReviewVerdict.partial: "🔶",
    }.get(result.verdict, "❓")

    verdict_ru = {
        ReviewVerdict.correct: "Верно",
        ReviewVerdict.incorrect: "Неверно",
        ReviewVerdict.partial: "Частично верно",
    }.get(result.verdict, "—")

    feedback_text = f"\n\n💬 {result.feedback}" if result.feedback else ""
    score_pct = int(result.score * 100)

    await message.answer(
        f"{verdict_emoji} <b>{verdict_ru}</b> ({score_pct}%)"
        f"{feedback_text}\n\n"
        f"Уровень: <b>{progress.level.value}</b> | "
        f"Попыток: {progress.total_attempts} | "
        f"Правильных: {progress.correct_attempts}\n\n"
        "Используй /study чтобы получить следующий вопрос.",
        parse_mode="HTML",
    )
