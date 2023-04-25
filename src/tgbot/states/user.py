"""Различные состояния пользователя"""
from aiogram.fsm.state import StatesGroup, State


class Register(StatesGroup):
    """Состояния, используемые при регистрации."""
    SHOW_PRIVACY_POLICY = State()
    LOGIN = State()
    PASSWORD = State()
    QUARTER = State()
    SAVE_DATA = State()


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
    SETTINGS = State()


class AdminState(StatesGroup):
    """Состояния админа."""
    SEND_MESSAGE = State()