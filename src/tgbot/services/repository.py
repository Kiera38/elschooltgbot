"""Основная логика взаимодействия с elschool."""
import logging
import time
from pprint import pprint
from typing import List

import aiohttp
import aiosqlite
from bs4 import BeautifulSoup

from tgbot.models.user import User

logger = logging.getLogger(__name__)


class Repo:
    """Класс для управления всеми пользователями."""
    def __init__(self, db: aiosqlite.Connection):
        self.db = db
        self.elschool_repo = ElschoolRepo()

    async def add_user(self, user_id, user: User) -> None:
        """Добавить нового пользователя."""
        async with self.db.execute('INSERT INTO Users VALUES (?, ?, ?, ?, ?, ?)',
                                   (user_id, user.jwtoken, user.quarter, user.role.value, user.url, user.last_cache)):
            logger.info(f'пользователь добавлен {user}')
        await self.db.commit()

    async def list_users(self) -> List[User]:
        """Список всех пользователей"""
        async with self.db.execute('SELECT jwtoken, quarter, role, url, last_cache FROM Users') as cursor:
            return list(await cursor.fetchall())

    async def user_ids(self):
        """Список всех id пользователей"""
        async with self.db.execute('SELECT id FROM users') as cursor:
            return list(await cursor.fetchall())

    async def get_user(self, user_id):
        """Получить конкретного пользователя."""
        async with self.db.execute('SELECT jwtoken, quarter, role, url, last_cache FROM Users WHERE id = ?',
                                   (user_id,)) as cursor:
            return await cursor.fetchone()

    async def remove_user(self, user_id):
        """Удалить пользователя."""
        await self.db.execute('DELETE FROM Users WHERE id = ?', (user_id,))
        await self.db.commit()

    async def register_user(self, login, password):
        """Регистрация нового пользователя, возвращает его токен."""
        return await self.elschool_repo.register(login, password)

    async def get_grades_userdata(self, jwtoken, url=None):
        """Получить оценки по токену."""
        start = time.time()
        logger.info('получаем новые оценки')
        if url:
            grades = await self.elschool_repo.get_grades(jwtoken, url)
        else:
            grades, url = await self.elschool_repo.get_grades_and_url(jwtoken)
        end = time.time()
        logger.info(f'получены новые оценки за {end - start}')
        return grades, end - start, url

    async def get_grades(self, user_id):
        """Получить оценки для пользователя."""
        async with self.db.cursor() as cursor:
            await cursor.execute('SELECT last_cache, quarter, jwtoken, url FROM Users WHERE id=?', (user_id,))
            last_cache, quarter, jwtoken, url = await cursor.fetchone()
            if time.time() - last_cache < 3600:
                await cursor.execute('SELECT name, date, value FROM QuarterLessonMarks WHERE user_id=? AND quarter=?',
                                     (user_id, quarter))
                cached_grades = {}
                async for name, date, value in cursor:
                    if name not in cached_grades:
                        cached_grades[name] = []
                    print(value)
                    if value != 0:
                        cached_grades[name].append({
                            'date': date,
                            'value': value
                        })
                return cached_grades, 0

            return await self._update_cache(cursor, user_id, quarter, jwtoken, url)

    async def has_user(self, user_id):
        """Существует ли пользователь с определённым id"""
        async with self.db.execute('SELECT EXISTS(SELECT id FROM Users WHERE id=?)', (user_id,)) as cursor:
            return bool((await cursor.fetchone())[0])

    async def update_user_token(self, user_id, jwtoken):
        await self.db.execute('UPDATE Users SET jwtoken = ?, last_cache = 0 WHERE id = ?',
                                   (jwtoken, user_id))
        await self.db.commit()

    async def check_has_user(self, user_id):
        async with self.db.execute('SELECT EXISTS(SELECT id FROM Users WHERE id=? AND jwtoken IS NOT NULL)',
                                   (user_id,)) as cursor:
            return bool((await cursor.fetchone())[0])

    async def clear_user_cache(self, user_id):
        await self.db.execute('DELETE FROM QuarterLessonMarks WHERE user_id = :user_id AND quarter = '
                              '  (SELECT quarter FROM Users WHERE id = :user_id)', {'user_id': user_id})
        await self.db.execute('UPDATE Users SET last_cache = 0 WHERE id = ?', (user_id,))
        await self.db.commit()

    async def update_cache(self, user_id):
        async with self.db.cursor() as cursor:
            await cursor.execute('SELECT quarter, jwtoken, url FROM Users WHERE id=?', (user_id,))
            quarter, jwtoken, url = await cursor.fetchone()
            return await self._update_cache(cursor, user_id, quarter, jwtoken, url)

    async def _update_cache(self, cursor, user_id, quarter, jwtoken, url):
        grades, get_time, url = await self.get_grades_userdata(jwtoken, url)
        quarter_grades = grades[quarter]
        await cursor.execute('UPDATE Users SET last_cache = ? WHERE id = ?', (time.time(), user_id))
        await cursor.execute('DELETE FROM QuarterLessonMarks WHERE user_id = ? AND quarter = ?', (user_id, quarter))
        pprint(quarter_grades)
        for name, values in quarter_grades.items():
            if not values:
                quarter_grades[name].append({'date': '--.--.----', 'value': 0})
        await cursor.executemany('INSERT INTO QuarterLessonMarks VALUES (?, ?, ?, ?, ?)',
                                 [(user_id, quarter, name, value['date'], value['value'])
                                  for name, values in quarter_grades.items() for value in values])
        await self.db.commit()
        return grades[quarter], get_time

    async def get_quarters(self, user_id):
        async with self.db.execute('SELECT DISTINCT quarter FROM QuarterLessonMarks WHERE user_id = ?',
                                   (user_id,)) as cursor:
            return [row[0] async for row in cursor]

    async def set_user_quarter(self, user_id, quarter):
        await self.db.execute('UPDATE Users SET quarter = ? WHERE id = ?' , (quarter, user_id))
        await self.db.commit()

    async def get_user_lessons(self, user_id):
        async with self.db.execute('SELECT DISTINCT name FROM QuarterLessonMarks WHERE user_id = :user_id AND quarter = '
                                   '    (SELECT quarter FROM Users WHERE id = :user_id)', {'user_id': user_id}) as cursor:
            return [row[0] async for row in cursor]



class ElschoolRepo:
    """Класс для взаимодействия с сервером elschool"""

    async def _get_url(self, session):
        response = await session.get(f'https://elschool.ru/users/diaries', ssl=False)
        html = await response.text()
        bs = BeautifulSoup(html, 'html.parser')
        return 'https://elschool.ru/users/diaries/' + bs.find('a', text='Табель')['href']

    async def get_grades(self, jwtoken, url):
        """Получить оценки с сервера."""
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            return await self._get_grades(url, session)

    async def _get_grades(self, url, session):
        response = await session.get(url, ssl=False)
        if not response.ok:
            raise NoDataException(f"не удалось получить оценки с сервера, код ошибки {response.status}")
        if not str(response.url).startswith(url):
            raise NoDataException("не удалось получить оценки с сервера. Обычно такое происходит, "
                                  "если не правильно указан логин или пароль. "
                                  "Попробуй изменить логин или пароль")
        return self._parse_grades(await response.text())

    async def get_grades_and_url(self, jwtoken):
        """Получить оценки и адрес страницы пользователя.
        Это эффективней, чем получение оценок и адреса по отдельности.
        """
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            url = await self._get_url(session)
            grades = await self._get_grades(url, session)
            return grades, url

    async def register(self, login, password):
        """Регистрация пользователя по логину и паролю, возвращает токен."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'login': login,
                'password': password
            }
            response = await session.post(f'https://elschool.ru/Logon/Index', params=payload, ssl=False)
            logger.info(f'register response :{response}')
            if not response.ok:
                raise NotRegisteredException(f"Не удалось выполнить регистрацию, код сервера {response.status}")

            if not str(response.url).startswith('https://elschool.ru/users/privateoffice'):
                raise NotRegisteredException("Не удалась регистрация. Обычно такое происходит, "
                                             "если не правильно указан логин или пароль. "
                                             "Попробуй изменить данные от аккаунта", login=login, password=password)

            jwtoken = session.cookie_jar.filter_cookies('https://elschool.ru').get('JWToken')
            logger.info(f'получен jwtoken: {jwtoken}')
            if not jwtoken or not jwtoken.value:
                raise NotRegisteredException('Регистрация удалась, но не найден токен. '
                                             'Я пока не знаю, почему это могло произойти.'
                                             'Скорее всего изменился способ работы регистрации у elschool.'
                                             'Эта проверка существует потому что такое может произойти.'
                                             'Это сообщение станет более информативным, когда я его получу.')
            return jwtoken.value

    @staticmethod
    def _parse_grades(html):
        if not html:
            raise NoDataException('данные не получены')
        try:
            grades = {}
            bs = BeautifulSoup(html, 'html.parser')
            quarters = [th.text.strip() for th in bs.find('thead').find_all('th') if not th.attrs]
            tbody = bs.find('tbody')
            if tbody:
                for quarter_index in range(len(quarters)):
                    quarter_grades = {}
                    for lesson in tbody.find_all('tr'):
                        lesson_name = lesson.find('td', class_='grades-lesson')
                        lesson_grades = lesson.find_all('td', class_='grades-marks')
                        grades_list = []
                        for grade in lesson_grades[quarter_index].find_all('span', class_='mark-span'):
                            grades_list.append({
                                'value': int(grade.text),
                                'date': '\n'.join(grade['data-popover-content'].split('<p>'))
                            })
                        quarter_grades[lesson_name.text] = grades_list
                    grades[quarters[quarter_index]] = quarter_grades
        except Exception:
            raise NoDataException('данные получены в странном формате. Такое обычно происходит, если сайт перенаправляет на другую страницу.')
        return grades


class NotRegisteredException(Exception):
    """Исключение, сообщающее о том, что регистрация не удалась."""
    def __init__(self, *args, login=None, password=None):
        super().__init__(*args)
        self.login = login
        self.password = password


class NoDataException(Exception):
    """Исключение, сообщающее о том, что не удалось получить некоторые данные с сервера."""
    pass