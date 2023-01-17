import time
from dataclasses import dataclass
from enum import Enum


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    jwtoken: str = None
    quarter: int = None
    role: UserRole = UserRole.USER
    url: str = None
    cached_grades: dict = None
    last_cache: float = 0

    @property
    def has_cashed_grades(self):
        return self.cached_grades is not None and time.time() - self.last_cache < 3600

    def update_cache(self, grades):
        self.cached_grades = grades
        self.last_cache = time.time()

