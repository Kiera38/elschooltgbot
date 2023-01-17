from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from tgbot.models.user import UserRole


class RoleMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ['update']
    def __init__(self, admin_id: int):
        super().__init__()
        self.admin_id = admin_id

    async def pre_process(self, obj, data, *args):
        if not getattr(obj, "from_user", None):
            data["role"] = None
        elif obj.from_user.id == self.admin_id:
            data["role"] = UserRole.ADMIN
        else:
            data["role"] = UserRole.USER
        data['admin_id'] = self.admin_id

    async def post_process(self, obj, data, *args):
        del data["role"]
        del data["admin_id"]
