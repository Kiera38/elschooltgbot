from aiogram import Router, Dispatcher
from aiogram.filters import StateFilter, Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery

from tgbot.filters.Command import CommandFilter
from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers.utils import show_grades, show_fix_grades, show_grades_for_lesson, lower_keys
from tgbot.keyboards.user import main_keyboard, row_list_keyboard, grades_keyboard, pick_grades_inline_keyboard, \
    pick_grades_keyboard, register_keyboard, cancel_keyboard
from tgbot.middlewares.grades import GradesMiddleware
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import ParamsGetter, Change, Page

router = Router()
registered_router = Router()
grades_router = Router()


@router.message(CommandFilter(True))
async def text_is_command(message: Message):
    await message.answer('по моему ты написал одну из моих команд. Тебя что попросили написать?')


@router.message(StateFilter(ParamsGetter.GET_LOGIN), CommandFilter())
async def get_user_login(m: Message, state: FSMContext):
    await state.update_data(login=m.text)
    await m.delete()
    await m.answer('логин получил, теперь напиши пароль')
    await state.set_state(ParamsGetter.GET_PASSWORD)


@router.message(StateFilter(ParamsGetter.GET_PASSWORD), CommandFilter())
async def get_user_password(m: Message, repo: Repo, state: FSMContext):
    await m.delete()
    data = await state.get_data()
    await m.answer('проверка введённых данных, попытка регистрации')
    jwtoken = await repo.register_user(data['login'], m.text)
    await state.update_data(jwtoken=jwtoken)
    await m.answer('удалось зарегистрироваться, данные введены правильно, теперь попробую получить оценки')
    grades, time, url = await repo.get_grades_userdata(jwtoken)
    quarters = list(grades)
    await state.update_data(url=url, quarters=list(grades.keys()))
    await state.set_state(ParamsGetter.GET_QUARTER)
    await m.answer(f'оценки получил за {time:.3f}с. Выбери какие оценки мне нужно показывать', reply_markup=row_list_keyboard(quarters))



@router.message(StateFilter(ParamsGetter.GET_QUARTER), CommandFilter())
async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    data = await state.get_data()
    if m.text in data['quarters']:
        quarter = m.text
    else:
        quarters = list(data['quarters'].keys())
        await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
        return
    repo.add_user(m.from_user.id, User(data['jwtoken'], quarter, url=data['url']))
    await m.answer('регистрация завершена, теперь можешь получать оценки', reply_markup=main_keyboard())
    await m.delete()
    await state.clear()


@router.message(Command('register'))
async def register(m: Message, state: FSMContext):
    await state.set_state(ParamsGetter.GET_LOGIN)
    await m.answer('сейчас нужно ввести свои данные, сначала логин')


@router.message(Text('регистрация'))
async def keyboard_register(m: Message, state: FSMContext, repo: Repo):
    await state.set_state(Page.REGISTER)
    await state.update_data(message=m)
    await m.answer('выбери действие', reply_markup=register_keyboard(
        repo.has_user(m.from_user.id) and repo.get_user(m.from_user.id).jwtoken is not None))


@router.callback_query(Text('register'), StateFilter(Page.REGISTER))
async def keybard_register_user(query: CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await register(data['message'], state)
    await query.answer()


@registered_router.message(Text('оценки'))
async def grades(m: Message, state: FSMContext):
    await state.set_state(Page.GRADES)
    await m.answer('выбери действие', reply_markup=grades_keyboard())


async def grades_query(query: CallbackQuery, repo: Repo, state: FSMContext, next_state, answer_text: str, show_all):
    user = repo.get_user(query.from_user.id)
    if user.cached_grades:
        if user.quarter not in user.cached_grades:
            await query.message.answer('такой четверти не существует, попробуй изменить четверть')
            grades = {}
        else:
            grades = user.cached_grades[user.quarter]
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


@grades_router.message(Command('get_grades'))
async def get_grades(m: Message, grades):
    await m.answer(show_grades(grades), reply_markup=main_keyboard())


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.GET_GRADES))
async def get_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    await get_grades(query.message, grades)
    await state.clear()
    await query.answer()


@grades_router.message(StateFilter(Page.GET_GRADES))
async def keyboard_get_grades(m: Message, grades: dict, state: FSMContext):
    await grades_one_lesson(m, grades)
    await state.clear()


@grades_router.message(StateFilter(Page.FIX_GRADES))
async def keyboard_fix_grades(m: Message, grades: dict, state: FSMContext):
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
    user = repo.get_user(m.from_user.id)
    user.cached_grades = None
    await m.answer('очистил сохранённые оценки')


@registered_router.message(Command('update_cache'))
async def update_cache(m: Message, repo: Repo):
    await clear_cache(m, repo)
    await m.answer('обновляю сохранённые оценки')
    grades, time = await repo.get_grades(repo.get_user(m.from_user.id))
    await m.answer(f'оценки обновлены за {time: _.3f} с')


@registered_router.callback_query(Text('back_grades'))
async def back_grades(query: CallbackQuery, state: FSMContext):
    await state.set_state(Page.GRADES)
    await query.message.edit_reply_markup(grades_keyboard(True))
    data = await state.get_data()
    message: Message = data.get('grades_message')
    if message:
        await message.delete()
    await query.answer()


@registered_router.callback_query(Text('back_main'))
async def back_main(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer('основное меню', reply_markup=main_keyboard())
    await query.message.edit_reply_markup(None)
    await query.answer()


@router.message(Command('start'))
async def user_start(m: Message):
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help", reply_markup=main_keyboard())


@grades_router.message(Command('fix_grades'))
async def fix_grades(m: Message, grades):
    await m.answer(show_fix_grades(grades), reply_markup=main_keyboard())


@grades_router.callback_query(Text('all_grades'), StateFilter(Page.FIX_GRADES))
async def fix_all_grades(query: CallbackQuery, grades: dict, state: FSMContext):
    await fix_grades(query.message, grades)
    await state.clear()
    await query.answer()


@router.message(Command('version'))
@router.message(Text('версия'))
async def version(m: Message):
    await m.answer("""моя версия: 2.5.10.dev2 (обновление 3.1)
список изменений:
Исправление ошибок
""")


@router.message(Command('version_comments'))
async def version_comments(m: Message):
    await m.answer("""моя версия: 2.5.10.dev2 (обновление 3.1)

Исправление ошибок (ну как исправление. Скорее мойка кота.)
Код упрощён и почищен, улучшен. Если более конкретно, то удалены и перемещены некоторые функции.
""")


@router.message(Command('help'))
async def help(m: Message):
    await m.answer("""я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить

команды:
/register - указать данные для получения оценок
/get_grades - получить все оценки
/fix_grades - получить все оценки и как можно их исправить
/help - показать это сообщение
/version - показать версию и список изменений в последнем обновлении
/new_version - показать , что будет в следующем обновлении
/privacy_policy - посмотреть политику конфиденциальности 
/cancel - сбросить текущее состояние
/clear_cache - удалить сохранённые оценки.
/update_cache - обновить сохранённые оценки. Для скорости и некоторых других функций оценки хранятся в течение 1 часа, если по какой-то причине нужно их обновить можно использовать эту команду
/change_quarter - изменить четверть (полугодие, ну или как ещё можно назвать)
/reregister - изменить данные 
/unregister - удалить данные

Для получения оценок нужно обязательно указать свои данные с помощью /register или с помощью пункта в меню регистрация. Потребуется логин и пароль. Доступа к этим данным у разработчика нет. Всё это описано в политике конфиденциальности. 

Также, если просто написать название урока можно получить подробную информацию по каждой оценке""")


@registered_router.message(StateFilter(Change.QUARTER), CommandFilter())
async def quarter_changed(m: Message, state: FSMContext, repo: Repo):
    user = repo.get_user(m.from_user.id)
    quarters = user.cached_grades
    if m.text in quarters:
        quarter = m.text
    else:
        quarters = list(quarters.keys())
        await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
        return
    user.quarter = quarter
    await state.clear()
    await m.answer('изменил', reply_markup=main_keyboard())


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


@registered_router.message(Command('change_quarter'), CommandFilter())
async def change_quarter_command(m: Message, repo: Repo, state: FSMContext):
    user = repo.get_user(m.from_user.id)
    await change_quarter(m, user, state, repo)


@registered_router.callback_query(Text('change_quarter'))
async def change_quarter(query: CallbackQuery, state: FSMContext, repo: Repo):
    user = repo.get_user(query.from_user.id)
    await change_quarter(query.message, user, state, repo)
    await query.answer()


@router.message(Command('privacy_policy'))
@router.message(Text('политика конфиденциальности'))
async def privacy_policy(m: Message):
    await m.answer('это что-то похожее на политику конфиденциальности. '
                   'Если кто-то напишет нормальную политику конфиденциальности, я её обновлю.')
    await m.answer("Для получения оценок бот просит логин и пароль от журнала elschool. "
                   "Эти данные используются только для получения токена. "
                   "Этот токен используется для получения оценок. Никак ваши данные из него получить нельзя")


@registered_router.message(Command('reregister'))
async def reregister(m: Message, state: FSMContext):
    await m.answer('сейчас можно изменить свой логин и пароль, сначала введи новый логин')
    await state.set_state(Change.LOGIN)


@registered_router.message(StateFilter(Change.LOGIN), CommandFilter())
async def change_login(m: Message, state: FSMContext):
    await state.update_data(login=m.text)
    await state.set_state(Change.PASSWORD)
    await m.answer('хорошо, теперь напиши пароль')
    await m.delete()


@registered_router.message(StateFilter(Change.PASSWORD), CommandFilter())
async def change_password(m: Message, state: FSMContext, repo: Repo):
    data = await state.get_data()
    login = data['login']
    password = m.text
    await m.answer('проверка введённых данных, попытка регистрации')
    await m.delete()
    jwtoken = await repo.register_user(login, password)
    user = repo.get_user(m.from_user.id)
    user.jwtoken = jwtoken
    user.cached_grades = None
    await state.clear()
    await m.answer('удалось зарегистрироваться, данные введены правильно. Можешь получать оценки.')

@registered_router.callback_query(Text('change_data'), StateFilter(Page.REGISTER))
async def change_data(query: CallbackQuery, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await reregister(data['message'], state)
    await query.answer()

@registered_router.message(Command('unregister'))
async def unregister(m: Message, repo: Repo):
    try:
        repo.remove_user(m.from_user.id)
    except KeyError:
        await m.answer('ээээ. Ты куда собрался. Тебя нет в моём списке', reply_markup=main_keyboard())
    else:
        await m.answer('я тебя удалил.', reply_markup=main_keyboard())


@registered_router.callback_query(Text('remove_data'), StateFilter(Page.REGISTER))
async def remove_data(query: CallbackQuery, repo: Repo, state: FSMContext):
    await query.message.edit_reply_markup(cancel_keyboard())
    data = await state.get_data()
    await unregister(data['message'], repo)
    await state.clear()


@router.message(RegisteredUserFilter(False))
async def no_user(m: Message):
    await m.answer('тебя нет в списке пользователей, попробуй зарегистрироваться')


@grades_router.message()
async def grades_one_lesson(m: Message, grades):
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


def register_user(dp: Dispatcher):
    dp.include_router(router)
    registered_router.message.filter(RegisteredUserFilter(True))
    router.include_router(registered_router)
    grades_middleware = GradesMiddleware()
    grades_router.message.middleware(grades_middleware)
    grades_router.callback_query.middleware(grades_middleware)
    registered_router.include_router(grades_router)