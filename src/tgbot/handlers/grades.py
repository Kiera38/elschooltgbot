from aiogram import Router, Dispatcher
from aiogram.filters import Command, Text, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.filters.command import CommandFilter
from tgbot.handlers.user import registered_router
from aiogram.utils import markdown as fmt
from tgbot.keyboards.user import main_keyboard, pick_grades_keyboard, grades_keyboard
from tgbot.middlewares.grades import GradesMiddleware
from tgbot.services.grades_fixer import get_mean_gr, fix_to5, fix_to4
from tgbot.services.repository import Repo
from tgbot.states.user import Page

grades_router = Router()


def show_grades(grades):
    """Создать строку для сообщения со всеми оценками."""
    text = ['вот твои оценки']
    floor_grades = {3: [], 4: [], 5: []}
    for name, grade in grades.items():
        txt, floor_gr = show_grade(name, grade)
        text.append(txt)
        if floor_gr == 0:
            continue
        if floor_gr < 3.5:
            floor_grades[3].append(name)
        elif floor_gr < 4.5:
            floor_grades[4].append(name)
        else:
            floor_grades[5].append(name)
    if floor_grades[5]:
        lessons = ', '.join(floor_grades[5])
        text.append(fmt.text(fmt.hbold('5 выходит по урокам'), lessons))
    if floor_grades[4]:
        lessons = ', '.join(floor_grades[4])
        text.append(fmt.text(fmt.hbold('4 выходит по урокам'), lessons))
    if floor_grades[3]:
        lessons = ', '.join(floor_grades[3])
        text.append(fmt.text(fmt.hbold('3 выходит по урокам'), lessons))
    return '\n'.join(text)


def show_grade(name, grade):
    """Вспомогательная функция для создания строки для 1 урока."""
    gr = ', '.join([str(gra['value']) for gra in grade]) + ', '
    if gr == ', ':
        return fmt.text(fmt.hunderline(name), fmt.hbold('нет оценок')), 0
    else:
        floor_gr = get_mean_gr([gra['value'] for gra in grade])
        return fmt.text(fmt.hunderline(name), gr, fmt.hitalic('средняя'), f'{floor_gr:.2f}'), floor_gr


def lower_keys(grades):
    """Создаёт словарь на основе другого в котором все строки написаны маленькими буквами."""
    return {key.lower(): value for key, value in grades.items()}


def show_grades_for_lesson(grades):
    """Создаёт строку для показа сообщения для 1 урока."""
    text = []
    for grade in grades:
        gr = grade['value']
        date = grade['date']
        text.append(fmt.text(fmt.text(fmt.hunderline('оценка'), gr), date, sep='\n'))
    grades_list = [grade['value'] for grade in grades]
    round_grade = get_mean_gr(grades_list)
    text.append(fmt.text(fmt.hitalic('средняя'), f'{round_grade:.2f}'))
    if round_grade < 3.5:
        text.append(show_fix_to4(grades_list))
    if round_grade < 4.5:
        text.append(show_fix_to5(grades_list))
    return '\n'.join(text)


def show_fix_to5(grades_list):
    """Строка для показа, как можно исправить оценку до 5."""
    tooltips = ', '.join([str(i) for i in fix_to5(grades_list)])
    return fmt.text('для', fmt.hitalic('исправления оценки до 5'), 'можно получить', tooltips)


def show_fix_to4(grades_list):
    """Строка для показа, как можно исправить оценку до 4."""
    tooltips = ' или '.join([fmt.text(*var, sep=', ') for var in fix_to4(grades_list)])
    return fmt.text('для', fmt.hitalic('исправления оценки до 4'), 'можно получить', tooltips)


def show_fix_grades(grades):
    """Строка для отправки всех оценок и как их можно исправить."""
    text = []
    for name, grade in grades.items():
        txt, round_grade = show_grade(name, grade)
        text.append(txt)
        grades_list = [gr['value'] for gr in grade]
        if round_grade < 3.5:
            text.append(show_fix_to4(grades_list))
        if round_grade < 4.5:
            text.append(show_fix_to5(grades_list))
    return '\n'.join(text)


@registered_router.callback_query(Text('back_grades'))
async def back_grades(query: CallbackQuery, state: FSMContext):
    """Обработка кнопки назад для возврата к странице оценок."""
    await state.set_state(Page.GRADES)
    await query.message.edit_reply_markup(grades_keyboard(True))
    data = await state.get_data()
    message: Message = data.get('grades_message')
    if message:
        await message.delete()
    await query.answer()


@registered_router.message(Text('оценки'))
async def grades(m: Message, state: FSMContext):
    """Показывает страницу оценок клавиатуры"""
    await state.set_state(Page.GRADES)
    await m.answer('выбери действие', reply_markup=grades_keyboard())


async def grades_query(query: CallbackQuery, repo: Repo, state: FSMContext, next_state, answer_text: str):
    """Вспомогательная функция для обработки действий со страницы оценок."""
    lessons = await repo.get_user_lessons(query.from_user.id)
    await state.set_state(next_state)
    #await query.message.edit_reply_markup(pick_grades_inline_keyboard())
    message = await query.message.answer(answer_text, reply_markup=pick_grades_keyboard(lessons=lessons))
    await state.update_data(grades_message=message)


@registered_router.callback_query(Text('get_grades'), StateFilter(Page.GRADES))
async def get_grades_query(query: CallbackQuery, repo: Repo, state: FSMContext):
    """Когда пользователь выбрал показать оценки на станице оценок клавиатуры."""
    await grades_query(query, repo, state, Page.GET_GRADES, 'какие оценки показать')


@registered_router.callback_query(Text('fix_grades'), StateFilter(Page.GRADES))
async def fix_grades_query(query: CallbackQuery, repo: Repo, state: FSMContext):
    """Когда пользователь выбрал исправить оценки на странице оценок клавиатуры."""
    await grades_query(query, repo, state, Page.FIX_GRADES, 'какие оценки исправить')


@grades_router.message(Command('get_grades'))
async def get_grades(m: Message, grades):
    """Обработчик для команды показа оценок, но также функция для показа оценок."""
    await m.answer(show_grades(grades), reply_markup=main_keyboard())


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.GET_GRADES))
async def get_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    """Когда пользователь выбрал показать все оценки на клавиатуре."""
    await get_grades(query.message, grades)
    await state.clear()


@grades_router.message(StateFilter(Page.GET_GRADES))
async def keyboard_get_grades(m: Message, grades: dict, state: FSMContext):
    """Когда пользователь выбрал показать оценки по конкретному уроку."""
    await grades_one_lesson(m, grades)
    await state.clear()


@grades_router.message(StateFilter(Page.FIX_GRADES))
async def keyboard_fix_grades(m: Message, grades: dict, state: FSMContext):
    """Когда пользователь выбрал исправить оценки по конкретному уроку."""
    if m.text == 'все':
        await fix_grades(m, grades)
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
    await state.clear()


@grades_router.message(Command('fix_grades'))
async def fix_grades(m: Message, grades):
    """Обработка команды исправления оценок и функция для показа сообщения исправления оценок."""
    await m.answer(show_fix_grades(grades), reply_markup=main_keyboard())


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.FIX_GRADES))
async def fix_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    """Обработка кнопки исправления всех оценок."""
    await fix_grades(query.message, grades)
    await state.clear()
    await query.answer()


@grades_router.message(CommandFilter())
async def grades_one_lesson(m: Message, grades):
    """Показать оценки для одного урока."""
    if m.text == 'все':
        await get_grades(m, grades)
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
