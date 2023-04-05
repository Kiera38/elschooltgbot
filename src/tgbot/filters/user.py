from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import User, Message

from tgbot.services.repository import Repo


class RegisteredUserFilter(BaseFilter):
    """Фильтр для проверки регистрации пользователя."""

    async def __call__(self, message: Message, event_from_user: User, repo: Repo) -> Union[bool, Dict[str, Any]]:
        has_user = (await repo.check_has_user(event_from_user.id))
        return has_user == self.is_user

    def __init__(self, is_user: bool):
        self.is_user = is_user
