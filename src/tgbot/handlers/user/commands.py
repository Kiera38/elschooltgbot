from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers.user import router, registered_router, grades_router, functions
from tgbot.handlers.user.functions import show_all_grades, show_get_grades, show_all_get_fix_grades, register_user, \
    change_data, show_version, remove_data, show_privacy_policy
from tgbot.keyboards.user import main_keyboard, row_list_keyboard
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import ParamsGetter, Change


async def is_command(m: Message):
    if m.text in [
        "/get_grades",
        "/fix_grades",
        '/start',
        '/help',
        '/version',
        '/change_quarter',
        '/cancel',
        "/update_cache",
        '/clear_cache',
        '/new_version',
        '/reregister',
        '/unregister'
    ]:
        await m.answer('по моему ты написал одну из моих команд. Тебя что попросили написать?')
        return True
    return False


@router.message(StateFilter(ParamsGetter.GET_LOGIN))
async def get_user_login(m: Message, state: FSMContext):
    if await is_command(m):
        return
    await state.update_data(login=m.text)
    await m.delete()
    await m.answer('логин получил, теперь напиши пароль')
    await state.set_state(ParamsGetter.GET_PASSWORD)


@router.message(StateFilter(ParamsGetter.GET_PASSWORD))
async def get_user_password(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return

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



@router.message(StateFilter(ParamsGetter.GET_QUARTER))
async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    data = await state.get_data()
    if not m.text.isdigit():
        if m.text in data['quarters']:
            quarter = m.text
        else:
            quarters = list(data['quarters'].keys())
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
            return
    else:
        quarter = int(m.text)
        quarters = list(data['quarters'])
        if quarter > len(quarters):
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз',reply_markup=row_list_keyboard(quarters))
            return
        quarter = quarters[quarter - 1]
    repo.add_user(m.from_user.id, User(data['jwtoken'], quarter, url=data['url']))
    await m.answer('регистрация завершена, теперь можешь получать оценки', reply_markup=main_keyboard())
    await m.delete()
    await state.clear()


@router.message(Command('register'))
async def register(m: Message, state: FSMContext):
    await register_user(m, state)


@router.message(Command('start'))
async def user_start(m: Message):
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help", reply_markup=main_keyboard())


@grades_router.message(Command('get_grades'))
async def get_grades(m: Message, grades):
    await show_all_grades(m, grades)


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


@grades_router.message(Command('fix_grades'))
async def fix_grades(m: Message, grades):
    await show_all_get_fix_grades(m, grades)

@router.message(Command('version'))
async def version(m: Message):
    await show_version(m)


@router.message(Command('version_comments'))
async def version_comments(m: Message):
    await m.answer("""моя версия: 2.5.2 (3 обновление)
список изменений:
Нормальная регистрация (разобрался, как можно сделать)
Переход на aiogram 3.x (крупные компании обычно не меняют версии, но мне можно)
(если что aiogram 3.x предоставляет больше функций для разработчика по сравнению с 2.х, но это было несовместимое обновление)
Изменения в регистрации (знаю, написал во второй раз, но код мне пришлось тоже 2 раза писать)
Теперь перед получением оценок нужно один раз использовать /register для получения токена. С помощью этого токена бот получает оценки. Раньше использовал логин и пароль. Теперь логин и пароль используется только для получения токена.
Увеличение скорости получения оценок из-за изменившейся регистрации
Исправлена ошибка из-за которой ни один новый пользователь не мог получать оценки
Взаимодействие с ботом через кнопки
Большие изменения в коде (например из-за перехода на aiogram 3.x)
Обновление политики конфиденциальности
Ну и естественно обновление сообщения в /help
А ещё, как все разработчики любят писать, улучшена стабильность работы (ну кстати бот действительно должен работать стабильней)
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


@registered_router.message(StateFilter(Change.QUARTER))
async def quarter_changed(m: Message, state: FSMContext, repo: Repo):
    if await is_command(m):
        return
    user = repo.get_user(m.from_user.id)
    quarters = user.cached_grades
    if not m.text.isdigit():
        if m.text in quarters:
            quarter = m.text
        else:
            quarters = list(quarters.keys())
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
            return
    else:
        quarter = int(m.text)
        quarters = list(quarters)
        if quarter > len(quarters):
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
            return
        quarter = quarters[quarter-1]
    user.quarter = quarter
    await state.clear()
    await m.answer('изменил', reply_markup=main_keyboard())


@registered_router.message(Command('change_quarter'))
async def change_quarter(m: Message, repo: Repo, state: FSMContext):
    user = repo.get_user(m.from_user.id)
    await functions.change_quarter(m, user, state, repo)


@router.message(Command('privacy_policy'))
async def privacy_policy(m: Message):
    await show_privacy_policy(m)


@registered_router.message(Command('reregister'))
async def reregister(m: Message, state: FSMContext):
    await change_data(m, state)


@registered_router.message(StateFilter(Change.LOGIN))
async def change_login(m: Message, state: FSMContext):
    if await is_command(m):
        return
    await state.update_data(login=m.text)
    await state.set_state(Change.PASSWORD)
    await m.answer('хорошо, теперь напиши пароль')


@registered_router.message(StateFilter(Change.PASSWORD))
async def change_password(m: Message, state: FSMContext, repo: Repo):
    if await is_command(m):
        return
    data = await state.get_data()
    login = data['login']
    password = m.text
    await m.answer('проверка введённых данных, попытка регистрации')
    jwtoken = await repo.register_user(login, password)
    user = repo.get_user(m.from_user.id)
    user.jwtoken = jwtoken
    user.cached_grades = None
    await state.clear()
    await m.answer('удалось зарегистрироваться, данные введены правильно')


@registered_router.message(Command('unregister'))
async def unregister(m: Message, repo: Repo):
    await remove_data(m, repo)


@grades_router.message()
async def grades_one_lesson(m: Message, grades):
    await show_get_grades(m, grades)


@router.message(RegisteredUserFilter(False))
async def no_user(m: Message):
    await m.answer('тебя нет в списке пользователей, попробуй зарегистрироваться')
