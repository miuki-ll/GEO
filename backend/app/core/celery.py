from celery import Celery
from kombu import Queue

from app.core.config import settings

celery_app = Celery(
    "app",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Shanghai",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=3600,
    task_soft_time_limit=3300,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=100,
    task_default_queue="default",
    task_queues=(
        Queue("default", routing_key="task.#"),
        Queue("diagnosis", routing_key="diagnosis.#"),
        Queue("content", routing_key="content.#"),
        Queue("monitor", routing_key="monitor.#"),
    ),
    task_routes={
        "app.agents.l1.*": {"queue": "default"},
        "app.tasks.diagnosis_run": {"queue": "diagnosis"},
        "app.tasks.content_*": {"queue": "content"},
        "app.tasks.monitor_*": {"queue": "monitor"},
    },
    beat_schedule={},
)

import app.tasks  # noqa: E402,F401  -- register tasks on worker startup

