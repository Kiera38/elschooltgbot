import traceback

from aiogram import Dispatcher, Router, Bot
from aiogram.filters import Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.filters.role import RoleFilter
from tgbot.handlers.user import user_start
from tgbot.models.user import UserRole
from tgbot.services.repository import Repo
from tgbot.states.user import AdminState


admin_router = Router()
admin_router.message.filter(RoleFilter(UserRole.ADMIN))

@admin_router.message(Command('start'))
async def admin_start(m: Message):
    await m.reply("Hello, admin!")
    await user_start(m)


@admin_router.message(Command('send_message'))
async def admin_send_messages(m: Message, state: FSMContext):
    await m.answer('что хотите отправить?')
    await state.set_state(AdminState.SEND_MESSAGE)


@admin_router.message(StateFilter(AdminState.SEND_MESSAGE))
async def admin_message(m: Message, repo: Repo, state: FSMContext, bot: Bot):
    await m.answer('отправляю')
    for user_id in repo.user_ids():
        try:
            await bot.send_message(user_id, m.text)
        except Exception:
            exc_m = ''.join(traceback.format_exc())
            await m.answer(f'при отправке пользователю с id {user_id} произошло исключение {exc_m}')

    await state.clear()
    await m.answer('отправил')


@admin_router.message(Command('users_count'))
async def users_count(m: Message, repo: Repo):
    await m.answer(f'сейчас у меня {len(repo.list_users())} пользователей')


async def no_admin(m: Message):
    await m.answer('эээ ты что. Тебе не доступно это действие. Оно может использоваться только моим разработчиком.')


def register_admin(dp: Dispatcher):
    dp.message.register(no_admin, RoleFilter(UserRole.USER), Command('send_message', 'users_count'))
    dp.include_router(admin_router)
