import logging
from datetime import datetime

from celery import Celery
from celery.schedules import crontab

from config import celery_config
from mongo import db

from app.processing import processing_data


logger = logging.getLogger(__name__)
logging.basicConfig(format="%(asctime)s - %(name)s - %(levelname)s - %(message)s", level=logging.INFO)


app = Celery("tasks", broker=celery_config.broker)
app.conf.update(
    worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
    broker_pool_limit=celery_config.broker_pool_limit,
    timezone=celery_config.timezone,
)

app.conf.beat_schedule = {
    "Parsing Sahibinden": {
        "task": "app.tasks.start_processing",
        "schedule": crontab(minute="*/3"),
    }
}


@app.task
def start_processing() -> None:
    city = db.cities.find().sort("last_parsing")[0]
    logging.info(f"Start parsing {city['name']}")
    db.cities.find_one_and_update({"_id": city["_id"]}, {"$set": {"last_parsing": datetime.now()}})
    city_parameter = dict(address_town=city["_id"])
    processing_data(city_parameter)
