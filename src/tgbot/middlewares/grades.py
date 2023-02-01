from typing import Callable, Dict, Any, Awaitable, cast

from aiogram import BaseMiddleware, types
from aiogram.types import TelegramObject, Message, CallbackQuery

from tgbot.services.repository import Repo


class GradesMiddleware(BaseMiddleware):
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
        grades, time = await repo.get_grades(bot_user)
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
