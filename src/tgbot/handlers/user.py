"""Обработка основных событий, совершённых пользователем."""
from aiogram import Router, Dispatcher
from aiogram.filters import StateFilter, Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.filters.command import CommandFilter
from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers.utils import show_grades, show_fix_grades, show_grades_for_lesson, lower_keys
from tgbot.keyboards.user import main_keyboard, row_list_keyboard, grades_keyboard, pick_grades_inline_keyboard, \
    pick_grades_keyboard, register_keyboard, cancel_keyboard
from tgbot.middlewares.grades import GradesMiddleware
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import Change, Page, Register

router = Router()
registered_router = Router()
grades_router = Router()
not_command_router = Router()


@router.message(StateFilter(Register.LOGIN), CommandFilter())
async def get_user_login(m: Message, state: FSMContext):
    """Когда пользователь при регистрации написал логин, вызывается эта функция."""
    await state.update_data(login=m.text)
    await m.delete()
    await m.answer('логин получил, теперь напиши пароль')
    await state.set_state(Register.PASSWORD)


@router.message(StateFilter(Register.PASSWORD), CommandFilter())
async def get_user_password(m: Message, repo: Repo, state: FSMContext):
    """Когда пользователь при регистрации написал пароль, вызывается эта функция."""
    await m.delete()
    data = await state.get_data()
    await m.answer('проверка введённых данных, попытка регистрации')
    jwtoken = await repo.register_user(data['login'], m.text)
    await state.update_data(jwtoken=jwtoken)
    await m.answer('удалось зарегистрироваться, данные введены правильно, теперь попробую получить оценки')
    grades, time, url = await repo.get_grades_userdata(jwtoken)
    quarters = list(grades)
    await state.update_data(url=url, quarters=list(grades.keys()))
    await state.set_state(Register.QUARTER)
    await m.answer(f'оценки получил за {time:.3f}с. Выбери какие оценки мне нужно показывать', reply_markup=row_list_keyboard(quarters))



@router.message(StateFilter(Register.QUARTER), CommandFilter())
async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    """Когда пользователь при регистрации указал четверть, вызывается эта функция."""
    data = await state.get_data()
    if m.text in data['quarters']:
        quarter = m.text
    else:
        quarters = list(data['quarters'].keys())
        await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
        return
    await repo.add_user(m.from_user.id, User(data['jwtoken'], quarter, url=data['url']))
    await m.answer('регистрация завершена, теперь можешь получать оценки', reply_markup=main_keyboard())
    await m.delete()
    await state.clear()


@router.message(Command('register'))
async def register(m: Message, state: FSMContext):
    """Когда пользователь захотел зарегистрироваться."""
    await state.set_state(Register.LOGIN)
    await m.answer('сейчас нужно ввести свои данные, сначала логин')


@router.message(Text('регистрация'))
async def keyboard_register(m: Message, state: FSMContext, repo: Repo):
    """Показывает страницу регистрации клавиатуры."""
    await state.set_state(Page.REGISTER)
    await state.update_data(message=m)
    await m.answer('выбери действие', reply_markup=register_keyboard(await repo.check_has_user(m.from_user.id)))


@router.callback_query(Text('register'), StateFilter(Page.REGISTER))
async def keybard_register_user(query: CallbackQuery, state: FSMContext):
    """Регистрация из клавиатуры."""
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await register(data['message'], state)
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
    await query.answer()
    await query.message.edit_reply_markup(pick_grades_inline_keyboard())
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
    await query.answer()


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


@registered_router.message(Command('clear_cache'))
async def clear_cache(m: Message, repo: Repo):
    """Очистка сохранённых оценок."""
    await repo.clear_user_cache(m.from_user.id)
    await m.answer('очистил сохранённые оценки')


@registered_router.message(Command('update_cache'))
async def update_cache(m: Message, repo: Repo):
    """Обновление сохранённых оценок."""
    await m.answer('обновляю сохранённые оценки')
    _, time = await repo.update_cache(m.from_user.id)
    await m.answer(f'оценки обновлены за {time: .3f} с')


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


@registered_router.callback_query(Text('back_main'))
async def back_main(query: CallbackQuery, state: FSMContext):
    """Обработка кнопки назад для возврата к основной странице."""
    await state.clear()
    await query.message.answer('основное меню', reply_markup=main_keyboard())
    await query.message.edit_reply_markup(None)
    await query.answer()


@router.message(Command('start'))
async def user_start(m: Message):
    """При старте бота показать приветственное сообщение."""
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help", reply_markup=main_keyboard())


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


@router.message(Command('version'))
@router.message(Text('версия'))
async def version(m: Message):
    """Показать версию и список изменений."""
    await m.answer("""моя версия: 2.6.14.dev0 (обновление 4.0)
список изменений:
Бот теперь использует базу данных вместо обычного файла для хранения данных о пользователях.
Исправлена ошибка, из-за которой нельзя было использовать команды.
Исправлено множество других мелких ошибок.
""")


@router.message(Command('version_comments'))
async def version_comments(m: Message):
    """Подробно показать список изменений."""
    await m.answer("""моя версия: 2.6.14.dev0 (обновление 4.0)

Бот теперь использует базу данных вместо обычного файла для хранения данных о пользователях. (возможно увеличение производительности).
Исправлена ошибка, из-за которой нельзя было использовать команды. (ошибка страшная, но решалась очень легко)
Исправлено множество других мелких ошибок. (я не помню каких, а нет вспомнил одну из них.) Например, неработающее изменение четверти, используя кнопку.
""")


@router.message(Command('help'))
async def help(m: Message):
    """Показать помощь."""
    await m.answer("""я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить

команды:
/register - указать данные для получения оценок
/get_grades - получить все оценки
/fix_grades - получить все оценки и как можно их исправить
/help - показать это сообщение
/version - показать версию и список изменений в последнем обновлении
/privacy_policy - посмотреть политику конфиденциальности 
/cancel - сбросить текущее состояние
/clear_cache - удалить сохранённые оценки.
/update_cache - обновить сохранённые оценки. Для скорости и некоторых других функций оценки хранятся в течение 1 часа, если по какой-то причине нужно их обновить можно использовать эту команду
/change_quarter - изменить четверть (полугодие, ну или как ещё можно назвать)
/reregister - изменить данные 
/unregister - удалить данные

Для получения оценок нужно обязательно указать свои данные с помощью /register или с помощью пункта в меню регистрация. Потребуется логин и пароль. Доступа к этим данным у разработчика нет. Всё это описано в политике конфиденциальности. 

Также, если просто написать название урока можно получить подробную информацию по каждой оценке""") #TODO добавить помощь по кнопкам.


@registered_router.message(StateFilter(Change.QUARTER), CommandFilter())
async def quarter_changed(m: Message, state: FSMContext, repo: Repo):
    """Когда пользователь выбрал четверть после того, как захотел её изменить."""
    quarters = await repo.get_quarters(m.from_user.id)
    if m.text in quarters:
        quarter = m.text
    else:
        await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
        return
    await repo.set_user_quarter(m.from_user.id, quarter)
    await state.clear()
    await m.answer('изменил', reply_markup=main_keyboard())


async def change_quarter(m: Message, user_id: int, state: FSMContext, repo: Repo):
    """Пользователь захотел изменить четверть."""
    await state.set_state(Change.QUARTER)
    quarters = await repo.get_quarters(user_id)
    await m.answer(f'выбери вариант', reply_markup=row_list_keyboard(quarters))


@registered_router.message(Command('change_quarter'), CommandFilter())
async def change_quarter_command(m: Message, repo: Repo, state: FSMContext):
    """Пользователь захотел изменить четверть из клавиатуры."""
    await change_quarter(m, m.from_user.id, state, repo)


@registered_router.callback_query(Text('change_quarter'))
async def change_quarter_query(query: CallbackQuery, state: FSMContext, repo: Repo):
    """Пользователь захотел изменить четверть с помощью команды."""
    await change_quarter(query.message, query.from_user.id, state, repo)
    await query.answer()


@router.message(Command('privacy_policy'))
async def privacy_policy(m: Message):
    """Показать политику конфиденциальности."""
    await m.answer('это что-то похожее на политику конфиденциальности. '
                   'Если кто-то напишет нормальную политику конфиденциальности, я её обновлю.')
    await m.answer("Для получения оценок бот просит логин и пароль от журнала elschool. "
                   "Эти данные используются только для получения токена. "
                   "Этот токен используется для получения оценок. Никак ваши данные из него получить нельзя", reply_markup=main_keyboard())


@router.callback_query(Text('privacy_policy'), StateFilter(Page.REGISTER))
async def privacy_policy_query(query: CallbackQuery, state: FSMContext):
    await privacy_policy(query.message)
    await query.answer()
    await state.clear()


@registered_router.message(Command('reregister'))
async def reregister(m: Message, state: FSMContext):
    """Пользователь захотел изменить данные.

    Это обработчик для команды и вспомогательная функция при использовании клавиатуры.
    """
    await m.answer('сейчас можно изменить свой логин и пароль, сначала введи новый логин')
    await state.set_state(Change.LOGIN)


@registered_router.message(StateFilter(Change.LOGIN), CommandFilter())
async def change_login(m: Message, state: FSMContext):
    """После ввода логина при изменении данных аккаунта."""
    await state.update_data(login=m.text)
    await state.set_state(Change.PASSWORD)
    await m.answer('хорошо, теперь напиши пароль')
    await m.delete()


@registered_router.message(StateFilter(Change.PASSWORD), CommandFilter())
async def change_password(m: Message, state: FSMContext, repo: Repo):
    """После ввода пароля при изменении данных аккаунта."""
    data = await state.get_data()
    login = data['login']
    password = m.text
    m = await m.answer('проверка введённых данных, попытка регистрации')
    await m.delete()
    jwtoken = await repo.register_user(login, password)
    await repo.update_user_token(m.from_user.id, jwtoken)
    await state.clear()
    await m.edit_text('удалось зарегистрироваться, данные введены правильно. Можешь получать оценки.')

@registered_router.callback_query(Text('change_data'), StateFilter(Page.REGISTER))
async def change_data(query: CallbackQuery, state: FSMContext):
    """Пользователь захотел изменить данные с помощью кнопки на клавиатуре."""
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await reregister(data['message'], state)
    await query.answer()

@registered_router.message(Command('unregister'))
async def unregister(m: Message, repo: Repo):
    """Пользователь захотел изменить данные.

    Как всегда, это обработчик для команды и вспомогательная
    функция при обработке события нажатия кнопки.
    """
    await repo.remove_user(m.from_user.id)
    await m.answer('я тебя удалил.', reply_markup=main_keyboard())


@registered_router.callback_query(Text('remove_data'), StateFilter(Page.REGISTER))
async def remove_data(query: CallbackQuery, repo: Repo, state: FSMContext):
    """Пользователь захотел изменить данные с помощью кнопки на клавиатуре."""
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await unregister(data['message'], repo)
    await state.clear()


@router.message(RegisteredUserFilter(False))
async def no_user(m: Message):
    """Пользователь не зарегистрирован,
    но захотел использовать функцию для зарегистрированных пользователей\
    """
    await m.answer('тебя нет в списке пользователей, попробуй зарегистрироваться')


@grades_router.message()
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


@not_command_router.message(CommandFilter(True))
async def text_is_command(message: Message):
    """В случае, если пользователь написал команду вместо того,
    что его попросили, будет вызываться эта функция.
    """
    await message.answer('по моему ты написал одну из моих команд. Тебя что попросили написать?')


def register_user(dp: Dispatcher):
    """Настройка роутеров."""
    dp.include_router(router)
    registered_router.message.filter(RegisteredUserFilter(True))
    router.include_router(registered_router)
    grades_middleware = GradesMiddleware()
    grades_router.message.middleware(grades_middleware)
    grades_router.callback_query.middleware(grades_middleware)
    registered_router.include_router(grades_router)
    router.include_router(not_command_router)