from aiogram import Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.types import Message

from tgbot.handlers.utils import show_grades, lower_keys, show_grades_for_lesson, show_fix_grades
from tgbot.models.user import User
from tgbot.services.repository import Repo
from tgbot.states.user import ParamsGetter


async def is_command(m: Message):
    if m.text in ["/get_grades",
                  "/fix_grades",
                  '/start',
                  '/help',
                  '/version',
                  '/save_params',
                  '/remove_params',
                  '/remove_memory_params'
                  '/change_quarter',
                  '/cancel',
                  "/update_cache",
                  '/admin_scope',
                  '/send_message',
                  '/users_count']:
        await m.answer('по моему ты написал одну из моих команд. Тебя что попросили написать?')
        return True
    return False


async def command_with_params(m: Message, command, repo: Repo, state: FSMContext):
    await state.update_data(command=command, message=m)
    user = repo.get_user(m.from_id)
    if not user.has_cashed_grades:
        if not user.login:
            await state.set_state(ParamsGetter.GET_LOGIN)
            await m.answer('для продолжения работы потребуется ввести свой логин от elschool')
            return
        if not user.password:
            await state.set_state(ParamsGetter.GET_PASSWORD)
            await m.answer('для продолжения работы потребуется ввести свой пароль от elschool')
            return
    await command(m, repo, state, user)


async def grades_command(m: Message, command, repo: Repo, state: FSMContext):
    await state.update_data(grades_command=command)
    await command_with_params(m, grades_cmd, repo, state)


async def grades_cmd(m: Message, repo: Repo, state: FSMContext, user: User):
    if user.has_cashed_grades:
        await m.answer('есть сохранённые оценки, использую их')
    else:
        await m.answer('оценки не сохранены, начинаю получать новые оценки, пожалуйста подожди')
    grades, time = await repo.get_grades(user)
    if time:
        await m.answer(f'оценки получены за {time:.2} c')
    if not user.quarter:
        await state.set_state(ParamsGetter.GET_QUARTER)
        quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(grades, 1)])
        await m.answer(f'какие оценки показать, укажи просто число, варианты \n{quarters}')
        return
    command = (await state.get_data())['grades_command']
    await command(m, repo, state, list(grades.values())[user.quarter - 1])
    await state.finish()


async def get_user_login(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    user = repo.get_user(m.from_id)
    user.login = m.text
    await m.delete()
    await m.answer('логин сохранён')
    data = await state.get_data()
    await command_with_params(data['message'], data['command'], repo, state)


async def get_user_password(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    repo.set_user_password(m.from_id, m.text)
    await m.delete()
    await m.answer('пароль сохранён')
    data = await state.get_data()
    await command_with_params(data['message'], data['command'], repo, state)


async def get_user_quarter(m: Message, repo: Repo, state: FSMContext):
    if await is_command(m):
        return
    if not m.text.isdigit():
        await m.answer(f'должно быть число, например 1, не {m.text}')
    else:
        user = repo.get_user(m.from_id)
        user.quarter = int(m.text)
        await m.answer('сохранено')
        await m.delete()
        data = await state.get_data()
        if data:
            await grades_cmd(data['message'], repo, state, user)
        else:
            await state.finish()


async def user_start(m: Message):
    await m.reply("привет, я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить\n"
                  "чтобы узнать как пользоваться используй /help")


async def get_grades(m: Message, repo: Repo, state: FSMContext):
    await grades_command(m, send_grades, repo, state)


async def send_grades(m: Message, repo: Repo, state: FSMContext, grades):
    await m.answer(show_grades(grades))


async def grades_one_lesson(m: Message, repo: Repo, state: FSMContext):
    await grades_command(m, send_grades_one_lesson, repo, state)


async def send_grades_one_lesson(m: Message, repo: Repo, state: FSMContext, grades):
    grades = lower_keys(grades)
    lesson = m.text.lower()
    if lesson not in grades:
        await m.answer('кажется, тебе хотелось не этого получить')
        return
    await m.answer(show_grades_for_lesson(grades[lesson]))


async def clear_cache(m: Message, repo: Repo):
    await m.answer('очищаю сохранённые оценки')
    user = repo.get_user(m.from_user.id)
    user.cached_grades = None


async def update_cache(m: Message, repo: Repo, state: FSMContext):
    await clear_cache(m, repo)
    await m.answer('обновляю сохранённые оценки')
    await grades_command(m, cache_updated, repo, state)


async def cache_updated(m: Message, repo: Repo, state: FSMContext, grades):
    await m.answer('оценки обновлены')
    await state.finish()


async def fix_grades(m: Message, repo: Repo, state: FSMContext):
    await grades_command(m, send_fix_grades, repo, state)


async def send_fix_grades(m, repo, state, grades):
    await m.answer(show_fix_grades(grades))


async def save_params_cmd(m: Message, repo: Repo, state: FSMContext):
    await m.answer('надеюсь ты ознакомлен с моей политикой конфиденциальности.')
    await command_with_params(m, save_params, repo, state)


async def save_params(m: Message, repo: Repo, state: FSMContext, user):
    user.save_params = True
    await m.answer('параметры будут сохраняться при перезагрузках бота')
    await state.finish()


async def remove_params(m: Message, repo: Repo):
    user = repo.get_user(m.from_id)
    user.save_params = False
    await m.answer('твои параметры больше не будут сохранятся при перезагрузках бота')


async def remove_memory_params(m: Message, repo: Repo):
    user = repo.get_user(m.from_id)
    user.login = None
    user.password = None
    user.quarter = None
    await m.answer('твои данные сброшены')


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


async def new_version(m: Message):
    await m.answer("""В следующем обновлении:
    
Взаимодействие с ботом через кнопки (через команды также можно) 
Нормальная регистрация (разобрался, как можно сделать)
переход на aiogram 3.x
Некоторые мелкие изменения
Возможно база данных вместо обычного файла для хранения данных пользователей (в одном из обновлений это произойдёт, возможно в этом)
""")


async def help(m: Message):
    await m.answer("""я могу присылать тебе оценки из электронного журнала elschool и подсказывать как их испавить

команды:
/get_grades - получить все оценки
/fix_grades - получить все оценки и как можно их исправить
/help - показать это сообщение
/version - показать версию и список изменений в последнем обновлении
/save_params - сохранять параметры между перезагрузками бота
/remove_params - перестать сохранять параметры между перезагрузками бота
/remove_memory_params - удалить все данные о пользователе (придётся вводить заново)
/privacy_policy - посмотреть политику конфиденциальности 
/cancel - сбросить текущее состояние
/update_cache - обновить сохранённые оценки. Для скорости и некоторых других функций оценки хранятся в течение 1 часа, если по какой-то причине нужно их обновить можно использовать эту команду

Команды, которые получают оценки могут потребовать логин и пароль. Доступа к этим данным у разработчика нет. Всё это описано в политике конфиденциальности. 

Также, если просто написать название урока можно получить подробную информацию по каждой оценке""")


async def cancel(m: Message, state: FSMContext):
    await state.reset_state()
    await m.answer('текущее состояние сброшено')


async def change_quarter(m: Message, repo: Repo, state: FSMContext):
    user = repo.get_user(m.from_id)
    await state.set_state(ParamsGetter.GET_QUARTER)
    if user.cached_grades:
        grades = user.cached_grades
        quarters = '\n'.join([f'{i}). {quarter}' for i, quarter in enumerate(grades, 1)])
        await m.answer(f'выбери вариант, укажи просто число, варианты \n{quarters}')
    else:
        await m.answer('оценки не получены, вариантов нет напиши просто число')


async def privacy_policy(m: Message):
    await m.answer("""
Бот может работать без сбора данных, но для выполнения запросов на сервер elschool потребуется ввести логин и пароль. После ввода логина и пароля эти данные хранятся в оперативной памяти. В этом случае доступа к этим данным у разработчика нет.
Чтобы не потерять данные между перезагрузками бота их можно сохранить на сервере. У разработчика нет прямого доступа к этм данным, но возможность их посмотреть все равно существует. Эту функцию нужно включать отдельно, по умолчанию она не включена.""")


def register_user(dp: Dispatcher):
    dp.register_message_handler(cancel, commands='cancel', state='*')
    dp.register_message_handler(user_start, commands=["start"], state="*")

    dp.register_message_handler(save_params_cmd, state=None, commands='save_params')
    dp.register_message_handler(remove_params, state=None, commands='remove_params')
    dp.register_message_handler(remove_memory_params, state=None, commands='remove_memory_params')

    dp.register_message_handler(get_user_login, state=ParamsGetter.GET_LOGIN)
    dp.register_message_handler(get_user_password, state=ParamsGetter.GET_PASSWORD)
    dp.register_message_handler(get_user_quarter, state=ParamsGetter.GET_QUARTER)

    dp.register_message_handler(get_grades, state=None, commands="get_grades", is_user=True)
    dp.register_message_handler(fix_grades, commands='fix_grades', is_user=True)

    dp.register_message_handler(version, state='*', commands='version')
    dp.register_message_handler(help, state='*', commands='help')
    dp.register_message_handler(privacy_policy, state='*', commands='privacy_policy')
    dp.register_message_handler(update_cache, commands="update_cache", is_user=True, state=None)

    dp.register_message_handler(change_quarter, commands='change_quarter', is_user=True, state=None)

    dp.register_message_handler(grades_one_lesson, state=None, is_user=True)

