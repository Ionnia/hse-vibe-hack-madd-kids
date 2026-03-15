from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import Message, ReplyKeyboardMarkup, KeyboardButton, ReplyKeyboardRemove
from sqlalchemy.ext.asyncio import AsyncSession

from app.adapters.llm.factory import get_llm
from app.repositories.repos import MaterialRepository, TopicRepository, UserRepository

router = Router(name="ask")


class AskState(StatesGroup):
    choosing_topic = State()
    waiting_for_question = State()


@router.message(Command("ask"))
async def cmd_ask(message: Message, session: AsyncSession, state: FSMContext) -> None:
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
    all_topics = []
    for material in materials:
        topics = await topic_repo.get_by_material_id(material.id)
        all_topics.extend(topics)

    if not all_topics:
        await message.answer(
            "Тем пока нет. Сначала загрузи учебный материал — текст, фото или голосовое."
        )
        return

    # Save topics in state
    topics_data = {str(t.id): {"name": t.name, "text": t.text} for t in all_topics}
    await state.update_data(topics=topics_data)
    await state.set_state(AskState.choosing_topic)

    # Build keyboard
    buttons = [[KeyboardButton(text=t.name)] for t in all_topics]
    buttons.append([KeyboardButton(text="❌ Отмена")])
    kb = ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True, one_time_keyboard=True)

    await message.answer("По какой теме задать вопрос?", reply_markup=kb)


@router.message(AskState.choosing_topic)
async def handle_topic_choice(message: Message, state: FSMContext) -> None:
    text = message.text or ""

    if text == "❌ Отмена":
        await state.clear()
        await message.answer("Отменено.", reply_markup=ReplyKeyboardRemove())
        return

    data = await state.get_data()
    topics: dict = data.get("topics", {})

    chosen = next((v for v in topics.values() if v["name"] == text), None)
    if chosen is None:
        await message.answer("Не нашёл такую тему. Выбери из списка или нажми Отмена.")
        return

    await state.update_data(chosen_topic=chosen)
    await state.set_state(AskState.waiting_for_question)

    await message.answer(
        f"Тема: <b>{chosen['name']}</b>\n\nЗадай свой вопрос:\n"
        "<i>/cancel — отменить и выйти</i>",
        parse_mode="HTML",
        reply_markup=ReplyKeyboardRemove(),
    )


@router.message(AskState.waiting_for_question, F.text)
async def handle_question(message: Message, state: FSMContext) -> None:
    question = message.text or ""

    if not question.strip():
        await message.answer("Напиши вопрос текстом.")
        return

    data = await state.get_data()
    topic = data.get("chosen_topic")
    if not topic:
        await state.clear()
        await message.answer("Сессия истекла. Начни заново с /ask.")
        return

    await message.answer("Ищу ответ... 🤔")

    llm = get_llm()
    answer = await llm.answer_question(
        topic_name=topic["name"],
        topic_text=topic["text"],
        question=question,
    )

    await message.answer(
        f"<b>Вопрос:</b> {question}\n\n"
        f"<b>Ответ:</b> {answer}\n\n"
        "Задай ещё вопрос или /ask для новой темы.",
        parse_mode="HTML",
    )

    # Stay in waiting_for_question — можно задать ещё вопрос по той же теме
