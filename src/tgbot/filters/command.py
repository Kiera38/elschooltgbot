from typing import Any, Union, Dict

from aiogram.filters import BaseFilter
from aiogram.types import Message, User


class CommandFilter(BaseFilter):
    """Фильтр для проверки, является ли введённое сообщение командой.
    Для тех случаев когда не надо вводить команду.
    """
    def __init__(self, is_command=False):
        self.is_command = is_command
    async def __call__(self, message: Message) -> Union[bool, Dict[str, Any]]:
        return message.text in [
            "/get_grades",
            "/fix_grades",
            '/start',
            '/help',
            '/version',
            '/change_quarter',
            '/cancel',
            "/update_cache",
            '/clear_cache',
            '/new_version',
            '/reregister',
            '/unregister',
            '/register'
        ] == self.is_command
