from typing import Callable, Dict, Any, Awaitable

from aiogram import BaseMiddleware
from aiogram.types import TelegramObject

from tgbot.models.user import UserRole


class RoleMiddleware(BaseMiddleware):
    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def __call__(self, handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
                       event: TelegramObject, data: Dict[str, Any]):
        if not getattr(event, "from_user", None):
            data["role"] = None
        elif event.from_user.id == self.admin_id:
            data["role"] = UserRole.ADMIN
        else:
            data["role"] = UserRole.USER
        data['admin_id'] = self.admin_id
        return await handler(event, data)
