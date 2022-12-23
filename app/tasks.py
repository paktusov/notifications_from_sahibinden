from celery import Celery
from celery.schedules import crontab

from config import celery_config, cities_config

from app.processing import processing_data


app = Celery("tasks", broker=celery_config.broker)
app.conf.update(
    worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
    broker_pool_limit=celery_config.broker_pool_limit,
    timezone=celery_config.timezone,
)

for i, city_config in enumerate(cities_config):
    city, config = city_config
    time = ','.join([str(j) for j in range(i * 2, 60, 6)])
    app.conf.beat_schedule[f"parsing_{city}"] = {
            "task": "app.tasks.start_processing",
            "schedule": crontab(minute=time),
            "args": (config,),
    }


@app.task
def start_processing(parameter: str) -> None:
    city_parameter = dict(address_town=parameter)
    processing_data(city_parameter)
