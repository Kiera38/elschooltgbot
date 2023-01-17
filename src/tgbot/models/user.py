import time
from dataclasses import dataclass
from enum import Enum
from typing import List, Dict, Union, Optional


class UserRole(Enum):
    ADMIN = "admin"
    USER = "user"


@dataclass
class User:
    login: str = None
    password: Optional[Union[str, List[int]]] = None
    quarter: int = None
    role: UserRole = UserRole.USER
    url: str = None
    save_params: bool = False
    cached_grades: Dict[str, Dict[str, Union[List[int], List[str]]]] = None
    last_cache: float = 0

    def __getstate__(self):
        if self.save_params:
            return {
                'login': self.login,
                'password': self.password,
                'quarter': self.quarter,
                'role': self.role,
                'url': self.url,
                'save_params': self.save_params
            }
        return {
            'quarter': self.quarter,
            'role': self.role,
            'url': self.url,
            'save_params': self.save_params
        }

    def __setstate__(self, state):
        for key, value in state.items():
            if hasattr(self, key):
                setattr(self, key, value)

    @property
    def has_cashed_grades(self):
        return self.cached_grades is not None and time.time() - self.last_cache < 3600

    def update_cache(self, grades):
        self.cached_grades = grades
        self.last_cache = time.time()

