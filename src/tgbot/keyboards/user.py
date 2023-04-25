"""Клавиатуры для пользователя."""
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    """Основная клавиатура."""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='оценки')],
        [KeyboardButton(text='настройки')]
    ], resize_keyboard=True)


def grades_keyboard(show_back=False):
    """Клавиатура для страницы оценки."""
    keyboard = [
        [InlineKeyboardButton(text='получить', callback_data='get_grades')],
        [InlineKeyboardButton(text='исправить', callback_data='fix_grades')],
    ]
    if show_back:
        keyboard.append([InlineKeyboardButton(text='назад', callback_data='back_main')])
    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def pick_grades_keyboard(lessons=()):
    """Клавиатура для выбора конкретного урока."""
    buttons = []

    if not lessons:
        return None
    if len(lessons) == 1:
        buttons.append([KeyboardButton(text=lessons[0])])
        return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)
    if len(lessons) < 10:
        for lesson in lessons:
            buttons.append([KeyboardButton(text=lesson)])
        return ReplyKeyboardMarkup(keyboard=buttons)
    for lesson1, lesson2 in zip(lessons[::2], lessons[1::2]):
        buttons.append([KeyboardButton(text=lesson1), KeyboardButton(text=lesson2)])
    return ReplyKeyboardMarkup(keyboard=buttons)


def pick_grades_inline_keyboard():
    """Inline клавиатура, которая показывается при выборе конкретного урока."""
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='все', callback_data='all_grades')],
        [InlineKeyboardButton(text='назад', callback_data='back_grades'),
         InlineKeyboardButton(text='отмена', callback_data='cancel')]
    ])


def cancel_keyboard():
    """Клавиатура для показа отмены действия."""
    return InlineKeyboardMarkup(inline_keyboard=[[
        InlineKeyboardButton(text='отмена', callback_data='cancel')
    ]])


def row_list_keyboard(lst):
    """Клавиатура для показа списка по горизонтали."""
    return ReplyKeyboardMarkup(keyboard=[[KeyboardButton(text=text) for text in lst]], resize_keyboard=True)


def settings_keyboard(registered=False):
    if registered:
        register_buttons = [
            InlineKeyboardButton(text='изменить данные', callback_data='change_data'),
            InlineKeyboardButton(text='удалить данные', callback_data='remove_data')
        ]
    else:
        register_buttons = [InlineKeyboardButton(text='регистрация', callback_data='register')]

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='политика конфиденциальности', callback_data='privacy_policy')],
        register_buttons,
        [InlineKeyboardButton(text='версия', callback_data='version'),
         InlineKeyboardButton(text='изменить четверть', callback_data='change_quarter')],
    ])

def user_agree_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='да', callback_data='yes'), InlineKeyboardButton(text='нет', callback_data='no')]
    ])