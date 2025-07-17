"""
Plant Care Application - Celery Application

This module creates and configures the Celery application for background tasks.
"""
import os
from celery import Celery
import structlog

from app.shared.config.settings import get_settings

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)

# Create Celery application
celery_app = Celery(
    "plant_care",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=[
        "app.background_jobs.tasks.care_reminders",
        "app.background_jobs.tasks.health_monitoring", 
        "app.background_jobs.tasks.weather_updates",
        "app.background_jobs.tasks.analytics_processing",
        "app.background_jobs.tasks.notification_sending",
        "app.background_jobs.tasks.api_rotation",
        "app.background_jobs.tasks.data_cleanup",
    ]
)

# Configure Celery
celery_app.conf.update(
    # Task serialization
    task_serializer=settings.CELERY_TASK_SERIALIZER,
    result_serializer=settings.CELERY_RESULT_SERIALIZER,
    accept_content=["json"],
    result_expires=3600,
    timezone=settings.CELERY_TIMEZONE,
    enable_utc=True,
    
    # Worker settings
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    worker_concurrency=settings.CELERY_WORKER_CONCURRENCY,
    
    # Task routing
    task_routes={
        # High priority tasks
        "app.background_jobs.tasks.notification_sending.send_urgent_notification": {"queue": "high_priority"},
        "app.background_jobs.tasks.care_reminders.send_care_reminder": {"queue": "high_priority"},
        "app.background_jobs.tasks.health_monitoring.send_health_alert": {"queue": "high_priority"},
        
        # Medium priority tasks
        "app.background_jobs.tasks.notification_sending.send_notification": {"queue": "medium_priority"},
        "app.background_jobs.tasks.api_rotation.rotate_api_usage": {"queue": "medium_priority"},
        "app.background_jobs.tasks.weather_updates.update_weather_data": {"queue": "medium_priority"},
        
        # Low priority tasks
        "app.background_jobs.tasks.analytics_processing.process_analytics": {"queue": "low_priority"},
        "app.background_jobs.tasks.data_cleanup.cleanup_old_data": {"queue": "low_priority"},
    },
    
    # Task time limits
    task_soft_time_limit=settings.CELERY_TASK_SOFT_TIME_LIMIT,
    task_time_limit=settings.CELERY_TASK_TIME_LIMIT,
    
    # Task retry configuration
    task_acks_late=True,
    task_reject_on_worker_lost=True,
    task_track_started=True,
    
    # Beat schedule for periodic tasks
    beat_schedule={
        # Care reminders - every 15 minutes
        "send-care-reminders": {
            "task": "app.background_jobs.tasks.care_reminders.send_care_reminders",
            "schedule": 900.0,  # 15 minutes in seconds
            "options": {"queue": "high_priority"},
        },
        
        # Health monitoring - every 30 minutes
        "check-plant-health": {
            "task": "app.background_jobs.tasks.health_monitoring.check_plant_health",
            "schedule": 1800.0,  # 30 minutes in seconds
            "options": {"queue": "medium_priority"},
        },
        
        # Weather updates - every hour
        "update-weather-data": {
            "task": "app.background_jobs.tasks.weather_updates.update_weather_data",
            "schedule": 3600.0,  # 1 hour in seconds
            "options": {"queue": "medium_priority"},
        },
        
        # Analytics processing - every 6 hours
        "process-analytics": {
            "task": "app.background_jobs.tasks.analytics_processing.process_analytics",
            "schedule": 21600.0,  # 6 hours in seconds
            "options": {"queue": "low_priority"},
        },
        
        # Data cleanup - daily
        "cleanup-old-data": {
            "task": "app.background_jobs.tasks.data_cleanup.cleanup_old_data",
            "schedule": 86400.0,  # 24 hours in seconds
            "options": {"queue": "low_priority"},
        },
    },
)

# Environment-specific configuration
if settings.APP_ENV == "development":
    # In development, you might want to disable some periodic tasks
    # or run them less frequently
    celery_app.conf.beat_schedule.update({
        # Reduce frequency in development
        "send-care-reminders": {
            "task": "app.background_jobs.tasks.care_reminders.send_care_reminders",
            "schedule": 3600.0,  # 1 hour instead of 15 minutes
            "options": {"queue": "high_priority"},
        },
    })
    
elif settings.APP_ENV == "testing":
    # Disable beat schedule in testing
    celery_app.conf.beat_schedule = {}
    celery_app.conf.task_always_eager = True
    celery_app.conf.task_eager_propagates = True


# Task base class for better error handling
class PlantCareTask(celery_app.Task):
    """Custom task base class for Plant Care tasks."""
    
    def on_success(self, retval, task_id, args, kwargs):
        """Called when task succeeds."""
        logger.info(
            "Task completed successfully",
            task_id=task_id,
            task_name=self.name,
            result=retval,
        )
    
    def on_failure(self, exc, task_id, args, kwargs, einfo):
        """Called when task fails."""
        logger.error(
            "Task failed",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            traceback=str(einfo),
        )
    
    def on_retry(self, exc, task_id, args, kwargs, einfo):
        """Called when task is retried."""
        logger.warning(
            "Task retrying",
            task_id=task_id,
            task_name=self.name,
            error=str(exc),
            retry_count=self.request.retries,
        )


# Set custom task base
celery_app.Task = PlantCareTask


# Utility functions for running Celery components
def run_worker():
    """Run Celery worker."""
    celery_app.start(argv=["celery", "worker", "--loglevel=info"])


def run_beat():
    """Run Celery beat scheduler."""
    celery_app.start(argv=["celery", "beat", "--loglevel=info"])


def run_flower():
    """Run Flower monitoring."""
    os.system("celery -A app.background_jobs.celery_app flower")


# Auto-discover tasks (will be used when we implement the task modules)
def autodiscover_tasks():
    """Auto-discover tasks from all modules."""
    try:
        # This will be used when we implement actual task modules
        task_modules = [
            "app.background_jobs.tasks.care_reminders",
            "app.background_jobs.tasks.health_monitoring",
            "app.background_jobs.tasks.weather_updates", 
            "app.background_jobs.tasks.analytics_processing",
            "app.background_jobs.tasks.notification_sending",
            "app.background_jobs.tasks.api_rotation",
            "app.background_jobs.tasks.data_cleanup",
        ]
        
        for module in task_modules:
            try:
                celery_app.autodiscover_tasks([module])
            except ImportError:
                # Module doesn't exist yet, skip it
                logger.debug(f"Task module {module} not found, skipping")
                pass
                
    except Exception as e:
        logger.warning("Failed to autodiscover tasks", error=str(e))


# Export the celery app and utilities
__all__ = [
    "celery_app",
    "run_worker", 
    "run_beat",
    "run_flower",
    "autodiscover_tasks",
    "PlantCareTask",
]