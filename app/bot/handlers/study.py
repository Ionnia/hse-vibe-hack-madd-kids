from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

import random
from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository
from app.services.study_orchestrator_service import StudyOrchestratorService
from app.services.tutor_task_service import TutorTaskService

router = Router(name="study")


class StudyState(StatesGroup):
    waiting_for_answer = State()


@router.message(Command("study"))
async def cmd_study(message: Message, session: AsyncSession, state: FSMContext) -> None:
    tg_user = message.from_user
    if tg_user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    user_repo = UserRepository(session)
    user = await user_repo.get_by_telegram_id(tg_user.id)
    if user is None:
        await message.answer("Сначала используй /start для регистрации.")
        return

    orchestrator = StudyOrchestratorService(session)
    task = await orchestrator.request_next_task(user.id)

    if task is None:
        # Try to get any topic and generate a task
        material_repo = MaterialRepository(session)
        topic_repo = TopicRepository(session)
        materials = await material_repo.get_by_user_id(user.id)
        all_topics = []
        for material in materials:
            topics = await topic_repo.get_by_material_id(material.id)
            all_topics.extend(topics)
        topic = random.choice(all_topics) if all_topics else None

        if topic is None:
            await message.answer(
                "Тем пока нет. Сначала загрузи учебный материал!\n"
                "Отправь текст, фото или голосовое сообщение."
            )
            return

        tutor_service = TutorTaskService(session)
        task = await tutor_service.get_next_task(user.id, topic.id)
        await session.commit()

    await state.set_state(StudyState.waiting_for_answer)
    await state.update_data(task_id=str(task.id))

    hints_text = ""
    if task.hints:
        hints_text = "\n\n💡 <b>Подсказки:</b>\n" + "\n".join(f"• {h}" for h in task.hints)

    await message.answer(
        f"<b>Вопрос (сложность: {task.difficulty}/5):</b>\n\n"
        f"{task.question}"
        f"{hints_text}\n\n"
        "Напиши свой ответ:\n"
        "<i>/cancel — отменить и выйти</i>",
        parse_mode="HTML",
    )
