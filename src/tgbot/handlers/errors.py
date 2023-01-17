import logging
import traceback

from aiogram import Dispatcher
from aiogram.types import Update

from tgbot.services.repository import NotRegisteredException, NoDataException

logger = logging.getLogger(__name__)


async def error_handler(update: Update, exception: Exception, admin_id:int):
    try:
        username = update.message.from_user.full_name
    except AttributeError:
        username = 'неизвестный пользователь'
    errtrace = ''.join(traceback.format_exception(type(exception), exception, exception.__traceback__))
    await update.bot.send_message(admin_id, f'произошла ошибка у пользователя {username}\n{errtrace}')
    await update.message.answer('при возникновении ошибки, то есть сейчас, рекомендую сбросить текущее состояние с помощью /cancel')


async def not_registered_handler(update: Update, exception: NotRegisteredException):
    await update.message.answer(f"произошла ошибка регистрации: {exception}")


async def no_data(update: Update, exception: NoDataException):
    await update.message.answer(f'произошла ошибка при получении оценок: {exception}')


async def timeout(update: Update, exception: NotRegisteredException):
    await update.message.answer('Действие выполнялось слишком долго, из-за этого произошла ошибка.'
                                'Возможно, это могло произойти из-за плохого подключения к серверу elschool.'
                                'Как вариант стоит попробовать сделать это действие немного позже')


def register_errors(dp: Dispatcher):
    dp.register_errors_handler(not_registered_handler, exception=NotRegisteredException)
    dp.register_errors_handler(timeout, exception=TimeoutError)
    dp.register_errors_handler(no_data, exception=NoDataException)
    dp.register_errors_handler(error_handler)

