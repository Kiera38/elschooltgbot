"""Middleware для получения оценок обработчиками."""
from typing import Callable, Dict, Any, Awaitable, cast

from aiogram import BaseMiddleware, types
from aiogram.fsm.context import FSMContext
from aiogram.types import TelegramObject, Message, CallbackQuery

from tgbot.services.repository import Repo, NoDataException
from tgbot.states.user import Change


class GradesMiddleware(BaseMiddleware):
    """Получает оценки перед обработкой события."""
    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]) -> Any:
        user: types.User = data['event_from_user']
        repo: Repo = data['repo']
        bot_user = repo.get_user(user.id)
        if isinstance(event, CallbackQuery):
            message = event.message
        else:
            message = cast(Message, event)
        if bot_user.has_cached_grades:
            await message.answer('есть сохранённые оценки, показываю их')
        else:
            await message.answer('нет сохранённых оценок, сейчас получу новые, придётся подождать')
        try:
            grades, time = await repo.get_grades(bot_user)
        except NoDataException:
            state: FSMContext = data['state']
            await state.set_state(Change.LOGIN)
            await message.answer('Кажется, что elschool обновил некоторые данные о тебе. '
                                 'Чтобы я смог продолжить получать оценки, я должен обновить эти данные.'
                                 'Для этого понадобится ввести логин и пароль. Сначала логин.')
            return
        if time:
            await message.answer(f'оценки получены за {time:.3f} с')
        if isinstance(bot_user.quarter, str):
            if bot_user.quarter not in grades:
                await message.answer('такой четверти не существует, попробуй изменить четверть')
                return
            data['grades'] = grades[bot_user.quarter]
        else:
            if bot_user.quarter-1 > len(list(grades)):
                await message.answer('такой четверти не существует, попробуй изменить четверть')
                return
            data['grades'] = list(grades.values())[bot_user.quarter-1]
            bot_user.quarter = list(grades.keys())[bot_user.quarter-1]
        return await handler(event, data)
