"""
Plant Care Application - Structured Logging Configuration
"""
import logging
import sys
from typing import Any, Dict

import structlog
from structlog.typing import FilteringBoundLogger

from app.shared.config.settings import get_settings

# Get application settings
settings = get_settings()


def setup_logging() -> None:
    """
    Set up structured logging for the Plant Care Application.
    """
    # Configure structlog
    structlog.configure(
        processors=[
            # Add timestamp
            structlog.stdlib.add_log_level,
            structlog.stdlib.add_logger_name,
            structlog.processors.TimeStamper(fmt="ISO"),
            # Add plant care context
            add_plant_care_context,
            # Stack info for errors
            structlog.processors.StackInfoRenderer(),
            # Format exceptions
            structlog.dev.set_exc_info,
            # JSON formatting for production
            structlog.processors.JSONRenderer() if settings.is_production
            else structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Configure standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, settings.LOG_LEVEL.upper()),
    )

    # Set log levels for third-party libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(
        logging.INFO if settings.DEBUG else logging.WARNING
    )
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("redis").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)


def add_plant_care_context(logger: Any, method_name: str, event_dict: Dict[str, Any]) -> Dict[str, Any]:
    """
    Add Plant Care Application context to log entries.
    
    Args:
        logger: The logger instance
        method_name: The method name
        event_dict: The event dictionary
        
    Returns:
        Dict[str, Any]: Updated event dictionary
    """
    # Add application context
    event_dict["app"] = "plant_care"
    event_dict["version"] = settings.APP_VERSION
    event_dict["environment"] = settings.APP_ENV
    
    return event_dict


def get_logger(name: str) -> FilteringBoundLogger:
    """
    Get a structured logger instance.
    
    Args:
        name: Logger name (usually __name__)
        
    Returns:
        FilteringBoundLogger: Configured logger instance
    """
    return structlog.get_logger(name)


class LoggerMixin:
    """
    Mixin to add logging capabilities to classes.
    """
    
    @property
    def logger(self) -> FilteringBoundLogger:
        """Get logger for this class."""
        return get_logger(self.__class__.__module__ + "." + self.__class__.__name__)


# Plant Care specific log helpers
def log_user_action(user_id: str, action: str, **kwargs) -> None:
    """
    Log user actions for analytics.
    
    Args:
        user_id: User ID
        action: Action performed
        **kwargs: Additional context
    """
    logger = get_logger("user_actions")
    logger.info(
        "User action",
        user_id=user_id,
        action=action,
        **kwargs
    )


def log_plant_action(user_id: str, plant_id: str, action: str, **kwargs) -> None:
    """
    Log plant-related actions.
    
    Args:
        user_id: User ID
        plant_id: Plant ID
        action: Action performed
        **kwargs: Additional context
    """
    logger = get_logger("plant_actions")
    logger.info(
        "Plant action",
        user_id=user_id,
        plant_id=plant_id,
        action=action,
        **kwargs
    )


def log_api_call(api_name: str, endpoint: str, response_time: float, status_code: int, **kwargs) -> None:
    """
    Log external API calls.
    
    Args:
        api_name: Name of the API
        endpoint: API endpoint
        response_time: Response time in seconds
        status_code: HTTP status code
        **kwargs: Additional context
    """
    logger = get_logger("api_calls")
    logger.info(
        "External API call",
        api_name=api_name,
        endpoint=endpoint,
        response_time=response_time,
        status_code=status_code,
        **kwargs
    )


def log_performance(operation: str, duration: float, **kwargs) -> None:
    """
    Log performance metrics.
    
    Args:
        operation: Operation name
        duration: Duration in seconds
        **kwargs: Additional context
    """
    logger = get_logger("performance")
    logger.info(
        "Performance metric",
        operation=operation,
        duration=duration,
        **kwargs
    )


def log_error(error: Exception, context: Dict[str, Any] = None) -> None:
    """
    Log errors with context.
    
    Args:
        error: Exception that occurred
        context: Additional context
    """
    logger = get_logger("errors")
    logger.error(
        "Error occurred",
        error=str(error),
        error_type=type(error).__name__,
        context=context or {},
        exc_info=True
    )


def log_security_event(event_type: str, user_id: str = None, **kwargs) -> None:
    """
    Log security-related events.
    
    Args:
        event_type: Type of security event
        user_id: User ID if applicable
        **kwargs: Additional context
    """
    logger = get_logger("security")
    logger.warning(
        "Security event",
        event_type=event_type,
        user_id=user_id,
        **kwargs
    )


# Export logging utilities
__all__ = [
    "setup_logging",
    "get_logger",
    "LoggerMixin",
    "log_user_action",
    "log_plant_action",
    "log_api_call",
    "log_performance",
    "log_error",
    "log_security_event",
]