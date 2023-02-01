from aiogram.filters import Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.handlers.user import registered_router, grades_router, router, functions
from tgbot.handlers.user.functions import show_get_grades, show_get_fix_grades, show_version, show_all_grades, \
    show_all_get_fix_grades, show_privacy_policy
from tgbot.keyboards.user import grades_keyboard, pick_grades_keyboard, register_keyboard, cancel_keyboard, \
    pick_grades_inline_keyboard, main_keyboard
from tgbot.services.repository import Repo
from tgbot.states.user import Page


@registered_router.message(Text('оценки'))
async def grades(m: Message, state: FSMContext):
    await state.set_state(Page.GRADES)
    await m.answer('выбери действие', reply_markup=grades_keyboard())


async def grades_query(query: CallbackQuery, repo: Repo, state: FSMContext, next_state, answer_text: str, show_all):
    user = repo.get_user(query.from_user.id)
    if user.cached_grades:
        if isinstance(user.quarter, str):
            if user.quarter not in user.cached_grades:
                await query.message.answer('такой четверти не существует, попробуй изменить четверть')
                grades = {}
            else:
                grades = user.cached_grades[user.quarter]
        else:
            if user.quarter-1 > len(list(user.cached_grades)):
                await query.message.answer('такой четверти не существует, попробуй изменить четверть')
                grades = {}
            else:
                grades = list(user.cached_grades.values())[user.quarter-1]
                user.quarter = list(grades.keys())[user.quarter-1]
        lessons = list(grades.keys())
    else:
        lessons = []
    await state.set_state(next_state)
    await query.answer()
    await query.message.edit_reply_markup(pick_grades_inline_keyboard())
    message = await query.message.answer(answer_text, reply_markup=pick_grades_keyboard(lessons=lessons))
    await state.update_data(grades_message=message)


@registered_router.callback_query(Text('get_grades'), StateFilter(Page.GRADES))
async def get_grades_query(query: CallbackQuery, repo: Repo, state: FSMContext):
    await grades_query(query, repo, state, Page.GET_GRADES, 'какие оценки получить', True)


@registered_router.callback_query(Text('fix_grades'), StateFilter(Page.GRADES))
async def fix_grades_query(query: CallbackQuery, repo: Repo, state: FSMContext):
    await grades_query(query, repo, state, Page.FIX_GRADES, 'какие оценки исправить', True)


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.GET_GRADES))
async def get_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    await show_all_grades(query.message, grades)
    await state.clear()
    await query.answer()


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.FIX_GRADES))
async def fix_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    await show_all_get_fix_grades(query.message, grades)
    await state.clear()
    await query.answer()


@grades_router.message(StateFilter(Page.GET_GRADES))
async def get_grades(m: Message, grades: dict, state: FSMContext):
    await show_get_grades(m, grades)
    await state.clear()


@grades_router.message(StateFilter(Page.FIX_GRADES))
async def fix_grades(m: Message, grades: dict, state: FSMContext):
    await show_get_fix_grades(m, grades)
    await state.clear()


@registered_router.callback_query(Text('back_grades'))
async def back_grades(query: CallbackQuery, state: FSMContext):
    await state.set_state(Page.GRADES)
    await query.message.edit_reply_markup(grades_keyboard(True))
    data = await state.get_data()
    message: Message = data['grades_message']
    await message.delete()
    await query.answer()


@registered_router.callback_query(Text('back_main'))
async def back_main(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer('основное меню', reply_markup=main_keyboard())
    await query.message.edit_reply_markup(None)
    await query.answer()


@registered_router.callback_query(Text('change_quarter'))
async def change_quarter(query: CallbackQuery, state: FSMContext, repo: Repo):
    user = repo.get_user(query.from_user.id)
    await functions.change_quarter(query.message, user, state, repo)
    await query.answer()


@router.message(Text('регистрация'))
async def register(m: Message, state: FSMContext, repo: Repo):
    await state.set_state(Page.REGISTER)
    await state.update_data(message=m)
    await m.answer('выбери действие', reply_markup=register_keyboard(repo.has_user(m.from_user.id)))


@router.callback_query(Text('register'), StateFilter(Page.REGISTER))
async def register_user(query: CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await functions.register_user(data['message'], state)
    await query.answer()


@registered_router.callback_query(Text('change_data'), StateFilter(Page.REGISTER))
async def change_data(query: CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await functions.change_data(data['message'], state)
    await query.answer()


@registered_router.callback_query(Text('remove_data'), StateFilter(Page.REGISTER))
async def remove_data(query: CallbackQuery, repo: Repo, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await functions.remove_data(data['message'], repo)
    await state.clear()


@router.message(Text('версия'))
async def version(m: Message):
    await show_version(m)


@router.message(Text('политика конфиденциальности'))
async def privacy_policy(m: Message):
    await show_privacy_policy(m)