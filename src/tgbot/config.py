import configparser
from dataclasses import dataclass


@dataclass
class TgBot:
    token: str
    admin_id: int
    use_pickle_memory: bool


@dataclass
class DataConfig:
    users_pkl_file: str
    memory_file: str


@dataclass
class Config:
    tg_bot: TgBot
    data: DataConfig


def load_config(path: str):
    config = configparser.ConfigParser()
    config.read(path)

    tg_bot = config["tg_bot"]

    return Config(
        tg_bot=TgBot(
            token=tg_bot.get("token"),
            admin_id=tg_bot.getint("admin_id"),
            use_pickle_memory=tg_bot.getboolean("use_piclie_memory"),
        ),
        data=DataConfig(**config["data"]),
    )
