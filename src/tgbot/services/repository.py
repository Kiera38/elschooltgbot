import logging
import time
from typing import List, Dict

import aiohttp
from bs4 import BeautifulSoup
import aiogram.utils.markdown as fmt

from tgbot.models.user import User

logger = logging.getLogger(__name__)


def _decrypt_pass(password):
    return ''.join([chr(i) for i in password])


def _encrypt_pass(password):
    return [ord(c) for c in password]


class Repo:
    def __init__(self, users, admin_id):
        self.users: Dict[int, User] = users
        self.elschool_repo = ElschoolRepo()
        self._admin_id = admin_id

    async def add_user(self, user_id, user: User) -> None:
        if user.password:
            user.password = _encrypt_pass(user.password)
        self.users[user_id] = user
        logger.info('пользователь добавлен')

    def list_users(self) -> List[User]:
        """List all bot users"""
        return list(self.users.values())

    def user_ids(self):
        return list(self.users.keys())

    def get_admin_user(self):
        return self.get_user(self._admin_id)

    def get_user(self, user_id):
        return self.users.get(user_id)

    def remove_user(self, user_id):
        del self.users[user_id]

    async def get_grades(self, user):
        if user.has_cashed_grades:
            logger.info('используются кешированные оценки')
            return user.cached_grades, 0
        start = time.time()
        logger.info('получаем новые оценки')
        if user.url:
            grades = await self.elschool_repo.get_grades(user.login, _decrypt_pass(user.password), user.url)
        else:
            grades, user.url = await self.elschool_repo.get_grades_and_url(user.login, _decrypt_pass(user.password))
        user.update_cache(grades)
        end = time.time()
        logger.info(f'получены новые оценки за {end-start}')

        return grades, end - start

    def has_user(self, user_id):
        return user_id in self.users

    def set_user_password(self, user_id, password):
        user = self.get_user(user_id)
        user.password = _encrypt_pass(password)



class ElschoolRepo:
    def __init__(self):
        self._url = 'https://elschool.ru'

    async def get_user_url(self, login, password):
        async with aiohttp.ClientSession() as session:
            await self._register(login, password, session)
            return await self._get_url(session)

    async def _get_url(self, session):
        response = await session.get(f'{self._url}/users/diaries')
        return self._find_user_url(await response.text())

    async def get_grades(self, login, password, url):
        async with aiohttp.ClientSession() as session:
            await self._register(login, password, session)
            return await self._get_grades(url, session)

    async def _get_grades(self, url, session):
        response = await session.get(url)
        if not response.ok:
            raise NoDataException(f"не удалось получить оценки с сервера, код ошибки {response.status}")
        return self._parse_grades(await response.text())

    async def get_grades_and_url(self, login, password):
        async with aiohttp.ClientSession() as session:
            await self._register(login, password, session)
            url = await self._get_url(session)
            grades = await self._get_grades(url, session)
            return grades, url

    async def _register(self, login, password, session):
        payload = {
            'login': login,
            'password': password,
            'GoogleAuthCode': '',
        }
        response = await session.post(f'{self._url}/Logon/Index', params=payload, ssl=False)
        logger.info(f'register response :{response}')
        if not response.ok:
            raise NotRegisteredException(f"не удалось выполнить регистрацию, код сервера {response.status}")

        if str(response.url) != 'https://elschool.ru/users/privateoffice':
            raise NotRegisteredException("не удалась регистрация. Обычно такое происходит, "
                                         "если не правильно указан логин или пароль."
                                         "Смена логина или пароля может помочь"
                                         f"твой логин: {fmt.hspoiler(login)} и пароль {fmt.hspoiler(password)}")

    @staticmethod
    def _find_user_url(html):
        bs = BeautifulSoup(html, 'html.parser')
        return 'https://elschool.ru/users/diaries/' + bs.find('a', text='Табель')['href']

    @staticmethod
    def _parse_grades(html):
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
        return grades


class NotRegisteredException(Exception):
    pass

class NoDataException(Exception):
    pass