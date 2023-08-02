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
        if isinstance(event, Message):
            message = await event.answer('получаю оценки')
        else:
            await event.message.edit_text('получаю оценки')
            message = event.message
        data['grades_message'] = message

        try:
            time = await repo.prepare_cache_grades(user.id)
        except NoDataException:
            login, password = await repo.get_user_data(user.id)
            if login is not None and password is not None:
                await message.edit_text('мне не удалось получить оценки из elschool. '
                                        'Скорее всего, это произошло из-за того, что elschool обновил данные. '
                                        'Так-как ты сохранил логин и пароль я их обновлю.')
                jwtoken = await repo.register_user(login, password)
                await repo.update_user_token(user.id, jwtoken)
                time = await repo.prepare_cache_grades(user.id)
                await message.edit_text(f'получилось обновить данные и заново получить оценки. '
                                        f'Оценки получил за {time: .3f}')
            else:
                state: FSMContext = data['state']
                await state.set_state(Change.LOGIN)
                await message.answer('Кажется, что elschool обновил некоторые данные о тебе. '
                                     'Чтобы я смог продолжить получать оценки, я должен обновить эти данные.'
                                     'Для этого понадобится ввести логин и пароль. Сначала логин.',
                                     reply_markup=main_keyboard())
                return
        else:
            if time:
                await message.edit_text(f'оценки получил за {time: .3f}')
        return await handler(event, data)
