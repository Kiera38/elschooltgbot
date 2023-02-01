import logging
import traceback
from typing import cast

from aiogram import Dispatcher, Router, Bot
from aiogram.filters import ExceptionTypeFilter
from aiogram.fsm.context import FSMContext
from aiogram.types.error_event import ErrorEvent
from aiogram import html
import aiogram.utils.markdown as fmt

from tgbot import handlers
from tgbot.services.repository import NotRegisteredException, NoDataException

logger = logging.getLogger(__name__)

error_router = Router()


@error_router.errors(ExceptionTypeFilter(NotRegisteredException))
async def not_registered_handler(error: ErrorEvent, admin_id: int, bot: Bot, state: FSMContext):
    exception = cast(NotRegisteredException, error.exception)
    await error.update.message.answer(f"произошла ошибка регистрации: {error.exception}")
    if exception.login is not None and exception.password is not None:
        await error.update.message.answer(fmt.text('твой логин', html.spoiler(exception.login),
                                                   'и твой пароль', html.spoiler(exception.password)))

    await error_handler(error, admin_id, bot, state)

@error_router.errors(ExceptionTypeFilter(NoDataException))
async def no_data(error: ErrorEvent, admin_id: int, bot: Bot, state: FSMContext):
    await error.update.message.answer(f'произошла ошибка при получении оценок: {error.exception}')
    await error_handler(error, admin_id, bot, state)


@error_router.errors(ExceptionTypeFilter(TimeoutError))
async def timeout(error: ErrorEvent, admin_id: int, bot: Bot, state: FSMContext):
    await error.update.message.answer('Действие выполнялось слишком долго, из-за этого произошла ошибка.'
                                      'Возможно, это могло произойти из-за плохого подключения к серверу elschool.'
                                      'Как вариант стоит попробовать сделать это действие немного позже')
    await error_handler(error, admin_id, bot, state)


@error_router.errors(ExceptionTypeFilter(Exception))
async def error_handler(error: ErrorEvent, admin_id: int, bot: Bot, state: FSMContext):
    try:
        username = error.update.message.from_user.full_name
    except AttributeError:
        username = 'неизвестный пользователь'
    errtrace = traceback.format_exception(type(error.exception), error.exception, error.exception.__traceback__)
    len_err = len(errtrace)
    if len_err > 15:
        errtrace1 = html.code(fmt.text(*errtrace[:15], sep=''))
        await bot.send_message(admin_id, f'произошла ошибка у пользователя {username}\n{errtrace1}')
        errtrace = html.code(fmt.text(*errtrace[15:], sep=''))
        await bot.send_message(admin_id, errtrace)
    else:
        errtrace = html.code(fmt.text(*errtrace))
        await bot.send_message(admin_id, f'произошла ошибка у пользователя {username}\n{errtrace}')

    await handlers.cancel(error.update.message or error.update.callback_query.message, state)


def register_errors(dp: Dispatcher):
    dp.include_router(error_router)
