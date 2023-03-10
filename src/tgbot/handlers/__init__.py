"""Настройка обработчиков для событий telegram"""

from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message, CallbackQuery
from tgbot.handlers import user, admin, errors
from tgbot.keyboards.user import main_keyboard


commands = {
    '/register': 'указать данные для получения оценок',
    '/get_grades': 'получить оценки',
    '/fix_grades': 'исправить все оценки',
    '/start': 'запустить бота и добавить в список пользователей',
    '/help': 'как пользоваться ботом',
    '/version': 'моя версия и список изменений',
    '/change_quarter': 'изменить четверть (полугодие)',
    '/reregister': 'изменить свои данные',
    '/unregister': 'удалить все данные',
    '/cancel': 'сбросить текущее состояние',
    '/update_cache': 'обновить сохранённые оценки',
    '/clear_cache': 'очистить сохранённые оценки'
}


def get_commands():
    """Получить все команды бота для отправки их в set_my_commands."""
    return [BotCommand(command=command, description=description) for command, description in commands.items()]


async def cancel(m: Message, state: FSMContext):
    """Сбросить состояние для пользователя."""
    await state.clear()
    await m.answer('текущее состояние сброшено', reply_markup=main_keyboard())


async def cancel_query(query: CallbackQuery, state: FSMContext):
    """Сбросить состояние для пользователя, используя кнопку."""
    await cancel(query.message, state)
    await query.answer()

def register_handlers(dp: Dispatcher):
    """Добавить все обработчики."""
    dp.message.register(cancel, Command('cancel'), StateFilter('*'))
    dp.callback_query.register(cancel_query, Text('cancel'))
    admin.register_admin(dp)
    user.register_user(dp)
    errors.register_errors(dp)
