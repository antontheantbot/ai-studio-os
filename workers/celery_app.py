from celery import Celery
from celery.schedules import crontab
import os

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "aistudio",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=["workers.tasks.scheduled"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_acks_late=True,
    worker_prefetch_multiplier=1,
)

celery_app.conf.beat_schedule = {
    # Daily at 08:00 UTC
    "scan-opportunities-daily": {
        "task": "tasks.scan_opportunities",
        "schedule": crontab(hour=8, minute=0),
    },
    # Daily at 09:00 UTC
    "monitor-press-daily": {
        "task": "tasks.monitor_press",
        "schedule": crontab(hour=9, minute=0),
    },
    # Weekly on Monday at 07:00 UTC
    "scout-architecture-weekly": {
        "task": "tasks.scout_architecture",
        "schedule": crontab(hour=7, minute=0, day_of_week=1),
    },
}
