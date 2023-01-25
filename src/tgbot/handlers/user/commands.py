from typing import cast

from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers.user import router, registered_router, grades_router
from tgbot.handlers.utils import show_grades, lower_keys, show_grades_for_lesson, show_fix_grades
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
    quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(grades, 1)])
    await state.update_data(url=url, quarters=list(grades.keys()))
    await state.set_state(ParamsGetter.GET_QUARTER)
    await m.answer(f'оценки получиз за {time:.3f}с. Выбери какие оценки мне нужно показывать, варианты\n{quarters}')



@router.message(StateFilter(ParamsGetter.GET_QUARTER))
async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    data = await state.get_data()
    if not m.text.isdigit():
        if m.text in data['quarters']:
            quarter = cast(list, data['quarters']).index(m.text) + 1
        else:
            quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(data['quarters'], 1)])
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз, варианты:\n{quarters}')
            return
    else:
        quarter = int(m.text)
        if quarter > len(data['quarters']):
            quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(data['quarters'], 1)])
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз, варианты:\n{quarters}')
            return
    repo.add_user(m.from_user.id, User(data['jwtoken'], quarter, url=data['url']))
    await m.answer('регистрация завершена, теперь можешь получать оценки')
    await m.delete()
    await state.clear()


@router.message(Command('register'))
async def register(m: Message, state: FSMContext):
    await state.set_state(ParamsGetter.GET_LOGIN)
    await m.answer('сейчас нужно ввести свои данные, сначала логин')



@router.message(Command('start'))
async def user_start(m: Message):
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help")


@grades_router.message(Command('get_grades'))
async def get_grades(m: Message, grades):
    await m.answer(show_grades(grades))


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
    await m.answer(show_fix_grades(grades))

@router.message(Command('version'))
async def version(m: Message):
    await m.answer("""моя версия: 1.5.8
список изменений:
улучшена обработка ошибок

Новая система ввода данных о пользователе:
При старте бот больше не просит данные, они будут запрошены при первом получении оценок. После этого данные хранятся только в оперативной памяти. Поэтому доступа у разработчика к ним нет. Но из-за этого при перезагрузке бота эти данные потеряются. Чтобы не потерять эти данные, можно сохранить на диске с помощью /save_params.

Появилась политика конфиденциальности. Чтобы её посмотреть, используйте /privacy_policy. 
Добавлено форматирование сообщений. 
добавлена команда /fix_grades в список команд telegram. Сама команда существовала давно, но в этом списке её не было
Улучшена команда /help в соответствии с обновлением
Добавлена команда /cancel. Она нужна чтобы сбросить текущее состояние
Команда админа бота /send_message теперь отправляет всем пользователям одновременно. Раньше она это делала по очереди. Она всё таки отправляет по очереди из-за ограничений telegram.  
Команды для разработчика добавлены в список команд. Но вы все равно не сможете ими воспользоваться. В /help их нет, только в списке команд
больше нельзя написать команду вместо чего-то, что просит бот""")


@router.message(Command('new_version'))
async def new_version(m: Message):
    await m.answer("""В следующем обновлении:
    
сделано:
Нормальная регистрация (разобрался, как можно сделать)

сейчас делаю:
переход на aiogram 3.x

будет сделано: 
Взаимодействие с ботом через кнопки (через команды также можно)
Некоторые мелкие изменения
Возможно база данных вместо обычного файла для хранения данных пользователей (в одном из обновлений это произойдёт, возможно в этом)
""")


@router.message(Command('help'))
async def help(m: Message):
    await m.answer("""я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить

команды:
/get_grades - получить все оценки
/fix_grades - получить все оценки и как можно их исправить
/help - показать это сообщение
/version - показать версию и список изменений в последнем обновлении
/new_version - показать , что будет в следующем обновлении
/privacy_policy - посмотреть политику конфиденциальности 
/cancel - сбросить текущее состояние
/clear_cache - удалить сохранённые оценки.
/update_cache - обновить сохранённые оценки. Для скорости и некоторых других функций оценки хранятся в течение 1 часа, если по какой-то причине нужно их обновить можно использовать эту команду
/change_quarter - изменить четверть (полугодие)
/reregister - изменить данные 
/unregister - удалить все данные

Команды, которые получают оценки могут потребовать логин и пароль. Доступа к этим данным у разработчика нет. Всё это описано в политике конфиденциальности. 

Также, если просто написать название урока можно получить подробную информацию по каждой оценке""")


@registered_router.message(StateFilter(Change.QUARTER))
async def quarter_changed(m: Message, state: FSMContext, repo: Repo):
    if await is_command(m):
        return
    user = repo.get_user(m.from_user.id)
    quarters = list(user.cached_grades)
    if not m.text.isdigit():
        if m.text in quarters:
            quarter = cast(list, quarters).index(m.text) + 1
        else:
            quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(quarters, 1)])
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз, варианты:\n{quarters}')
            return
    else:
        quarter = int(m.text)
        if quarter > len(quarters):
            quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(quarters, 1)])
            await m.answer(f'тут немного не правильно написано, попробуй ещё раз, варианты:\n{quarters}')
            return
    user.quarter = quarter
    await state.clear()
    await m.answer('изменил')


@registered_router.message(Command('change_quarter'))
async def change_quarter(m: Message, repo: Repo, state: FSMContext):
    user = repo.get_user(m.from_user.id)
    await state.set_state(Change.QUARTER)
    if user.cached_grades:
        grades = user.cached_grades
    else:
        await m.answer('нет сохранённых, оценок. Чтобы узнать какие есть варианты, сейчас получу оценки')
        grades, time = await repo.get_grades(user)
        await m.answer(f'оценки получил за {time:.3f}с')
    quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(grades, 1)])
    await m.answer(f'выбери вариант, укажи просто число, варианты \n{quarters}')


@router.message(Command('privacy_policy'))
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
    try:
        repo.remove_user(m.from_user.id)
    except KeyError:
        await m.answer('ээээ. Ты куда собрался. Тебя нет в моём списке')
    else:
        await m.answer('я тебя удалил.')


@grades_router.message()
async def grades_one_lesson(m: Message, grades):
    grades = lower_keys(grades)
    lesson = m.text.lower()
    if lesson not in grades:
        await m.answer(f'кажется, тебе хотелось не этого получить. '
                       f'Если что, мне показалось, что ты хочешь получить оценки для {lesson}. '
                       f'Такого названия урока нет. Если хотел сделать что-то другое можешь обратится к моему разработчику.'
                       f'Он может добавить нужную функцию.')
        return
    await m.answer(show_grades_for_lesson(grades[lesson]))


@router.message(RegisteredUserFilter(False))
async def no_user(m: Message):
    await m.answer('тебя нет в списке пользователей, сейчас добавлю, попробуй зарегистрироваться')
