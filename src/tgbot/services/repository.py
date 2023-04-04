"""Основная логика взаимодействия с elschool."""
import datetime
import logging
import time
from typing import List, Dict

import aiohttp
from bs4 import BeautifulSoup

from tgbot.models.user import User

logger = logging.getLogger(__name__)


def schedule_from_day(day):
    return [lesson['name'] for lesson in day['lessons']]


def homework_from_day(day):
    return {lesson['name']: lesson['homework'] for lesson in day['lessons']}


def time_schedule_from_day(day):
    return [lesson['time'] for lesson in day['lessons']]


def marks_from_day(day):
    return [lesson['marks'] for lesson in day['lessons']]


class Repo:
    """Класс для управления всеми пользователями."""
    def __init__(self, users, classes):
        self.users: Dict[int, User] = users
        self.classes = classes
        self.elschool_repo = ElschoolRepo()

    def add_user(self, user_id, user: User) -> None:
        """Добавить нового пользователя."""
        self.users[user_id] = user
        logger.info(f'пользователь добавлен {user}')

    def list_users(self) -> List[User]:
        """Список всех пользователей"""
        return list(self.users.values())

    def user_ids(self):
        """Список всех id пользователей"""
        return list(self.users.keys())

    def get_user(self, user_id):
        """Получить конкретного пользователя."""
        return self.users.get(user_id)

    def remove_user(self, user_id):
        """Удалить пользователя."""
        del self.users[user_id]

    async def register_user(self, login, password):
        """Регистрация нового пользователя, возвращает его токен."""
        return await self.elschool_repo.register(login, password)

    async def get_grades_userdata(self, jwtoken, url_base=None):
        """Получить оценки по токену."""
        start = time.time()
        logger.info('получаем новые оценки')
        if url_base:
            grades = await self.elschool_repo.get_grades(jwtoken, url_base)
        else:
            grades, url_base = await self.elschool_repo.get_grades_and_url_base(jwtoken)
        end = time.time()
        logger.info(f'получены новые оценки за {end - start}')
        return grades, end - start, url_base

    async def get_grades(self, user):
        """Получить оценки для пользователя."""
        if user.has_cached_grades:
            logger.info('используются кешированные оценки')
            return user.cached_grades, 0
        url = user.url
        if url.startswith('https://elschool.ru/users/diaries/grades'):
            url = url[len('https://elschool.ru/users/diaries/grades'):]
        grades, time, user.url = await self.get_grades_userdata(user.jwtoken, url)
        user.update_cache(grades)
        return grades, time

    def get_class(self, name):
        return self.classes.get(name)

    def add_class(self, name, cls):
        self.classes[name] = cls

    def remove_class(self, name):
        del self.classes[name]

    async def get_schedule(self, user: User, date=None):
        if date is None:
            date = datetime.date.today()
        if day := user.cls.find_day(date):
            try:
                return schedule_from_day(day)
            except KeyError:
                pass
        if day := user.find_day(date):
            try:
                return schedule_from_day(day)
            except KeyError:
                pass
        if user.url.startswith('https://elschool.ru/users/diaries/grades'):
            user.url = user.url[len('https://elschool.ru/users/diaries/grades'):]
        days = await self.elschool_repo.get_days(user.jwtoken, user.url, date.year, date.isocalendar()[1])
        user.update_days(days)
        return schedule_from_day(days[date.weekday()])

    async def get_time_schedule(self, user, date=None):
        if date is None:
            date = datetime.date.today()
        if user.cls.has_day(date):
            try:
                return time_schedule_from_day(user.cls.get_day(date))
            except KeyError:
                pass
        if user.has_day(date):
            try:
                return time_schedule_from_day(user.get_day(date))
            except KeyError:
                pass
        if user.url.startswith('https://elschool.ru/users/diaries/grades'):
            user.url = user.url[len('https://elschool.ru/users/diaries/grades'):]
        days = await self.elschool_repo.get_days(user.jwtoken, user.url, date.year, date.isocalendar()[1])
        user.update_days(days)
        return time_schedule_from_day(days[date.weekday()])

    async def get_homework(self, user, date=None):
        if date is None:
            date = datetime.date.today()
        if day := user.cls.find_day(date):
            try:
                return homework_from_day(day)
            except KeyError:
                pass
        if day := user.find_day(date):
            try:
                return homework_from_day(day)
            except KeyError:
                pass
        if user.url.startswith('https://elschool.ru/users/diaries/grades'):
            user.url = user.url[len('https://elschool.ru/users/diaries/grades'):]
        days = await self.elschool_repo.get_days(user.jwtoken, user.url, date.year, date.isocalendar()[1])
        user.update_days(days, date)
        return homework_from_day(days[date.weekday()])

    async def get_day_marks(self, user, date=None):
        if date is None:
            date = datetime.date.today()
        if user.has_day(date):
            try:
                return marks_from_day(user.get_day(date))
            except KeyError:
                pass
        if user.url.startswith('https://elschool.ru/users/diaries/grades'):
            user.url = user.url[len('https://elschool.ru/users/diaries/grades'):]
        days = await self.elschool_repo.get_days(user.jwtoken, user.url, date.year, date.isocalendar()[1])
        user.update_days(days, date)
        return marks_from_day(days[date.weekday()])

    def has_user(self, user_id):
        """Существует ли пользователь с определённым id"""
        return user_id in self.users


class ElschoolRepo:
    """Класс для взаимодействия с сервером elschool"""

    async def _get_url_base(self, session):
        response = await session.get(f'https://elschool.ru/users/diaries', ssl=False)
        html = await response.text()
        bs = BeautifulSoup(html, 'html.parser')
        return bs.find('a', text='Табель')['href'][len('grades'):]

    async def get_grades(self, jwtoken, url_base):
        """Получить оценки с сервера."""
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            return await self._get_grades(url_base, session)

    async def _get_grades(self, url_base, session):
        url = f'https://elschool.ru/users/diaries/grades?{url_base}'
        response = await session.get(url, ssl=False)
        if not response.ok:
            raise NoDataException(f"не удалось получить оценки с сервера, код ошибки {response.status}")
        if str(response.url) != url:
            print(response.url, url, str(response.url)==url)
            raise NoDataException("не удалось получить оценки с сервера. Обычно такое происходит, "
                                  "если не правильно указан логин или пароль. "
                                  "Попробуй изменить логин или пароль")
        text = await response.text()
        if not text:
            raise NoDataException('данные не получены')

        try:
            grades = {}
            bs = BeautifulSoup(text, 'html.parser')
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
                                'grade': int(grade.text),
                                'date': grade['data-popover-content'].split('<p>')
                            })
                        quarter_grades[lesson_name.text] = grades_list
                    grades[quarters[quarter_index]] = quarter_grades
        except Exception:
            raise NoDataException('данные получены в странном формате. Такое обычно происходит, если сайт перенаправляет на другую страницу.')
        return grades

    async def get_grades_and_url_base(self, jwtoken):
        """Получить оценки и адрес страницы пользователя.
        Это эффективней, чем получение оценок и адреса по отдельности.
        """
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            url_base = await self._get_url_base(session)
            grades = await self._get_grades(url_base, session)
            return grades, url_base

    async def get_days(self, jwtoken, url_base, year, week):
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            url = f'https://elschool.ru/users/diaries/details?{url_base}&year={year}&week={week}'
            response = await session.get(url, ssl=False)
            if not response.ok:
                raise NoDataException(f"не удалось получить оценки с сервера, код ошибки {response.status}")
            if str(response.url) != url:
                print(response.url, url, str(response.url) == url)
                raise NoDataException("не удалось получить распсание с сервера. Обычно такое происходит, "
                                      "если не правильно указан логин или пароль. "
                                      "Попробуй изменить логин или пароль")
            text = await response.text()
            if not text:
                raise NoDataException('данные не получены')

        try:
            bs = BeautifulSoup(text, 'html.parser')
            tables = bs.find('div', class_='diaries').find_all('table')
            days = []
            for table in tables:
                for tbody in table.find_all('tbody'):
                    if not list(filter(lambda val: (not isinstance(val, str) or val.strip()), tbody.children)):
                        continue
                    day = tbody.find('td', class_='diary__dayweek').text.split()[-1]
                    day = {'day': f'{year}.{day}'}
                    if tbody.find('td', class_='diary__nolesson'):
                        day['lessons'] = []
                        days.append(day)
                        continue

                    lessons = []
                    for tr in tbody.find_all('tr', class_='diary__lesson'):
                        lesson_td = tr.find('td', class_='diary__discipline')
                        div = tr.find('td', class_='diary__homework').find('div', class_='diary__homework-text')
                        marks = [{'date': span['data-popover-content'],
                                  'mark': int(span.text)}
                                 for span in tr.find('td', class_='diary__marks')
                                    .find_all('span', class_='diary__mark')]
                        lesson = {
                            'name': lesson_td.div.div.text.split('. ')[1],
                            'time': lesson_td.find('div', class_='diary__discipline__time').text,
                            'homework': div.text if div else None,
                            'marks': marks
                        }
                        lessons.append(lesson)
                    day['lessons'] = lessons
                    days.append(day)
            return days
        except Exception:
            raise NoDataException('данные получены в странном формате. Такое обычно происходит, если сайт перенаправляет на другую страницу.')

    async def register(self, login, password):
        """Регистрация пользователя по логину и паролю, возвращает токен."""
        async with aiohttp.ClientSession() as session:
            payload = {
                'login': login,
                'password': password
            }
            response = await session.post(f'{self._url}/Logon/Index', params=payload, ssl=False)
            logger.info(f'register response :{response}')
            if not response.ok:
                raise NotRegisteredException(f"Не удалось выполнить регистрацию, код сервера {response.status}")

            if not str(response.url).startswith('https://elschool.ru/users/privateoffice'):
                raise NotRegisteredException("Не удалась регистрация. Обычно такое происходит, "
                                             "если не правильно указан логин или пароль. "
                                             "Попробуй изменить данные от аккаунта", login=login, password=password)

            jwtoken = session.cookie_jar.filter_cookies(self._url).get('JWToken')
            logger.info(f'получен jwtoken: {jwtoken}')
            if not jwtoken or not jwtoken.value:
                raise NotRegisteredException('Регистрация удалась, но не найден токен. '
                                             'Я пока не знаю, почему это могло произойти.'
                                             'Скорее всего изменился способ работы регистрации у elschool.'
                                             'Эта проверка существует потому что такое может произойти.'
                                             'Это сообщение станет более информативным, когда я его получу.')
            return jwtoken.value


class NotRegisteredException(Exception):
    """Исключение, сообщающее о том, что регистрация не удалась."""
    def __init__(self, *args, login=None, password=None):
        super().__init__(*args)
        self.login = login
        self.password = password


class NoDataException(Exception):
    """Исключение, сообщающее о том, что не удалось получить некоторые данные с сервера."""
    pass
