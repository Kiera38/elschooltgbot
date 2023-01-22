import inspect

from aiogram import Dispatcher, Router
from aiogram.filters import StateFilter, Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers.utils import show_grades, lower_keys, show_grades_for_lesson, show_fix_grades
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import ParamsGetter


user_router = Router()

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


@user_router.message(StateFilter(ParamsGetter.GET_LOGIN))
async def get_user_login(m: Message, state: FSMContext):
    if await is_command(m):
        return
    await state.update_data(login=m.text)
    await m.delete()
    await m.answer('логин сохранён, теперь напиши пароль')
    await state.set_state(ParamsGetter.GET_PASSWORD)


@user_router.message(StateFilter(ParamsGetter.GET_PASSWORD))
async def get_user_password(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return

    await m.delete()
    await m.answer('пароль сохранён')
    data = await state.get_data()
    await m.answer('проверка введённых данных, попытка регистрации')
    await repo.register_user(m.from_user.id, data['login'], m.text)
    await m.answer('удалось зарегистрироваться, данные введены правильно')
    if data:
        partial_data = _check_spec(data['spec'], {'user': repo.get_user(m.from_user.id), 'repo': repo, 'state': state})
        await data['command'](data['orig_msg'], **partial_data)
        if data['finish_state']:
            await state.clear()
    else:
        await state.clear()


@user_router.message(StateFilter(ParamsGetter.GET_QUARTER))
async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    if not m.text.isdigit():
        await m.answer(f'должно быть число, например 1, не {m.text}')
    else:
        user = repo.get_user(m.from_user.id)
        user.quarter = int(m.text)
        await m.answer('сохранено')
        await m.delete()
        data = await state.get_data()
        if data:
            if user.has_cashed_grades:
                await m.answer('есть сохранённые оценки, использую их')
            else:
                await m.answer('оценки не сохранены, получаю новые оценки, пожалуйста подожди')
            grades, time = await repo.get_grades(user)
            grades = list(grades.values())[user.quarter-1]
            if time:
                await m.answer(f'оценки получены за {time:_.3f}')
            partial_data = _check_spec(data['spec'], {'user': user, 'repo': repo, 'state': state, 'grades': grades})
            await data['command'](data['orig_msg'], **partial_data)
            if data['finish_state']:
                await state.clear()
        else:
            await state.clear()


@user_router.message(Command('start'))
async def user_start(m: Message, repo: Repo):
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help")
    repo.add_user(m.from_user.id, User())


def _check_spec(spec: inspect.FullArgSpec, kwargs: dict):
    if spec.varkw:
        return kwargs

    return {k: v for k, v in kwargs.items() if k in set(spec.args + spec.kwonlyargs)}


def register_needed(finish_state=False):
    def force_registered(command):
        spec = inspect.getfullargspec(command)
        async def registered(message: Message, repo: Repo, state: FSMContext, **kwargs):
            user = repo.get_user(message.from_user.id)
            if user.jwtoken is not None:
                partial_data = _check_spec(spec, {'user': user, 'repo': repo, 'state': state, **kwargs})
                await command(message, **partial_data)
                if finish_state:
                    await state.clear()
            else:
                await message.answer('похоже, что ты ещё не пробовал получать оценки. '
                                     'Сейчас нужно будет указать свои данные от elschool. '
                                     'Так я смогу получить всю нужную информацию. Эти данные я не собираюсь сохранять.')
                await message.answer('сейчас введи логин')
                await state.set_state(ParamsGetter.GET_LOGIN)
                await state.update_data(command=command, spec=spec, finish_state=finish_state, orig_msg=message)

        return registered
    return force_registered

def grades_command(finish_state=False):
    def force_quarter(command):
        spec = inspect.getfullargspec(command)
        @register_needed()
        async def quarter(m: Message, repo: Repo, state: FSMContext, user: User = None, **kwargs):
            if user is None:
                user = repo.get_user(m.from_user.id)
            if user.has_cashed_grades:
                await m.answer('есть сохранённые оценки, использую их')
            else:
                await m.answer('оценки не сохранены, получаю новые оценки, пожалуйста подожди')
            grades, time = await repo.get_grades(user)
            if time:
                await m.answer(f'оценки получены за {time:_.3f}')
            if user.quarter:
                grades = list(grades.values())[user.quarter - 1]
                partial_data = _check_spec(spec, {'user': user, 'repo': repo, 'state': state, 'grades': grades,**kwargs})
                await command(m, **partial_data)
                if finish_state:
                    await state.clear()
            else:
                await state.set_state(ParamsGetter.GET_QUARTER)
                await state.update_data(command=command, spec=spec, finish_state=finish_state, orig_msg=m)
                quarters = '\n'.join(list(grades.keys()))
                await m.answer(f'какие оценки показать, нужно просто число, варианты:\n{quarters}')

        return quarter
    return force_quarter


@user_router.message(Command('get_grades'))
@grades_command(True)
async def get_grades(m: Message, grades):
    await m.answer(show_grades(grades))

@user_router.message(Command('clear_cache'))
async def clear_cache(m: Message, repo: Repo):
    await m.answer('очищаю сохранённые оценки')
    user = repo.get_user(m.from_user.id)
    user.cached_grades = None


@user_router.message(Command('update_cache'))
async def update_cache(m: Message, repo: Repo, state: FSMContext):
    await clear_cache(m, repo)
    await m.answer('обновляю сохранённые оценки')
    await cache_updated(m, repo, state)


@grades_command(True)
async def cache_updated(m: Message):
    await m.answer('оценки обновлены')


@user_router.message(Command('fix_grades'))
@grades_command(True)
async def fix_grades(m: Message, grades):
    await m.answer(show_fix_grades(grades))

@user_router.message(Command('version'))
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


@user_router.message(Command('new_version'))
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


@user_router.message(Command('help'))
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


@user_router.message(Command('change_quarter'))
async def change_quarter(m: Message, repo: Repo, state: FSMContext):
    user = repo.get_user(m.from_user.id)
    await state.set_state(ParamsGetter.GET_QUARTER)
    if user.cached_grades:
        grades = user.cached_grades
        quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(grades, 1)])
        await m.answer(f'выбери вариант, укажи просто число, варианты \n{quarters}')
    else:
        await m.answer('оценки не получены, вариантов нет, напиши просто число')


@user_router.message(Command('privacy_policy'))
async def privacy_policy(m: Message):
    await m.answer('это что-то похожее на политику конфиденциальности. '
                   'Если кто-то напишет нормальную политику конфиденциальности, я её обновлю.')
    await m.answer("Для получения оценок бот просит логин и пароль от журнала elschool. "
                   "Эти данные используются только для получения токена. "
                   "Этот токен используется для получения оценок. Никак ваши данные из него получить нельзя")


@user_router.message(Command('reregister'))
async def reregister(m: Message, state: FSMContext):
    await m.answer('сейчас можно изменить свой логин и пароль, сначала введи новый логин')
    await state.set_state(ParamsGetter.GET_LOGIN)


@user_router.message(Command('unregister'))
async def unregister(m: Message, repo: Repo):
    try:
        repo.remove_user(m.from_user.id)
    except KeyError:
        await m.answer('ээээ. Ты куда собрался. Тебя нет в моём списке')
    else:
        await m.answer('я тебя удалил.')


async def no_user(m: Message, repo: Repo):
    await m.answer('тебя нет в списке пользователей, сейчас добавлю')
    await user_start(m, repo)


@user_router.message()
@grades_command(True)
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


def register_user(dp: Dispatcher):
    dp.include_router(user_router)
    dp.message.register(no_user, RegisteredUserFilter(False))

