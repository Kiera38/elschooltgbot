from aiogram.dispatcher.filters.state import StatesGroup, State


class UserRegister(StatesGroup):
    REGISTER_LOGIN = State()
    REGISTER_PASSWORD = State()
    SETUP_QUARTER = State()


class ParamsGetter(StatesGroup):
    GET_LOGIN = State()
    GET_PASSWORD = State()
    GET_QUARTER = State()


class Change(StatesGroup):
    LOGIN = State()
    PASSWORD = State()
    QUARTER = State()


class AdminState(StatesGroup):
    SEND_MESSAGE = State()