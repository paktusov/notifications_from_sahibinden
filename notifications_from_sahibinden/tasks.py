from celery import Celery
from celery.schedules import crontab
from notifications_from_sahibinden.config import celery_config
from notifications_from_sahibinden.data import processing_data


app = Celery('tasks', broker=celery_config.broker)
app.conf.update(
    worker_max_tasks_per_child=celery_config.worker_max_tasks_per_child,
    broker_pool_limit=celery_config.broker_pool_limit,
    timezone=celery_config.timezone,
)
app.conf.beat_schedule = dict()
app.conf.beat_schedule = {
    'add-every-1-minutes': {
        'task': 'notifications_from_sahibinden.tasks.start_processing',
        'schedule': crontab(minute='*/5'),
    },
}


@app.task
def start_processing():
    processing_data()