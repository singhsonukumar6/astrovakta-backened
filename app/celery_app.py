"""
Celery application configuration.
Uses Redis as broker and result backend.
"""
import os
from celery import Celery

REDIS_URL = os.environ.get("REDIS_URL", "redis://localhost:6379/0")

celery_app = Celery(
    "astrovakta",
    broker=REDIS_URL,
    backend=os.environ.get("REDIS_BACKEND_URL", "redis://localhost:6379/1"),
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    result_expires=3600,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    worker_max_tasks_per_child=100,
    task_routes={
        "app.workers.pdf_worker.*": {"queue": "pdf"},
        "app.workers.ai_worker.*": {"queue": "ai"},
    },
    task_default_queue="default",
)

celery_app.autodiscover_tasks(["app.workers"])
