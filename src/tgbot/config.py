"""Получение конфига бота из файла."""
import configparser
from dataclasses import dataclass


@dataclass
class TgBot:
    """Дааные о боте, полученные из файла bot.log"""
    token: str
    admin_id: int


@dataclass
class DataConfig:
    """Информация о том, где хранятся данные бота."""
    db_file: str


@dataclass
class Config:
    """Вся конфигурация бота, полученная из файла bot.ini"""
    tg_bot: TgBot
    data: DataConfig


def load_config(path: str):
    """Загрузка конфига."""
    config = configparser.ConfigParser()
    config.read(path)

    tg_bot = config["tg_bot"]

    return Config(
        tg_bot=TgBot(
            token=tg_bot.get("token"),
            admin_id=tg_bot.getint("admin_id"),
        ),
        data=DataConfig(**config["data"]),
    )
