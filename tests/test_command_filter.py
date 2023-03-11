import asyncio

import tgbot.handlers
from tgbot.filters import command
from aiogram.types import Message, Chat
import datetime

async def main():
    message = Message(text='/start', message_id=1012836, date=datetime.datetime.now(), chat=Chat(id=81294, type='private'))
    assert await command.CommandFilter()(message)


asyncio.run(main())