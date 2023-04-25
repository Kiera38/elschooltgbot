"""Обработка основных событий, совершённых пользователем."""
from typing import Union

from aiogram import Router, Dispatcher
from aiogram.filters import StateFilter, Command, Text
from aiogram.fsm.context import FSMContext
from aiogram.types import Message, CallbackQuery, InlineKeyboardMarkup

from tgbot.filters.command import CommandFilter
from tgbot.filters.user import RegisteredUserFilter
from tgbot.keyboards.user import main_keyboard, row_list_keyboard, cancel_keyboard, user_agree_keyboard, settings_keyboard
from tgbot.services.repository import Repo
from tgbot.states.user import Change, Page, Register

router = Router()
registered_router = Router()
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
    await state.update_data(jwtoken=jwtoken, password=m.text)
    await m.answer('удалось зарегистрироваться, данные введены правильно, теперь попробую получить оценки')
    grades, time, url = await repo.get_grades_userdata(jwtoken)
    quarters = list(grades)
    await state.update_data(url=url, quarters=list(grades.keys()))
    await state.set_state(Register.QUARTER)
    await m.answer(f'оценки получил за {time:.3f}с. Выбери какие оценки мне нужно показывать',
                   reply_markup=row_list_keyboard(quarters))


@router.message(StateFilter(Register.QUARTER), CommandFilter())
async def get_user_quarter(m: Message, state: FSMContext):
    """Когда пользователь при регистрации указал четверть, вызывается эта функция."""
    data = await state.get_data()
    if m.text in data['quarters']:
        await state.update_data(quarter=m.text)
        await state.set_state(Register.SAVE_DATA)
        await m.answer('регистрация завершена, но я спрошу ещё кое-что. Стоит ли мне сохранять логин и пароль, '
                       'чтобы когда elschool обновил некоторые данные, я мог их тоже обновить.'
                       'Обычно, это происходит раз в неделю. Ты всегда сможешь изменить это в настройках.',
                       reply_markup=user_agree_keyboard())
        await m.delete()
    else:
        quarters = list(data['quarters'].keys())
        await m.answer(f'тут немного не правильно написано, попробуй ещё раз', reply_markup=row_list_keyboard(quarters))
        return


@router.callback_query(StateFilter(Register.SAVE_DATA), Text('yes'))
async def save_user_data(query: CallbackQuery, state: FSMContext, repo: Repo):
    await query.message.answer('хорошо, я сохраню.', reply_markup=main_keyboard())
    data = await state.get_data()
    await repo.add_user(query.from_user.id, data['jwtoken'], data['quarter'],
                        url=data['url'], login=data['login'], password=data['password'])
    await state.clear()


@router.callback_query(StateFilter(Register.SAVE_DATA), Text('no'))
async def no_save_user_data(query: CallbackQuery, state: FSMContext, repo: Repo):
    await query.message.answer('я не буду сохранять логин и пароль. '
                               'При обновлениях данных я буду их спрашивать у тебя.', reply_markup=main_keyboard())
    data = await state.get_data()
    await repo.add_user(query.from_user.id, data['jwtoken'], data['quarter'], url=data['url'])
    await state.clear()


@router.message(Command('register'))
@router.callback_query(Text('register'), StateFilter(Page.SETTINGS))
async def register_user(message_or_query: Union[Message, CallbackQuery], state: FSMContext):
    """Регистрация """
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_reply_markup(cancel_keyboard())
        await message_or_query.answer()
        message = message_or_query.message
    else:
        message = message_or_query
    await state.set_state(Register.SHOW_PRIVACY_POLICY)
    await message.answer('надеюсь, ты согласен с политикой конфиденциальности.', reply_markup=user_agree_keyboard())
    await privacy_policy(message, state)


@router.callback_query(StateFilter(Register.SHOW_PRIVACY_POLICY), Text('yes'))
async def register_login(query: CallbackQuery, state: FSMContext):
    await state.set_state(Register.LOGIN)
    await query.message.edit_text('ну вот хорошо. Для начала введи логин.',
                                  reply_markup=InlineKeyboardMarkup(inline_keyboard=[]))


@router.callback_query(StateFilter(Register.SHOW_PRIVACY_POLICY), Text('no'))
async def exit_user(query: CallbackQuery, state: FSMContext):
    await state.clear()
    await query.message.answer('ну и не пользуйся, раз не согласен.', reply_markup=main_keyboard())


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


@router.message(Text('настройки'))
async def settings(message: Message, state: FSMContext, repo: Repo):
    await state.set_state(Page.SETTINGS)
    await message.answer('настройки', reply_markup=settings_keyboard(await repo.check_has_user(message.from_user.id)))


@router.message(Command('version'))
@router.callback_query(Text('version'), StateFilter(Page.SETTINGS))
async def version(message_or_query: Union[Message, CallbackQuery]):
    """Показать версию и список изменений."""
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.answer()
        message = message_or_query.message
    else:
        message = message_or_query
    await message.answer("""моя версия: 2.6.23.dev1 (обновление 4.0)
список изменений:
Бот теперь использует базу данных вместо обычного файла для хранения данных о пользователях.
Исправлена ошибка, из-за которой нельзя было использовать команды.
Исправлено множество других мелких ошибок.
""", reply_markup=main_keyboard())


@router.message(Command('version_comments'))
async def version_comments(m: Message):
    """Подробно показать список изменений."""
    await m.answer("""моя версия: 2.6.23.dev1 (обновление 4.0)

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


@registered_router.message(Command('change_quarter'))
@registered_router.callback_query(Text('change_quarter'), StateFilter(Page.SETTINGS))
async def change_quarter(message_or_query: Union[Message, CallbackQuery], repo: Repo, state: FSMContext):
    """Пользователь захотел изменить четверть из клавиатуры."""
    message = message_or_query.message if isinstance(message_or_query, CallbackQuery) else message_or_query
    await state.set_state(Change.QUARTER)
    quarters = await repo.get_quarters(message_or_query.from_user.id)
    await message.answer(f'выбери вариант', reply_markup=row_list_keyboard(quarters))


@router.message(Command('privacy_policy'))
@router.callback_query(Text('privacy_policy'), StateFilter(Page.SETTINGS))
async def privacy_policy(message_or_query: Union[Message, CallbackQuery], state: FSMContext):
    """Показать политику конфиденциальности."""
    message = message_or_query.message if isinstance(message_or_query, CallbackQuery) else message_or_query
    await message.answer("Для получения оценок бот просит логин и пароль от журнала elschool. "
                         "Эти данные используются только для получения токена. "
                         "Этот токен используется для получения оценок. Никак ваши данные из него получить нельзя."
                         "Есть возможность сохранить данные от аккаунта elschool. "
                         "Разработчик гарантирует, что данные никто смотреть не будет.",
                         reply_markup=main_keyboard())
    if isinstance(message_or_query, CallbackQuery):
        await state.clear()


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
    answer_message = await m.answer('проверка введённых данных, попытка регистрации')
    await m.delete()
    jwtoken = await repo.register_user(login, password)
    await repo.update_user_token(m.from_user.id, jwtoken)
    await state.clear()
    await answer_message.edit_text('удалось зарегистрироваться, данные введены правильно. Попробую получить оценки')
    grades, time = await repo.get_grades(m.from_user.id)
    await answer_message.edit_text(f'удалось получить оценки за {time:.3f} секунд.')



@registered_router.message(Command('change_data'))
@registered_router.callback_query(Text('change_data'), StateFilter(Page.SETTINGS))
async def change_data(message_or_query: Union[Message, CallbackQuery], state: FSMContext):
    """Пользователь захотел изменить данные с помощью кнопки на клавиатуре."""
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_reply_markup(cancel_keyboard())
        message = message_or_query.message
    else:
        message = message_or_query
    await message.answer('сейчас можно изменить свой логин и пароль, сначала введи новый логин')
    await state.set_state(Change.LOGIN)


@registered_router.message(Command('remove_data'))
@registered_router.callback_query(Text('remove_data'), StateFilter(Page.SETTINGS))
async def remove_data(message_or_query: CallbackQuery, repo: Repo, state: FSMContext):
    """Пользователь захотел изменить данные с помощью кнопки на клавиатуре."""
    if isinstance(message_or_query, CallbackQuery):
        await message_or_query.message.edit_reply_markup(cancel_keyboard())
        message = message_or_query.message
    else:
        message = message_or_query
    await repo.remove_user(message_or_query.from_user.id)
    await message.answer('я тебя удалил.', reply_markup=main_keyboard())
    await state.clear()


@router.message(RegisteredUserFilter(False))
async def no_user(m: Message):
    """Пользователь не зарегистрирован,
    но захотел использовать функцию для зарегистрированных пользователей\
    """
    await m.answer('тебя нет в списке пользователей, попробуй зарегистрироваться')


@not_command_router.message(CommandFilter(True))
async def text_is_command(message: Message):
    """В случае, если пользователь написал команду вместо того,
    что его попросили, будет вызываться эта функция.
    """
    await message.answer('по моему ты написал одну из моих команд. Тебя что попросили написать?')


def register_user_handlers(dp: Dispatcher):
    """Настройка роутеров."""
    dp.include_router(router)
    registered_router.message.filter(RegisteredUserFilter(True))
    router.include_router(registered_router)
    router.include_router(not_command_router)