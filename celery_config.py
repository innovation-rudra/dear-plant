"""
Plant Care Application - Celery Configuration
"""
import os
from datetime import timedelta

from celery import Celery
from celery.schedules import crontab
from kombu import Exchange, Queue

from app.shared.config.settings import get_settings

# Get application settings
settings = get_settings()

# Celery configuration
celery_config = {
    # Broker settings
    "broker_url": settings.CELERY_BROKER_URL,
    "result_backend": settings.CELERY_RESULT_BACKEND,
    
    # Task settings
    "task_serializer": settings.CELERY_TASK_SERIALIZER,
    "result_serializer": settings.CELERY_RESULT_SERIALIZER,
    "accept_content": ["json"],
    "result_expires": 3600,  # 1 hour
    "timezone": settings.CELERY_TIMEZONE,
    "enable_utc": True,
    
    # Worker settings
    "worker_prefetch_multiplier": 1,
    "worker_max_tasks_per_child": settings.CELERY_WORKER_MAX_TASKS_PER_CHILD,
    "worker_disable_rate_limits": False,
    "worker_concurrency": settings.CELERY_WORKER_CONCURRENCY,
    
    # Task routing
    "task_routes": {
        # High priority tasks
        "app.background_jobs.tasks.notification_sending.send_urgent_notification": {
            "queue": "high_priority"
        },
        "app.background_jobs.tasks.care_reminders.send_care_reminder": {
            "queue": "high_priority"
        },
        "app.background_jobs.tasks.health_monitoring.send_health_alert": {
            "queue": "high_priority"
        },
        
        # Medium priority tasks
        "app.background_jobs.tasks.notification_sending.send_notification": {
            "queue": "medium_priority"
        },
        "app.background_jobs.tasks.api_rotation.rotate_api_usage": {
            "queue": "medium_priority"
        },
        "app.background_jobs.tasks.weather_updates.update_weather_data": {
            "queue": "medium_priority"
        },
        
        # Low priority tasks
        "app.background_jobs.tasks.analytics_processing.process_analytics": {
            "queue": "low_priority"
        },
        "app.background_jobs.tasks.data_cleanup.cleanup_old_data": {
            "queue": "low_priority"
        },
    },
    
    # Queue configuration
    "task_default_queue": "medium_priority",
    "task_default_exchange": "plant_care",
    "task_default_exchange_type": "direct",
    "task_default_routing_key": "medium_priority",
    
    # Queue definitions
    "task_queues": (
        Queue(
            "high_priority",
            Exchange("plant_care", type="direct"),
            routing_key="high_priority",
            queue_arguments={"x-max-priority": 10},
        ),
        Queue(
            "medium_priority",
            Exchange("plant_care", type="direct"),
            routing_key="medium_priority",
            queue_arguments={"x-max-priority": 5},
        ),
        Queue(
            "low_priority",
            Exchange("plant_care", type="direct"),
            routing_key="low_priority",
            queue_arguments={"x-max-priority": 1},
        ),
    ),
    
    # Task time limits
    "task_soft_time_limit": settings.CELERY_TASK_SOFT_TIME_LIMIT,
    "task_time_limit": settings.CELERY_TASK_TIME_LIMIT,
    
    # Task retry configuration
    "task_acks_late": True,
    "task_reject_on_worker_lost": True,
    "task_track_started": True,
    
    # Beat schedule for periodic tasks
    "beat_schedule": {
        # Care reminders - every 15 minutes
        "send-care-reminders": {
            "task": "app.background_jobs.tasks.care_reminders.send_care_reminders",
            "schedule": crontab(minute="*/15"),
            "options": {"queue": "high_priority"},
        },
        
        # Health monitoring - every 30 minutes
        "check-plant-health": {
            "task": "app.background_jobs.tasks.health_monitoring.check_plant_health",
            "schedule": crontab(minute="*/30"),
            "options": {"queue": "medium_priority"},
        },
        
        # Weather updates - every hour
        "update-weather-data": {
            "task": "app.background_jobs.tasks.weather_updates.update_weather_data",
            "schedule": crontab(minute=0),
            "options": {"queue": "medium_priority"},
        },
        
        # API rotation - every hour
        "rotate-api-usage": {
            "task": "app.background_jobs.tasks.api_rotation.rotate_api_usage",
            "schedule": crontab(minute=0),
            "options": {"queue": "medium_priority"},
        },
        
        # Analytics processing - every 6 hours
        "process-analytics": {
            "task": "app.background_jobs.tasks.analytics_processing.process_analytics",
            "schedule": crontab(minute=0, hour="*/6"),
            "options": {"queue": "low_priority"},
        },
        
        # Data cleanup - daily at 2 AM
        "cleanup-old-data": {
            "task": "app.background_jobs.tasks.data_cleanup.cleanup_old_data",
            "schedule": crontab(minute=0, hour=2),
            "options": {"queue": "low_priority"},
        },
        
        # Generate daily reports - daily at 6 AM
        "generate-daily-reports": {
            "task": "app.background_jobs.tasks.analytics_processing.generate_daily_reports",
            "schedule": crontab(minute=0, hour=6),
            "options": {"queue": "low_priority"},
        },
        
        # Send weekly summaries - weekly on Monday at 8 AM
        "send-weekly-summaries": {
            "task": "app.background_jobs.tasks.notification_sending.send_weekly_summaries",
            "schedule": crontab(minute=0, hour=8, day_of_week=1),
            "options": {"queue": "medium_priority"},
        },
        
        # Update plant library - daily at 3 AM
        "update-plant-library": {
            "task": "app.background_jobs.tasks.data_cleanup.update_plant_library",
            "schedule": crontab(minute=0, hour=3),
            "options": {"queue": "low_priority"},
        },
        
        # Process milestone achievements - every 2 hours
        "process-milestones": {
            "task": "app.background_jobs.tasks.care_reminders.process_milestones",
            "schedule": crontab(minute=0, hour="*/2"),
            "options": {"queue": "medium_priority"},
        },
    },
    
    # Monitoring settings
    "worker_send_task_events": True,
    "task_send_sent_event": True,
    "worker_log_format": "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
    "worker_task_log_format": "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
    
    # Security settings
    "worker_hijack_root_logger": False,
    "worker_log_color": True,
    "worker_redirect_stdouts": True,
    "worker_redirect_stdouts_level": "INFO",
    
    # Error handling
    "task_annotations": {
        "*": {
            "rate_limit": "100/m",
            "time_limit": 300,
            "soft_time_limit": 240,
        },
        "app.background_jobs.tasks.notification_sending.send_urgent_notification": {
            "rate_limit": "1000/m",
            "time_limit": 60,
            "soft_time_limit": 45,
        },
        "app.background_jobs.tasks.analytics_processing.process_analytics": {
            "rate_limit": "10/m",
            "time_limit": 1800,
            "soft_time_limit": 1500,
        },
    },
    
    # Result backend settings
    "result_backend_transport_options": {
        "master_name": "mymaster",
        "visibility_timeout": 3600,
        "retry_policy": {
            "timeout": 5.0,
        },
    },
    
    # Broker transport options
    "broker_transport_options": {
        "visibility_timeout": 3600,
        "fanout_prefix": True,
        "fanout_patterns": True,
        "retry_policy": {
            "timeout": 5.0,
        },
    },
    
    # Additional settings for production
    "worker_pool_restarts": True,
    "worker_max_memory_per_child": 200000,  # 200MB
    "worker_disable_rate_limits": False,
    "task_compression": "gzip",
    "result_compression": "gzip",
    
    # Flower monitoring
    "flower_basic_auth": ["admin:admin"] if settings.APP_ENV == "development" else None,
    "flower_port": 5555,
    "flower_address": "0.0.0.0",
    
    # Custom configuration for different environments
    "include": [
        "app.background_jobs.tasks.care_reminders",
        "app.background_jobs.tasks.health_monitoring",
        "app.background_jobs.tasks.weather_updates",
        "app.background_jobs.tasks.analytics_processing",
        "app.background_jobs.tasks.notification_sending",
        "app.background_jobs.tasks.api_rotation",
        "app.background_jobs.tasks.data_cleanup",
    ],
}

# Environment-specific overrides
if settings.APP_ENV == "production":
    celery_config.update({
        "worker_log_format": "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        "worker_task_log_format": "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
        "worker_hijack_root_logger": False,
        "worker_log_color": False,
        "task_compression": "gzip",
        "result_compression": "gzip",
        "broker_pool_limit": 10,
        "broker_connection_retry_on_startup": True,
        "broker_connection_retry": True,
        "broker_connection_max_retries": 10,
    })
elif settings.APP_ENV == "development":
    celery_config.update({
        "worker_log_format": "[%(asctime)s: %(levelname)s/%(processName)s] %(message)s",
        "worker_task_log_format": "[%(asctime)s: %(levelname)s/%(processName)s][%(task_name)s(%(task_id)s)] %(message)s",
        "worker_hijack_root_logger": False,
        "worker_log_color": True,
        "task_always_eager": False,
        "task_eager_propagates": True,
    })
elif settings.APP_ENV == "testing":
    celery_config.update({
        "task_always_eager": True,
        "task_eager_propagates": True,
        "broker_url": "memory://",
        "result_backend": "cache+memory://",
    })

# Create Celery app instance
def create_celery_app() -> Celery:
    """
    Create and configure Celery application.
    
    Returns:
        Celery: Configured Celery application instance
    """
    celery_app = Celery("plant_care")
    celery_app.config_from_object(celery_config)
    
    # Update task base class for better error handling
    class CallbackTask(celery_app.Task):
        """A task that calls callbacks on success/failure."""
        
        def on_success(self, retval, task_id, args, kwargs):
            """Called when task succeeds."""
            from app.shared.utils.logging import get_logger
            logger = get_logger(__name__)
            logger.info(
                "Task completed successfully",
                task_id=task_id,
                task_name=self.name,
                result=retval,
            )
        
        def on_failure(self, exc, task_id, args, kwargs, einfo):
            """Called when task fails."""
            from app.shared.utils.logging import get_logger
            logger = get_logger(__name__)
            logger.error(
                "Task failed",
                task_id=task_id,
                task_name=self.name,
                error=str(exc),
                traceback=str(einfo),
            )
    
    celery_app.Task = CallbackTask
    
    return celery_app

# Export the configured Celery app
celery_app = create_celery_app()