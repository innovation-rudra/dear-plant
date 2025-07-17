"""
Plant Care Application - Background Jobs Package

Contains Celery tasks and background processing for the Plant Care Application.

Main components:
- celery_app.py: Celery application configuration
- tasks/: Individual task modules
- schedules/: Periodic task configurations
- workers/: Worker-specific configurations
"""

from .celery_app import celery_app

__all__ = ["celery_app"]