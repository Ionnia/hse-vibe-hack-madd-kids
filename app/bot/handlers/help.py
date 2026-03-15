from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

router = Router(name="help")

HELP_TEXT = """
<b>Команды бота</b>

/start — Запустить бота и зарегистрироваться
/help — Показать это сообщение
/topics — Список твоих учебных тем
/study — Начать занятие (получить следующее задание)
/ask — Задать вопрос по теме и получить ответ
/progress — Посмотреть прогресс обучения

<b>Загрузка материалов</b>
Отправь мне любое из следующего:
• 📷 <b>Фото</b> — извлеку текст через OCR
• 🎤 <b>Голосовое / аудио</b> — транскрибирую и изучу
• 📝 <b>Текстовое сообщение</b> — прямой ввод текста

После загрузки я извлеку темы и создам учебные задания.
"""


@router.message(Command("help"))
async def cmd_help(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="HTML")
