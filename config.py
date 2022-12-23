import os

from dotenv import load_dotenv
from pydantic import BaseSettings
from typing import Optional, List

load_dotenv()

CLOSED_AREAS: list[str] = [
    "Hurma Mah.",
    "Sarısu Mh.",
    "Liman Mah.",
    "Topçular Mh.",
]


class TelegramSettings(BaseSettings):
    token_antalya_bot: str
    antalya_bot_id: str
    id_antalya_channel: str
    id_antalya_chat: str

    class Config:
        evn_file = ".env"
        env_prefix = 'telegram_'


class MongoDBSettings(BaseSettings):
    username: Optional[str]
    password: Optional[str]
    uri: str
    port: int
    database: str

    class Config:
        evn_file = ".env"
        env_prefix = 'mongodb_'


class CelerySettings(BaseSettings):
    broker: str = 'redis://redis'
    timezone: str = 'Europe/Istanbul'
    worker_max_tasks_per_child: int = 1
    broker_pool_limit: bool = None


class MapboxSettings(BaseSettings):
    token: str
    url: str

    class Config:
        evn_file = ".env"
        env_prefix = 'mapbox_'


class CitiesSettings(BaseSettings):
    muratpasha: str = "83"
    kepez: str = "84"
    konyaalti: str = "85"


telegram_config = TelegramSettings()
mongo_config = MongoDBSettings()
celery_config = CelerySettings()
mapbox_config = MapboxSettings()
cities_config = CitiesSettings()
