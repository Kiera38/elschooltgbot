from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message
from tgbot.handlers import user, admin, errors


def get_commands():
    return [BotCommand(command='/register', description=''),
            BotCommand(command="/get_grades", description="получить оценки"),
            BotCommand(command="/fix_grades", description="исправить все оценки"),
            BotCommand(command='/start', description='запустить бота и добавить в список пользователей'),
            BotCommand(command='/help', description='как пользоваться ботом'),
            BotCommand(command='/version', description='моя версия и список изменений'),
            BotCommand(command='/new_version', description='список изменений в будущей версии'),
            BotCommand(command='/change_quarter', description='изменить четверть'),
            BotCommand(command="/reregister", description='изменить свои данные'),
            BotCommand(command='/unregister', description='удалить все данные'),
            BotCommand(command='/cancel', description='сбросить текущее состояние'),
            BotCommand(command="/update_cache", description="обновить сохранённые оценки"),
            BotCommand(command='/clear_cache', description='очистить сохранённые оценки')]


async def admin_scope(m: Message):
    await m.answer('это не команда! Только разделитель. Команды под этим разделителем тебе не доступны')


async def cancel(m: Message, state: FSMContext):
    await state.clear()
    await m.answer('текущее состояние сброшено')

def register_handlers(dp: Dispatcher):
    dp.message.register(cancel, Command('cancel'), StateFilter('*'))
    dp.message.register(admin_scope, Command('admin_scope'))
    admin.register_admin(dp)
    user.register_user(dp)
    errors.register_errors(dp)
