from celery import Celery
from kombu import Queue

from geo_core.core.config import settings

celery_app = Celery(
    "geo_core",
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
        "geo_core.agents.l1.*": {"queue": "default"},
        "geo_core.celery_app.tasks.diagnosis_*": {"queue": "diagnosis"},
        "geo_core.celery_app.tasks.content_*": {"queue": "content"},
        "geo_core.celery_app.tasks.monitor_*": {"queue": "monitor"},
    },
    beat_schedule={},
)

import geo_core.celery_app.tasks  # noqa: E402,F401  -- register tasks on worker startup

