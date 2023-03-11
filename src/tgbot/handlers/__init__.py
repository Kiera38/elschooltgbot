from aiogram import Dispatcher
from aiogram.filters import Command, StateFilter, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import BotCommand, Message, CallbackQuery
from tgbot.handlers import user, admin, errors
from tgbot.keyboards.user import main_keyboard


def get_commands():
    """Получить все команды бота для отправки их в set_my_commands."""
    #TODO сейчас все команды записаны в нескольких местах. Их нужно объединить в одно место.
    return [BotCommand(command='/register', description='указать данные для получения оценок'),
            BotCommand(command="/get_grades", description="получить оценки"),
            BotCommand(command="/fix_grades", description="исправить все оценки"),
            BotCommand(command='/start', description='запустить бота и добавить в список пользователей'),
            BotCommand(command='/help', description='как пользоваться ботом'),
            BotCommand(command='/version', description='моя версия и список изменений'),
            BotCommand(command='/new_version', description='список изменений в будущей версии'),
            BotCommand(command='/change_quarter', description='изменить четверть (полугодие)'),
            BotCommand(command="/reregister", description='изменить свои данные'),
            BotCommand(command='/unregister', description='удалить все данные'),
            BotCommand(command='/cancel', description='сбросить текущее состояние'),
            BotCommand(command="/update_cache", description="обновить сохранённые оценки"),
            BotCommand(command='/clear_cache', description='очистить сохранённые оценки')]


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
