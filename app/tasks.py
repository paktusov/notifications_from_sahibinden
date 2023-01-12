import asyncio
import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

from config import celery_config
from mongo import db

from app.processing import processing_data


logger = logging.getLogger(__name__)

app = Celery("tasks", broker=celery_config.broker)
app.conf.update(
    worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
    broker_pool_limit=celery_config.broker_pool_limit,
    timezone=celery_config.timezone,
)

app.conf.beat_schedule = {
    "Parsing Sahibinden": {
        "task": "app.tasks.start_processing",
        "schedule": crontab(minute="*/5"),
    }
}


@app.task
def start_processing() -> None:
    loop = asyncio.get_event_loop()
    town = db.towns.find().sort("last_parsing")[0]
    logging.info("Start parsing %s", town["name"])
    parameter = dict(address_town=town["_id"])
    loop.run_until_complete(processing_data(parameter))
    db.cities.find_one_and_update({"_id": town["_id"]}, {"$set": {"last_parsing": datetime.now()}})
