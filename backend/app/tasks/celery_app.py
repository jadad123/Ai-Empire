from celery import Celery
from celery.schedules import crontab
from app.config import settings

celery_app = Celery(
    "empire",
    broker=settings.redis_url,
    backend=settings.redis_url,
    include=[
        "app.tasks.ingestion_tasks",
        "app.tasks.processing_tasks"
    ]
)

# Configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=600,  # 10 minutes max
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    task_reject_on_worker_lost=True,
)

# Priority queues
celery_app.conf.task_queues = {
    'high': {'exchange': 'high', 'routing_key': 'high'},
    'default': {'exchange': 'default', 'routing_key': 'default'},
    'low': {'exchange': 'low', 'routing_key': 'low'},
}

celery_app.conf.task_default_queue = 'default'

# Beat schedule - periodic tasks
celery_app.conf.beat_schedule = {
    'poll-news-sources': {
        'task': 'app.tasks.ingestion_tasks.poll_all_sources',
        'schedule': crontab(minute='*/10'),  # Every 10 minutes
        'kwargs': {'velocity_mode': 'news'}
    },
    'poll-evergreen-sources': {
        'task': 'app.tasks.ingestion_tasks.poll_all_sources',
        'schedule': crontab(hour='*/24'),  # Every 24 hours
        'kwargs': {'velocity_mode': 'evergreen'}
    },
    'cleanup-old-articles': {
        'task': 'app.tasks.processing_tasks.cleanup_old_articles',
        'schedule': crontab(hour=3, minute=0),  # Daily at 3 AM
    },
}
