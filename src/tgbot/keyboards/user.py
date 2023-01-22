from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='оценки')],
        [KeyboardButton(text='регистрация'), KeyboardButton(text='версия')],
        [KeyboardButton(text='политика конфиденциальности')]
    ], resize_keyboard=True)


def grades_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='получить', callback_data='get_grades')],
        [InlineKeyboardButton(text='исправить', callback_data='fix_grades')],
        [InlineKeyboardButton(text='изменить четверть', callback_data='change_quarter')],
        [InlineKeyboardButton(text='назад', callback_data='grades_back')]
    ])


def pick_grades_keyboard(show_all=True, lessons=()):
    buttons = [[KeyboardButton(text='все')]] if show_all else []

    def add_cancel():
        buttons.append([KeyboardButton(text='назад'), KeyboardButton(text='отменить')])
        return buttons

    if not lessons:
        return ReplyKeyboardMarkup(keyboard=add_cancel(), resize_keyboard=True)
    if len(lessons) == 1:
        buttons.append([KeyboardButton(text=lessons[0])])
        return ReplyKeyboardMarkup(keyboard=add_cancel(), resize_keyboard=True)
    if len(lessons) < 10:
        for lesson in lessons:
            buttons.append([KeyboardButton(text=lesson)])
        return ReplyKeyboardMarkup(keyboard=add_cancel())
    for lesson1, lesson2 in zip(lessons[::2], lessons[1::2]):
        buttons.append([KeyboardButton(text=lesson1), KeyboardButton(text=lesson2)])
    return ReplyKeyboardMarkup(keyboard=add_cancel())

def register_keyboard(registered=False):
    if not registered:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='зарегистрироваться', callback_data='register')]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='изменить данные', callback_data='change_data')],
        [InlineKeyboardButton(text='удалить данные', callback_data='remove_data')]
    ])

