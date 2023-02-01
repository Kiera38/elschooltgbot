from aiogram.fsm.state import StatesGroup, State


class ParamsGetter(StatesGroup):
    GET_LOGIN = State()
    GET_PASSWORD = State()
    GET_QUARTER = State()


class Change(StatesGroup):
    LOGIN = State()
    PASSWORD = State()
    QUARTER = State()


class Page(StatesGroup):
    GRADES = State()
    GET_GRADES = State()
    FIX_GRADES = State()
    REGISTER = State()


class AdminState(StatesGroup):
    SEND_MESSAGE = State()