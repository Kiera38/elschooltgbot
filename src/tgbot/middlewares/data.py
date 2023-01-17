import os.path
import pickle

from aiogram.dispatcher.middlewares import LifetimeControllerMiddleware

from tgbot.services.repository import Repo


class DataMiddleware(LifetimeControllerMiddleware):
    skip_patterns = ["error", "update"]

    def __init__(self, file):
        super().__init__()
        if os.path.exists(file):
            with open(file, 'rb') as f:
                self.users = pickle.load(f)
        else:
            self.users = {}
        self.file = file

    async def pre_process(self, obj, data, *args):
        data["users"] = self.users
        repo = data["repo"] = Repo(self.users, data['admin_id'])
        data['elschool_repo'] = repo.elschool_repo

    async def post_process(self, obj, data, *args):
        del data["repo"]
        del data["elschool_repo"]
        users = data["users"]
        with open(self.file, "wb") as f:
            pickle.dump(users, f)
