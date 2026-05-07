from celery import Celery
from src.Config import Config


CELERY_BROKER_URL = Config.CELERY_BROKER_URL
CELERY_RESULT_BACKEND = Config.CELERY_RESULT_BACKEND

celery_app = Celery(
    "vendor_settlement",
    broker=CELERY_BROKER_URL,
    backend=CELERY_RESULT_BACKEND,
    include=[
        "src.Tasks.event_task",
        "src.Tasks.scheduled_task",
        "src.Tasks.reprocess_task"
    ]
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=300,  
    task_soft_time_limit=240,  
    worker_prefetch_multiplier=1,  
)

celery_app.conf.beat_schedule = {
    'process-scheduled-decisions-every-minute': {
        'task': 'process_scheduled_decisions',
        'schedule': 60.0, 
    },
}