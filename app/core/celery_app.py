"""
Celery Configuration and Application

Provides async task processing for background jobs.
"""
from celery import Celery

from app.core.config import settings

# Create Celery app
celery_app = Celery(
    "bookapi",
    broker=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/2",
    backend=f"redis://{settings.REDIS_HOST}:{settings.REDIS_PORT}/3",
    include=["app.core.tasks.tasks"],
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    result_expires=3600,  # Results expire after 1 hour

    # Beat schedule for periodic tasks
    beat_schedule={
        "cleanup-expired-tokens": {
            "task": "app.core.tasks.tasks.cleanup_expired_tokens",
            "schedule": 3600.0,  # Every hour
        },
        "send-daily-digest": {
            "task": "app.core.tasks.tasks.send_daily_digest",
            "schedule": 86400.0,  # Daily
        },
    },
)

# Task routing
celery_app.conf.task_routes = {
    "app.core.tasks.tasks.send_email_task": {"queue": "email"},
    "app.core.tasks.tasks.process_file_task": {"queue": "files"},
    "app.core.tasks.tasks.*": {"queue": "default"},
}
