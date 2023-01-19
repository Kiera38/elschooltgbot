import traceback

from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.handlers.user import user_start
from tgbot.models.user import UserRole
from tgbot.services.repository import Repo
from tgbot.states.user import AdminState


async def admin_start(m: Message, repo: Repo):
    await m.reply("Hello, admin!")
    await user_start(m, repo)


async def admin_send_messages(m: Message, state: FSMContext):
    await m.answer('что хотите отправить?')
    await state.set_state(AdminState.SEND_MESSAGE)


async def admin_message(m: Message, repo: Repo, state: FSMContext):
    await m.answer('отправляю')
    for user_id in repo.user_ids():
        try:
            await m.bot.send_message(user_id, m.text)
        except Exception:
            exc_m = ''.join(traceback.format_exc())
            await m.answer(f'при отправке пользователю с id {user_id} произошло исключение {exc_m}')

    await state.finish()
    await m.answer('отправил')


async def users_count(m: Message, repo: Repo):
    await m.answer(f'сейчас у меня {len(repo.list_users())} пользователей')


async def no_admin(m: Message):
    await m.answer('эээ ты что. Тебе не доступно это действие. Оно может использоваться только моим разработчиком.')


def register_admin(dp: Dispatcher):
    dp.register_message_handler(admin_start, commands=["start"], state="*", role=UserRole.ADMIN)
    dp.register_message_handler(admin_send_messages, commands="send_message", state=None, is_admin=True)
    dp.register_message_handler(admin_message, state=AdminState.SEND_MESSAGE, is_admin=True)
    dp.register_message_handler(users_count, commands='users_count', is_admin=True)
    dp.register_message_handler(no_admin, commands=['send_message', 'users_count'], is_admin=False)
