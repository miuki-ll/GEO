"""Celery task modules."""
from app.tasks.all_tasks import diagnosis_run, content_generate, monitor_sample  # noqa: F401

__all__ = ["diagnosis_run", "content_generate", "monitor_sample"]
