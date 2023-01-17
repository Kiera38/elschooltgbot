from aiogram import Dispatcher
from aiogram.types import BotCommand, Message

from tgbot.handlers.admin import register_admin
from tgbot.handlers.errors import register_errors
from tgbot.handlers.user import register_user


def get_commands():
    return [BotCommand("/get_grades", "получить оценки"),
            BotCommand("/fix_grades", "исправить все оценки"),
            BotCommand('/start', 'запустить бота'),
            BotCommand('/help', 'как пользоваться ботом'),
            BotCommand('/version', 'моя версия и список изменений'),
            BotCommand('/save_params', 'сохранить параметры'),
            BotCommand('/remove_params', 'удалить парамеры'),
            BotCommand('/remove_memory_params', 'полностью удалить параметры'),
            BotCommand('/change_quarter', 'изменить четверть'),
            BotCommand('/cancel', 'сбросить текущее состояние'),
            BotCommand("/update_cache", "обновить сохранённые оценки"),
            BotCommand('/admin_scope', 'КОМАНДЫ ТОЛЬКО ДЛЯ РАЗРАБОТЧИКА БОТА'),
            BotCommand('/send_message', 'отправить сообщение всем пользователям'),
            BotCommand('/users_count', 'показать количество пользователей')]


async def admin_scope(m: Message):
    await m.answer('это не команда! Только разделитель. Команды под этим разделителем тебе не доступны')


def register_handlers(dp: Dispatcher):
    dp.register_message_handler(admin_scope, commands='admin_scope')
    register_admin(dp)
    register_user(dp)
    register_errors(dp)
