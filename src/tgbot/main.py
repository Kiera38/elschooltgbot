import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.files import PickleStorage
from aiogram.contrib.fsm_storage.memory import MemoryStorage

from tgbot.config import load_config
from tgbot.filters.role import RoleFilter, AdminFilter
from tgbot.filters.user import RegisteredUserFilter
from tgbot.handlers import get_commands, register_handlers
from tgbot.middlewares.data import DataMiddleware
from tgbot.middlewares.role import RoleMiddleware

logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    await bot.set_my_commands(get_commands())


async def run_bot():
    handlers = logging.FileHandler('bot.log', encoding='utf-8'), logging.StreamHandler()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=handlers
    )
    logger.info("Starting bot")
    config = load_config("bot.ini")

    if config.tg_bot.use_pickle_memory:
        storage = PickleStorage(config.data.memory_file)
    else:
        storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode=types.ParseMode.HTML)
    dp = Dispatcher(bot, storage=storage)
    dp.middleware.setup(RoleMiddleware(config.tg_bot.admin_id))
    dp.middleware.setup(DataMiddleware(config.data.users_pkl_file))
    dp.filters_factory.bind(RoleFilter)
    dp.filters_factory.bind(AdminFilter)
    dp.filters_factory.bind(RegisteredUserFilter)

    register_handlers(dp)

    await set_bot_commands(bot)
    # start
    try:
        await dp.start_polling()
    finally:
        await dp.storage.close()
        await dp.storage.wait_closed()
        await (await bot.get_session()).close()


def main():
    """Wrapper for command line"""
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")


if __name__ == '__main__':
    main()
