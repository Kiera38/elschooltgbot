import asyncio
from pprint import pprint

from tgbot.services.repository import ElschoolRepo

async def test():
    elschool_repo = ElschoolRepo()
    jwtoken = await elschool_repo.register('Pavelskij_Maksim', 'Maxmax12356')
    pprint(await elschool_repo.get_days(jwtoken, 'rooId=47&instituteId=487&departmentId=227545&pupilId=552340', 2023, 13))


asyncio.run(test())
