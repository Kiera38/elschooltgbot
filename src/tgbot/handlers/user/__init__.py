from aiogram import Router, Dispatcher

from tgbot.filters.user import RegisteredUserFilter
from tgbot.middlewares.grades import GradesMiddleware

router = Router()
registered_router = Router()
registered_router.message.filter(RegisteredUserFilter(True))
router.include_router(registered_router)
grades_router = Router()
grades_router.message.middleware(GradesMiddleware())
registered_router.include_router(grades_router)

def register_user(dp: Dispatcher):
    dp.include_router(router)