"""Различные состояния пользователя"""
from aiogram.fsm.state import StatesGroup, State


class Register(StatesGroup):
    """Состояния, используемые при регистрации."""
    LOGIN = State()
    PASSWORD = State()
    QUARTER = State()


class Change(StatesGroup):
    """Состояния, используемые при изменении данных"""
    LOGIN = State()
    PASSWORD = State()
    QUARTER = State()


class Page(StatesGroup):
    """Состояния для разных страниц бота"""
    GRADES = State()
    GET_GRADES = State()
    FIX_GRADES = State()
    REGISTER = State()


class AdminState(StatesGroup):
    """Состояния админа."""
    SEND_MESSAGE = State()