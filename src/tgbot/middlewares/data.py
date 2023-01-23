import os.path
import pickle
from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tgbot.services.repository import Repo


class RepoMiddleware(BaseMiddleware):

    def __init__(self, file):
        super().__init__()
        if os.path.exists(file):
            with open(file, 'rb') as f:
                self.users = pickle.load(f)
        else:
            self.users = {}
        self.file = file

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject,
                       data: Dict[str, Any]):
        data["repo"] = Repo(self.users)
        result = await handler(event, data)
        with open(self.file, 'wb') as f:
            pickle.dump(self.users, f)
        return result
