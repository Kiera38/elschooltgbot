"""Middleware для получения оценок обработчиками."""
from typing import Callable, Dict, Any, Awaitable, cast, Union

from aiogram import BaseMiddleware, types, Bot, Dispatcher
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery

from tgbot.keyboards.user import main_keyboard
from tgbot.services.repository import Repo, NoDataException
from tgbot.states.user import Change


class GradesMiddleware(BaseMiddleware):
    """Получает оценки перед обработкой события."""
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: Union[Message, CallbackQuery],
                       data: Dict[str, Any]) -> Any:
        user: types.User = data['event_from_user']
        repo: Repo = data['repo']
        message = event if isinstance(event, Message) else event.message
        message = await cast(Bot, data['bot']).send_message(message.chat.id, 'получаю оценки')

        try:
            grades, time = await repo.get_grades(user.id)
        except NoDataException:
            state: FSMContext = data['state']
            await state.set_state(Change.LOGIN)
            await message.edit_text('Кажется, что elschool обновил некоторые данные о тебе. '
                                    'Чтобы я смог продолжить получать оценки, я должен обновить эти данные.'
                                    'Для этого понадобится ввести логин и пароль. Сначала логин.',
                                    reply_markup=main_keyboard())
            return
        data['grades'] = grades
        return await handler(event, data)
