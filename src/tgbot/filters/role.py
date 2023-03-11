import typing
from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import Message, User

from tgbot.models.user import UserRole


class RoleFilter(BaseFilter):
    """Фильтр для проверки роли."""
    async def __call__(self, message: Message, admin_id: int, event_from_user: User) -> Union[bool, Dict[str, Any]]:
        if self.roles is None:
            return True
        if event_from_user.id == admin_id:
            role = UserRole.ADMIN
        else:
            role = UserRole.USER
        if role in self.roles:
            return {'user_role': role}

    def __init__(
        self,
        role: typing.Union[None, UserRole, typing.Collection[UserRole]] = None,
    ):
        if role is None:
            self.roles = None
        elif isinstance(role, UserRole):
            self.roles = {role}
        else:
            self.roles = set(role)


class AdminFilter(BaseFilter):
    async def __call__(self, message: Message, is_admin: bool) -> Union[bool, Dict[str, Any]]:
        return is_admin == self.is_admin

    def __init__(self, is_admin: typing.Optional[bool] = None):
        self.is_admin = is_admin
