import time
from dataclasses import dataclass
from enum import Enum
from typing import Union


class UserRole(Enum):
    """Роли пользователя."""
    ADMIN = "admin" # админ
    USER = "user" # обычный пользователь


@dataclass
class User:
    """Вся информация о пользователе. Её не так много."""
    jwtoken: str = None # токен пользователя
    quarter: Union[str, int] = None # выбранная четверть (полугодие) может есть какое-нибудь другое название
    role: UserRole = UserRole.USER # роль пользователя
    url: str = None # url адрес на страницу с оценками пользователя
    cached_grades: dict = None # сохранённые оценки
    last_cache: float = 0 # время последнего сохранения оценок

    @property
    def has_cached_grades(self):
        """Можно ли использовать сохранённые оценки."""
        return self.cached_grades is not None and time.time() - self.last_cache < 3600

    def update_cache(self, grades):
        """Обновить сохранённые оценки и время последнего сохранения."""
        self.cached_grades = grades
        self.last_cache = time.time()

