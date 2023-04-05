import pickle
import sqlite3

import tgbot.config

db_file = tgbot.config.load_config('bot.ini').data.db_file
db = sqlite3.connect(db_file)
cursor = db.cursor()
cursor.execute('CREATE TABLE IF NOT EXISTS Users ('
               '   id INTEGER PRIMARY KEY,'
               '   jwtoken TEXT,'
               '   quarter TEXT,'
               '   role TEXT,'
               '   url TEXT,'
               '   last_cache REAL)')
print('создана таблица Users')
cursor.execute('CREATE TABLE IF NOT EXISTS QuarterLessonMarks ('
               '   user_id INTEGER,'
               '   quarter TEXT NOT NULL,'
               '   name TEXT NOT NULL,'
               '   date TEXT NOT NULL,'
               '   value INTEGER NOT NULL,'
               '   FOREIGN KEY (user_id) REFERENCES Users (id) ON DELETE CASCADE)')
print('создана таблица QuarterUserMarks')
with open('users.pkl', 'rb') as f:
    users = pickle.load(f)

print('добавляются данные о пользователях')
users_data = []
marks_data = []
for user_id, user in users.items():
    users_data.append((user_id, user.jwtoken, user.quarter, user.role.value, user.url, user.last_cache))
    user_marks_data = [(user_id, quarter, name, '\n'.join(value['date']), value['grade'])
                        for quarter, grades in user.cached_grades.items()
                        for name, values in grades.items() for value in values] if user.cached_grades is not None else []
    marks_data += user_marks_data
    print(f'пользователь с id {user_id} обработан, {users_data[-1]}, {len(user_marks_data)} оценок')

print('все пользователи обработаны')
cursor.executemany('INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?)', users_data)
print(f'все пользователи добавлены,{len(users_data)}')
cursor.executemany('INSERT INTO QuarterLessonMarks VALUES (?, ?, ?, ?, ?)', marks_data)
print(f'все оценки добавлены, {len(marks_data)}')
db.commit()
print('подтверждены действия с базой данных')
