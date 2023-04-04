import datetime
import time
from dataclasses import dataclass, field
from enum import Enum

from tgbot.models.cls import Class


class UserRole(Enum):
    """Роли пользователя."""
    ADMIN = "admin" # админ
    USER = "user" # обычный пользователь


@dataclass
class User:
    """Вся информация о пользователе."""
    jwtoken: str = None # токен пользователя
    quarter: str = None # выбранная четверть (полугодие) может есть какое-нибудь другое название
    role: UserRole = UserRole.USER # роль пользователя
    url: str = None # url адрес на страницу с оценками пользователя
    cached_grades: dict = None # сохранённые оценки
    last_cache: float = 0 # время последнего сохранения оценок
    cls: Class = None
    cached_weeks: list[list] = field(default_factory=lambda: [None, None])
    last_cache_weeks: list[float] = field(default_factory=lambda: [0, 0])

    @property
    def has_cached_grades(self):
        """Можно ли использовать сохранённые оценки."""
        return self.cached_grades is not None and time.time() - self.last_cache < 3600

    def update_cache(self, grades):
        """Обновить сохранённые оценки и время последнего сохранения."""
        self.cached_grades = grades
        self.last_cache = time.time()

    def find_day(self, date: datetime.date):
        cur_time = time.time()
        for i, (week, last_cache) in enumerate(zip(self.cached_weeks, self.last_cache_weeks)):
            if not week or last_cache - cur_time > 3600:
                continue
            for day in week:
                if datetime.date.fromisoformat(day['day']) == date:
                    if i != 0:
                        week0 = self.cached_weeks[0]
                        self.cached_weeks[0] = week
                        self.cached_weeks[i] = week0
                        last_cache0 = self.last_cache_weeks[0]
                        self.last_cache_weeks[0] = last_cache
                        self.last_cache_weeks[i] = last_cache0
                    return day
        return None

    def update_days(self, week):
        self.cached_weeks[-1] = week
        self.last_cache_weeks[-1] = time.time()

