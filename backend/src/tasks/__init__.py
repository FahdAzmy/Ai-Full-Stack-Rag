"""
Celery app configuration (SPEC-08).

Central Celery instance used by all background tasks.
Connects to Redis for both task brokering and result storage.
"""

from celery import Celery
from src.helpers.config import settings

celery_app = Celery(
    "scholargpt",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    # Serialization — JSON only (no pickle for security)
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],

    # Timezone
    timezone="UTC",
    enable_utc=True,

    # Task settings
    task_track_started=True,       # Enables STARTED state tracking
    task_acks_late=True,           # Acknowledge after completion (safer)
    worker_prefetch_multiplier=1,  # One task at a time per worker

    # Retry settings
    task_default_retry_delay=30,   # Wait 30s before retry
    task_max_retries=3,            # Maximum 3 retries

    # Result settings
    result_expires=3600,           # Results expire after 1 hour
)

# Explicitly include the ingestion module so Celery finds the task
celery_app.conf.update(
    include=['src.tasks.ingestion']
)
