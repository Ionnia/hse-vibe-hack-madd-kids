from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, ReplyKeyboardRemove

router = Router(name="cancel")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current is None:
        await message.answer("Нет активного действия.", reply_markup=ReplyKeyboardRemove())
    else:
        await message.answer(
            "Отменено. Можешь загрузить новый материал или выбрать команду.",
            reply_markup=ReplyKeyboardRemove(),
        )
