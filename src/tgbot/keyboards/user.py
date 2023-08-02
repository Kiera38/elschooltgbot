"""Клавиатуры для пользователя."""
import calendar
import datetime

from aiogram.types import ReplyKeyboardMarkup, KeyboardButton, InlineKeyboardMarkup, InlineKeyboardButton


def main_keyboard():
    """Основная клавиатура."""
    return ReplyKeyboardMarkup(keyboard=[
        [KeyboardButton(text='оценки')],
        [KeyboardButton(text='настройки')]
    ], resize_keyboard=True)


def grades_keyboard(all=True, pick=False, summary=False, detail=False, lesson_date=False, date=False,
                    five=False, four=False, three=False, two=False):
    """Клавиатура для страницы оценки."""
    all_key = '✓ все' if all else 'все'
    pick_key = '✓ выбрать из списка' if pick else 'выбрать из списка'
    summary_key = '✓ кратко' if summary else 'кратко'
    detail_key = '✓ подробно' if detail else 'подробно'
    lesson_date_key = '✓ дата оценки' if lesson_date else 'дата оценки'
    date_key = '✓ дата проставления' if date else 'дата проставления'
    five_key = '✓ 5' if five else '5'
    four_key = '✓ 4' if four else '4'
    three_key = '✓ 3' if three else '3'
    two_key = '✓ 2' if two else '2'
    if summary:
        return InlineKeyboardMarkup(inline_keyboard=[
            [InlineKeyboardButton(text='показать', callback_data='show')],
            [InlineKeyboardButton(text=summary_key, callback_data='summary'),
             InlineKeyboardButton(text=detail_key, callback_data='detail')],
            [InlineKeyboardButton(text=five_key, callback_data='mark5'),
             InlineKeyboardButton(text=four_key, callback_data='mark4'),
             InlineKeyboardButton(text=three_key, callback_data='mark3'),
             InlineKeyboardButton(text=two_key, callback_data='mark2')]
        ])
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='показать', callback_data='show')],

        [InlineKeyboardButton(text=all_key, callback_data='all'),
         InlineKeyboardButton(text=pick_key, callback_data='pick')],

        [InlineKeyboardButton(text=summary_key, callback_data='summary'),
         InlineKeyboardButton(text=detail_key, callback_data='detail')],

        [InlineKeyboardButton(text=lesson_date_key, callback_data='lesson_date'),
         InlineKeyboardButton(text=date_key, callback_data='date')],

        [InlineKeyboardButton(text=five_key, callback_data='mark5'),
         InlineKeyboardButton(text=four_key, callback_data='mark4'),
         InlineKeyboardButton(text=three_key, callback_data='mark3'),
         InlineKeyboardButton(text=two_key, callback_data='mark2')]
    ])


def pick_lessons_keyboard(lessons):
    """Inline клавиатура, которая показывается при выборе конкретного урока."""
    buttons = [[InlineKeyboardButton(text=f'✓ {lesson1}' if picked1 else lesson1, callback_data=str(i * 2)),
                InlineKeyboardButton(text=f'✓ {lesson2}' if picked2 else lesson2, callback_data=str(i*2 + 1))]
               for i, ((picked1, lesson1), (picked2, lesson2)) in enumerate(zip(lessons[::2], lessons[1::2]))]
    return InlineKeyboardMarkup(inline_keyboard=[
        *buttons,
        [InlineKeyboardButton(text='назад', callback_data='back'),
         InlineKeyboardButton(text='отмена', callback_data='cancel')]
    ])


month_names = ['январь', 'февраль', 'март', 'апрель', 'май', 'июнь',
               'июль', 'август', 'сентябрь', 'октябрь', 'ноябрь', 'декабрь']

def pick_day_keyboard(year, month, picked_dates=(), current_week=False, current_month=False):
    month_calendar = calendar.monthcalendar(year, month)
    buttons = [
        [InlineKeyboardButton(text=f'✓ {day}' if datetime.date(year, month, day) in picked_dates else str(day),
                              callback_data=f'day{year}.{month}.{day}') for day in week] for week in month_calendar
    ]
    current_week_key = '✓ текущая неделя' if current_week else 'текущая неделя'
    current_month_key = '✓ текущий месяц' if current_month else 'текущий месяц'
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='<<', callback_data='prev_month'),
         InlineKeyboardButton(text=f'{month_names[month]} {year}', callback_data='pick_month'),
         InlineKeyboardButton(text='>>', callback_data='next_month')],
        [InlineKeyboardButton(text=current_week_key, callback_data='current_week'),
         InlineKeyboardButton(text=current_month_key, callback_data='current_month')],
        *buttons,
        [InlineKeyboardButton(text='назад', callback_data='back'),
         InlineKeyboardButton(text='отмена', callback_data='cancel')]
    ])


def pick_month_keyboard(year, picked_month):
    months = month_names.copy()
    months[picked_month] = f'✓ {months[picked_month]}'

    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='<<', callback_data='prev_year'),
         InlineKeyboardButton(text=str(year), callback_data='pick_year'),
         InlineKeyboardButton(text='>>', callback_data='next_year')],
        [InlineKeyboardButton(text=months[0], callback_data='january'),
         InlineKeyboardButton(text=months[1], callback_data='february'),
         InlineKeyboardButton(text=months[2], callback_data='march'),
         InlineKeyboardButton(text=months[3], callback_data='april')],
        [InlineKeyboardButton(text=months[4], callback_data='may'),
         InlineKeyboardButton(text=months[5], callback_data='june'),
         InlineKeyboardButton(text=months[6], callback_data='july'),
         InlineKeyboardButton(text=months[7], callback_data='august')],
        [InlineKeyboardButton(text=months[8], callback_data='september'),
         InlineKeyboardButton(text=months[9], callback_data='october'),
         InlineKeyboardButton(text=months[10], callback_data='november'),
         InlineKeyboardButton(text=months[11], callback_data='december')]
    ])


def pick_year_keyboard(year):
    buttons = [[InlineKeyboardButton(text=str(row_year), callback_data=f'year{row_year}')
                for row_year in range(column_year-1, column_year+2)] for column_year in range(year-4, year+5, 3)]
    return InlineKeyboardMarkup(inline_keyboard=buttons)


def after_show_grades_keyboard():
    return InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text='исправить', callback_data='fix')]
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


