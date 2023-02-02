from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import User, Message

from tgbot.services.repository import Repo


class RegisteredUserFilter(BaseFilter):
    async def __call__(self, message: Message, event_from_user: User, repo: Repo) -> Union[bool, Dict[str, Any]]:
        return (repo.has_user(event_from_user.id) and
                repo.get_user(event_from_user.id).jwtoken is not None) == self.is_user

    def __init__(self, is_user: bool):
        self.is_user = is_user

