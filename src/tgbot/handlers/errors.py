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
    obj = error.update.message if error.update.message is not None else error.update.callback_query
    if obj is not None:
        username = obj.from_user.full_name
    else:
        username = 'неизвестный пользователь'
    errtrace = traceback.format_exception(type(error.exception), error.exception, error.exception.__traceback__)
    len_err = len(errtrace)
    await bot.send_message(admin_id, f'произошла ошибка у пользователя {username}')
    message_count = len_err // 15
    for mindex in range(message_count):
        if mindex * 15 + 15 < len_err:
            err_msg = ''.join(errtrace[mindex*15:mindex*15+15])
        else:
            err_msg = ''.join(errtrace[mindex*15:])
        await bot.send_message(admin_id, err_msg)

    await handlers.cancel(error.update.message or error.update.callback_query.message, state)


def register_errors(dp: Dispatcher):
    dp.include_router(error_router)
