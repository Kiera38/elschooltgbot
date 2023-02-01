import asyncio
import pickle
from pprint import pprint

import tgbot.config
import tgbot.services.repository

config = tgbot.config.load_config('../src/bot.ini')

with open('../src/'+config.data.users_pkl_file, 'rb') as f:
    users = pickle.load(f)

pprint(users)
token = 'eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJJZCI6IjU1Mjk0NCIsIk11c3RDaGFuZ2VQYXNzd29yZCI6IkZhbHNlIiwicm9sZSI6IjgsRGVwYXJ0bWVudCwsNTQsMTIwNywyMTA1OTQsIiwiRVNJQUxvZ29uIjoiRmFsc2UiLCJBdmFpbGFibGVSb2xlcyI6IjgiLCJuYmYiOjE2NzQwNjg0MDAsImV4cCI6MTY3NDY3MzIwMCwiaWF0IjoxNjc0MTM5ODMzLCJpc3MiOiIxMC42Mi4zNC4xNCIsImF1ZCI6Iml0LmJyc2MucnUifQ.3TB_OPpxDhjf1SG5lGhWm7fuqGZwrv2uVfJVwuTl9RU'
url='https://elschool.ru/users/diaries/grades?rooId=54&instituteId=1207&departmentId=210594&pupilId=552944'
repo = tgbot.services.repository.Repo(users)
pprint(asyncio.run(repo.get_grades_userdata(token, url)))