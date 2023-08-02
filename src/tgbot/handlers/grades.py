from aiogram import Router, Dispatcher, F
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.filters.command import CommandFilter
from tgbot.handlers.user import registered_router
from tgbot.keyboards.user import main_keyboard, grades_keyboard, after_show_grades_keyboard, pick_lessons_keyboard
from tgbot.middlewares.grades import GradesMiddleware
from tgbot.services.repository import Repo
from tgbot.states.user import Page

grades_router = Router()
grades_page_router = Router()
pick_lessons_router = Router()


@grades_router.message(F.text == 'оценки')
async def grades(m: Message, state: FSMContext, grades_message: Message):
    """Показывает страницу оценок клавиатуры"""
    await state.set_state(Page.GRADES)
    await m.answer('выбери оценки', reply_markup=grades_keyboard())


async def update_grades_keyboard(query: CallbackQuery, state_data, **params):
    data = {**state_data, **params}
    await query.message.edit_reply_markup(reply_markup=grades_keyboard(all=data.get('all', True),
                                                          pick=data.get('pick'),
                                                          summary=data.get('summary'),
                                                          detail=data.get('detail'),
                                                          lesson_date=data.get('lesson_date'),
                                                          date=data.get('date'),
                                                          five=data.get('five'),
                                                          four=data.get('four'),
                                                          three=data.get('three'),
                                                          two=data.get('two')))


@grades_page_router.callback_query(F.data == 'summary')
async def update_summary(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    summary = not state_data.get('summary')
    detail = False if summary else state_data.get('detail')
    await state.update_data(summary=summary, detail=detail)
    await query.answer()
    await update_grades_keyboard(query, state_data, summary=summary, detail=detail)


@grades_page_router.callback_query(F.data == 'detail')
async def update_detail(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    detail = not state_data.get('detail')
    summary = False if detail else state_data.get('summary')
    await state.update_data(summary=summary, detail=detail)
    await query.answer()
    await update_grades_keyboard(query, state_data, summary=summary, detail=detail)


@grades_page_router.callback_query(F.data == 'all')
async def update_all(query: CallbackQuery, state: FSMContext):
    state_data = await state.get_data()
    all = not state_data.get('all', True)
    await query.answer()
    if all:
        await state.update_data(all=all, pick=set())
        await update_grades_keyboard(query, state_data, all=all, pick=set())
    else:
        await state.update_data(all=all)
        await update_grades_keyboard(query, state_data, all=all)


@grades_page_router.callback_query(F.data == 'pick')
async def update_pick(query: CallbackQuery, state: FSMContext, repo: Repo):
    state_data = await state.get_data()
    if not (lessons := state_data.get('lessons')):
        lessons = await repo.get_user_lessons(query.from_user.id)
        await state.update_data(lessons=lessons)

    pick = state_data.get('pick') or set()
    picked_lessons = [(lesson in pick, lesson) for lesson in lessons]
    await state.set_state(Page.PICK_LESSONS)
    await query.answer()
    await query.message.edit_reply_markup(reply_markup=pick_lessons_keyboard(picked_lessons))


@grades_page_router.callback_query(F.data.startswith('mark'))
async def update_mark(query: CallbackQuery, state: FSMContext):
    data = await state.get_data()
    mark = int(query.data[-1])
    name = {
        5: 'five',
        4: 'four',
        3: 'three',
        2: 'two'
    }[mark]
    update = {name: not data.get(name)}
    await state.update_data(update)
    await update_grades_keyboard(query, data, **update)


@pick_lessons_router.callback_query(F.data == 'back')
async def back_pick_lessons(query: CallbackQuery, state: FSMContext):
    await state.set_state(Page.GRADES)
    await query.answer()
    data = await state.get_data()
    if data.get('pick'):
        await state.update_data(all=False)
        await update_grades_keyboard(query, data, all=False)
    else:
        await update_grades_keyboard(query, data)


@pick_lessons_router.callback_query()
async def add_pick(query: CallbackQuery, state: FSMContext):
    lesson = int(query.data)
    state_data = await state.get_data()
    pick = state_data.get('pick') or set()
    if lesson in pick:
        pick.remove(lesson)
    else:
        pick.add(lesson)
    picked_lessons = [(i in pick, lesson) for i, lesson in enumerate(state_data['lessons'])]
    await state.update_data(pick=pick)
    await query.message.edit_reply_markup(reply_markup=pick_lessons_keyboard(picked_lessons))


@registered_router.callback_query(F.data == 'show')
async def show_grades(query: CallbackQuery, state: FSMContext, repo: Repo):
    await state.set_state(Page.AFTER_SHOW_GRADES)
    grades = await repo.get_grades(query.from_user.id)
    await query.message.edit_text(str(grades), reply_markup=after_show_grades_keyboard())


@grades_router.message(CommandFilter())
async def grades_one_lesson(m: Message, grades):
    """Показать оценки для одного урока."""
    if m.text == 'все':
        await m.answer(show_grades(grades), reply_markup=main_keyboard())
    else:
        grades = lower_keys(grades)
        lesson = m.text.lower()
        if lesson not in grades:
            await m.answer(f'кажется, тебе хотелось не этого получить. '
                           f'Если что, мне показалось, что ты хочешь получить оценки для {lesson}. '
                           f'Такого названия урока нет. Если хотел сделать что-то другое можешь обратится к моему разработчику.'
                           f'Он может добавить нужную функцию.')
            return
        await m.answer(show_grades_for_lesson(grades[lesson]), reply_markup=main_keyboard())


def register_handlers(dp: Dispatcher):
    middleware = GradesMiddleware()
    grades_router.message.middleware(middleware)
    grades_router.callback_query.middleware(middleware)
    registered_router.include_router(grades_router)
    grades_page_router.callback_query.filter(Page.GRADES)
    pick_lessons_router.callback_query.filter(Page.PICK_LESSONS)
    dp.include_router(grades_page_router)
    dp.include_router(pick_lessons_router)
