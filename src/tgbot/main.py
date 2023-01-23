import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.fsm.storage.memory import MemoryStorage

from tgbot.config import load_config
from tgbot.handlers import get_commands, register_handlers
from tgbot.middlewares.data import RepoMiddleware
from tgbot.middlewares.role import RoleMiddleware

logger = logging.getLogger(__name__)


async def set_bot_commands(bot: Bot):
    await bot.set_my_commands(get_commands())


async def run_bot():
    handlers = logging.FileHandler('bot.log'), logging.StreamHandler()
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s - %(levelname)s - %(name)s - %(message)s",
        handlers=handlers
    )
    logger.info("Starting bot")
    config = load_config("bot.ini")

    storage = MemoryStorage()

    bot = Bot(token=config.tg_bot.token, parse_mode='HTML')
    dp = Dispatcher(storage=storage)
    role_middleware = RoleMiddleware(config.tg_bot.admin_id)
    dp.message.outer_middleware(role_middleware)
    dp.errors.middleware(role_middleware)
    dp.message.outer_middleware(RepoMiddleware(config.data.users_pkl_file))
    register_handlers(dp)

    await set_bot_commands(bot)
    # start
    try:
        await dp.start_polling(bot)
    finally:
        await dp.storage.close()


def main():
    """Wrapper for command line"""
    try:
        asyncio.run(run_bot())
    except (KeyboardInterrupt, SystemExit):
        logger.info("Bot stopped!")


if __name__ == '__main__':
    main()
