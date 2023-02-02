from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.handlers.utils import show_grades, lower_keys, show_grades_for_lesson, show_fix_grades
from tgbot.keyboards.user import main_keyboard, row_list_keyboard
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import ParamsGetter, Change


async def show_all_grades(m: Message, grades):
    await m.answer(show_grades(grades), reply_markup=main_keyboard())


async def show_get_grades(m: Message, grades):
    if m.text == 'все':
        await show_all_grades(m, grades)
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


async def show_all_get_fix_grades(m: Message, grades):
    await m.answer(show_fix_grades(grades), reply_markup=main_keyboard())


async def show_get_fix_grades(m: Message, grades):
    if m.text == 'все':
        await show_all_get_fix_grades(m, grades)
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


async def register_user(m: Message, state: FSMContext):
    await state.set_state(ParamsGetter.GET_LOGIN)
    await m.answer('сейчас нужно ввести свои данные, сначала логин')


async def change_data(m: Message, state: FSMContext):
    await m.answer('сейчас можно изменить свой логин и пароль, сначала введи новый логин')
    await state.set_state(Change.LOGIN)


async def remove_data(m: Message, repo: Repo):
    try:
        repo.remove_user(m.from_user.id)
    except KeyError:
        await m.answer('ээээ. Ты куда собрался. Тебя нет в моём списке', reply_markup=main_keyboard())
    else:
        await m.answer('я тебя удалил.', reply_markup=main_keyboard())


async def show_version(m: Message):
    await m.answer("""моя версия: 2.5.7 (3 обновление)
список изменений:
Нормальная регистрация
Переход на aiogram 3.x 
Изменения в регистрации
Теперь перед получением оценок нужно один раз использовать /register для получения токена. С помощью этого токена бот получает оценки. Раньше использовал логин и пароль. Теперь логин и пароль используется только для получения токена.
Увеличение скорости получения оценок из-за изменившейся регистрации
Исправлена ошибка из-за которой ни один новый пользователь не мог получать оценки
Взаимодействие с ботом через кнопки
Большие изменения в коде 
Обновление политики конфиденциальности
обновление сообщения в /help
улучшена стабильность работы
""")


async def show_privacy_policy(m: Message):
    await m.answer('это что-то похожее на политику конфиденциальности. '
                   'Если кто-то напишет нормальную политику конфиденциальности, я её обновлю.')
    await m.answer("Для получения оценок бот просит логин и пароль от журнала elschool. "
                   "Эти данные используются только для получения токена. "
                   "Этот токен используется для получения оценок. Никак ваши данные из него получить нельзя")


async def change_quarter(m: Message, user: User, state: FSMContext, repo: Repo):
    await state.set_state(Change.QUARTER)
    if user.cached_grades:
        grades = user.cached_grades
    else:
        await m.answer('нет сохранённых, оценок. Чтобы узнать какие есть варианты, сейчас получу оценки')
        grades, time = await repo.get_grades(user)
        await m.answer(f'оценки получил за {time:.3f}с')
    quarters = list(grades.keys())
    await m.answer(f'выбери вариант', reply_markup=row_list_keyboard(quarters))