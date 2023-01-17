from aiogram.dispatcher.filters import BoundFilter
from aiogram.dispatcher.handler import ctx_data
from aiogram.types.base import TelegramObject


class RegisteredUserFilter(BoundFilter):
    key = 'is_user'

    def __init__(self, is_user: bool):
        self.is_user = is_user

    async def check(self, arg: TelegramObject) -> bool:
        data = ctx_data.get()
        from_user = getattr(arg, 'from_user')
        if from_user is not None:
            return data.get("repo").has_user(from_user.id) == self.is_user
        return False

