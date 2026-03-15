import logging

from aiogram import Bot, Router
from aiogram.filters import StateFilter
from aiogram.fsm.state import default_state
from aiogram.types import Message
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.constants import InputType
from app.repositories.repos import UserRepository
from app.services.material_ingestion_pipeline import MaterialIngestionPipeline

logger = logging.getLogger(__name__)
router = Router(name="upload")


async def _get_or_create_user(session: AsyncSession, message: Message):
    tg_user = message.from_user
    if tg_user is None:
        return None
    user_repo = UserRepository(session)
    user = await user_repo.get_or_create(
        telegram_id=tg_user.id,
        username=tg_user.username,
        full_name=tg_user.full_name,
    )
    return user


@router.message(lambda m: m.photo is not None)
async def handle_photo(message: Message, session: AsyncSession, bot: Bot) -> None:
    user = await _get_or_create_user(session, message)
    if user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    await message.answer("Фото получено, обрабатываю... ⏳")

    photo = message.photo[-1]  # largest
    file_info = await bot.get_file(photo.file_id)
    file_data = await bot.download_file(file_info.file_path)
    data = file_data.read() if file_data else b""

    pipeline = MaterialIngestionPipeline(session)
    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.image,
        data=data,
        filename=f"{photo.file_id}.jpg",
        telegram_file_id=photo.file_id,
        title="Photo upload",
    )
    await session.commit()

    # Trigger background topic extraction
    try:
        from app.tasks.topic_extraction_tasks import run_topic_pipeline
        run_topic_pipeline.delay(str(material.id))
    except Exception as e:
        logger.warning("Could not enqueue topic pipeline: %s", e)

    await message.answer(
        f"Фото сохранено! ID материала: <code>{material.id}</code>\n"
        "Темы извлекаются в фоне. Используй /topics чтобы проверить готовность.",
        parse_mode="HTML",
    )


@router.message(lambda m: m.voice is not None or m.audio is not None)
async def handle_audio(message: Message, session: AsyncSession, bot: Bot) -> None:
    user = await _get_or_create_user(session, message)
    if user is None:
        await message.answer("Не удалось определить пользователя.")
        return

    await message.answer("Аудио получено, транскрибирую... ⏳")

    file_obj = message.voice or message.audio
    file_id = file_obj.file_id
    file_info = await bot.get_file(file_id)
    file_data = await bot.download_file(file_info.file_path)
    data = file_data.read() if file_data else b""

    pipeline = MaterialIngestionPipeline(session)
    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.audio,
        data=data,
        filename=f"{file_id}.ogg",
        telegram_file_id=file_id,
        title="Audio upload",
    )
    await session.commit()

    try:
        from app.tasks.topic_extraction_tasks import run_topic_pipeline
        run_topic_pipeline.delay(str(material.id))
    except Exception as e:
        logger.warning("Could not enqueue topic pipeline: %s", e)

    await message.answer(
        f"Аудио сохранено! ID материала: <code>{material.id}</code>\n"
        "Темы извлекаются в фоне. Используй /topics чтобы проверить готовность.",
        parse_mode="HTML",
    )


@router.message(StateFilter(default_state), lambda m: m.text is not None and not m.text.startswith("/"))
async def handle_text(message: Message, session: AsyncSession) -> None:
    user = await _get_or_create_user(session, message)
    if user is None:
        await message.answer("Could not identify user.")
        return

    text = message.text or ""
    if len(text) < 20:
        await message.answer("Текст слишком короткий. Отправь больше контента для изучения.")
        return

    await message.answer("Обрабатываю текст... ⏳")

    pipeline = MaterialIngestionPipeline(session)
    material = await pipeline.ingest(
        user_id=user.id,
        input_type=InputType.text,
        raw_text=text,
        title=text[:50] + ("..." if len(text) > 50 else ""),
    )
    await session.commit()

    try:
        from app.tasks.topic_extraction_tasks import run_topic_pipeline
        run_topic_pipeline.delay(str(material.id))
    except Exception as e:
        logger.warning("Could not enqueue topic pipeline: %s", e)

    await message.answer(
        f"Текст сохранён! ID материала: <code>{material.id}</code>\n"
        "Темы извлекаются в фоне. Используй /topics чтобы проверить готовность.",
        parse_mode="HTML",
    )
