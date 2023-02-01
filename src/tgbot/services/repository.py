#

import logging
import time
from typing import List, Dict

import aiohttp
from bs4 import BeautifulSoup
from aiogram import html

from tgbot.models.user import User

logger = logging.getLogger(__name__)


class Repo:
    def __init__(self, users):
        self.users: Dict[int, User] = users
        self.elschool_repo = ElschoolRepo()

    def add_user(self, user_id, user: User) -> None:
        self.users[user_id] = user
        logger.info(f'пользователь добавлен {user}')

    def list_users(self) -> List[User]:
        """List all bot users"""
        return list(self.users.values())

    def user_ids(self):
        return list(self.users.keys())

    def get_user(self, user_id):
        return self.users.get(user_id)

    def remove_user(self, user_id):
        del self.users[user_id]

    async def register_user(self, login, password):
        return await self.elschool_repo.register(login, password)

    async def get_grades_userdata(self, jwtoken, url=None):
        start = time.time()
        logger.info('получаем новые оценки')
        if url:
            grades = await self.elschool_repo.get_grades(jwtoken, url)
        else:
            grades, url = await self.elschool_repo.get_grades_and_url(jwtoken)
        end = time.time()
        logger.info(f'получены новые оценки за {end - start}')
        return grades, end - start, url

    async def get_grades(self, user):
        if user.has_cached_grades:
            logger.info('используются кешированные оценки')
            return user.cached_grades, 0
        grades, time, user.url = await self.get_grades_userdata(user.jwtoken, user.url)
        user.update_cache(grades)
        return grades, time

    def has_user(self, user_id):
        return user_id in self.users


class ElschoolRepo:
    def __init__(self):
        self._url = 'https://elschool.ru'

    async def _get_url(self, session):
        response = await session.get(f'{self._url}/users/diaries')
        html = await response.text()
        bs = BeautifulSoup(html, 'html.parser')
        return 'https://elschool.ru/users/diaries/' + bs.find('a', text='Табель')['href']

    async def get_grades(self, jwtoken, url):
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            return await self._get_grades(url, session)

    async def _get_grades(self, url, session):
        response = await session.get(url)
        if not response.ok:
            raise NoDataException(f"не удалось получить оценки с сервера, код ошибки {response.status}")
        return self._parse_grades(await response.text())

    async def get_grades_and_url(self, jwtoken):
        async with aiohttp.ClientSession(cookies={'JWToken': jwtoken}) as session:
            url = await self._get_url(session)
            grades = await self._get_grades(url, session)
            return grades, url

    async def register(self, login, password):
        async with aiohttp.ClientSession() as session:
            payload = {
                'login': login,
                'password': password
            }
            response = await session.post(f'{self._url}/Logon/Index', params=payload, ssl=False)
            logger.info(f'register response :{response}')
            if not response.ok:
                raise NotRegisteredException(f"Не удалось выполнить регистрацию, код сервера {response.status}")

            if str(response.url) != 'https://elschool.ru/users/privateoffice':
                raise NotRegisteredException("Не удалась регистрация. Обычно такое происходит, "
                                             "если не правильно указан логин или пароль. "
                                             "Попробуй изменить логин или пароль ", login=login, password=password)

            jwtoken = session.cookie_jar.filter_cookies(self._url).get('JWToken')
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
                                'grade': int(grade.text),
                                'date': grade['data-popover-content'].split('<p>')
                            })
                        quarter_grades[lesson_name.text] = grades_list
                    grades[quarters[quarter_index]] = quarter_grades
        except Exception:
            raise NoDataException('данные получены в странном формате. Такое обычно происходит если сайт перенаправляет на другую страницу.')
        return grades


class NotRegisteredException(Exception):
    def __init__(self, *args, login=None, password=None):
        super().__init__(*args)
        self.login = login
        self.password = password

class NoDataException(Exception):
    pass