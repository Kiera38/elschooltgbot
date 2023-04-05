"""Middleware для возможности получения repo обработчиками."""
import os.path
import pickle
from typing import Callable, Dict, Any, Awaitable

import aiosqlite
from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tgbot.services.repository import Repo


class RepoMiddleware(BaseMiddleware):
    """Добавляет repo перед обработкой события и сохраняет изменения после события.."""
    def __init__(self, file):
        super().__init__()
        #TODO добавить роутер для обработчиков, которым не нужен repo и флаг для обработчиков, которые не изменяют repo
        self.file = file

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]):
        async with aiosqlite.connect(self.file) as db:
            data["repo"] = Repo(db)
            result = await handler(event, data)
        return result
