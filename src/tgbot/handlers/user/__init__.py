from aiogram import Router, Dispatcher

from tgbot.filters.user import RegisteredUserFilter
from tgbot.middlewares.grades import GradesMiddleware

router = Router()
registered_router = Router()
registered_router.message.filter(RegisteredUserFilter(True))
router.include_router(registered_router)
grades_router = Router()
grades_middleware = GradesMiddleware()
grades_router.message.middleware(grades_middleware)
grades_router.callback_query.middleware(grades_middleware)
registered_router.include_router(grades_router)

def register_user(dp: Dispatcher):
    dp.include_router(router)


from . import keyboard, commands