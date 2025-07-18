"""
app/shared/events/base.py
Plant Care Application - Event System Base

Base classes and utilities for domain events in the Plant Care Application.
Enables decoupled communication between modules for plant care operations.
"""
import uuid
import asyncio
from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any, Dict, List, Optional, Type, Callable, Awaitable
from dataclasses import dataclass, field
from enum import Enum
import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import get_redis_manager

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()


class EventType(Enum):
    """Plant Care Application event types."""
    
    # User Management Events
    USER_REGISTERED = "user.registered"
    USER_PROFILE_UPDATED = "user.profile_updated"
    USER_SUBSCRIPTION_CHANGED = "user.subscription_changed"
    USER_DELETED = "user.deleted"
    
    # Plant Management Events
    PLANT_ADDED = "plant.added"
    PLANT_UPDATED = "plant.updated"
    PLANT_DELETED = "plant.deleted"
    PLANT_IDENTIFIED = "plant.identified"
    PLANT_PHOTO_UPLOADED = "plant.photo_uploaded"
    
    # Care Management Events
    CARE_TASK_CREATED = "care.task_created"
    CARE_TASK_COMPLETED = "care.task_completed"
    CARE_TASK_OVERDUE = "care.task_overdue"
    CARE_SCHEDULE_UPDATED = "care.schedule_updated"
    CARE_REMINDER_SENT = "care.reminder_sent"
    
    # Health Monitoring Events
    HEALTH_ASSESSMENT_RECORDED = "health.assessment_recorded"
    HEALTH_ALERT_TRIGGERED = "health.alert_triggered"
    HEALTH_DIAGNOSIS_COMPLETED = "health.diagnosis_completed"
    HEALTH_TREATMENT_STARTED = "health.treatment_started"
    HEALTH_RECOVERY_DETECTED = "health.recovery_detected"
    
    # Growth Tracking Events
    GROWTH_PHOTO_ADDED = "growth.photo_added"
    GROWTH_MILESTONE_ACHIEVED = "growth.milestone_achieved"
    GROWTH_MEASUREMENT_RECORDED = "growth.measurement_recorded"
    GROWTH_ANALYSIS_COMPLETED = "growth.analysis_completed"
    
    # Community Events
    COMMUNITY_POST_CREATED = "community.post_created"
    COMMUNITY_POST_LIKED = "community.post_liked"
    COMMUNITY_POST_COMMENTED = "community.post_commented"
    COMMUNITY_EXPERT_ADVICE_REQUESTED = "community.expert_advice_requested"
    COMMUNITY_EXPERT_ADVICE_PROVIDED = "community.expert_advice_provided"
    
    # AI & Smart Features Events
    AI_CHAT_MESSAGE_SENT = "ai.chat_message_sent"
    AI_RECOMMENDATION_GENERATED = "ai.recommendation_generated"
    AI_AUTOMATION_RULE_TRIGGERED = "ai.automation_rule_triggered"
    
    # Weather & Environmental Events
    WEATHER_DATA_UPDATED = "weather.data_updated"
    WEATHER_ALERT_ISSUED = "weather.alert_issued"
    ENVIRONMENTAL_CHANGE_DETECTED = "environmental.change_detected"
    
    # Analytics Events
    ANALYTICS_DATA_PROCESSED = "analytics.data_processed"
    ANALYTICS_INSIGHT_GENERATED = "analytics.insight_generated"
    ANALYTICS_REPORT_CREATED = "analytics.report_created"
    
    # Notification Events
    NOTIFICATION_SENT = "notification.sent"
    NOTIFICATION_DELIVERED = "notification.delivered"
    NOTIFICATION_OPENED = "notification.opened"
    NOTIFICATION_FAILED = "notification.failed"
    
    # Payment Events
    PAYMENT_PROCESSED = "payment.processed"
    PAYMENT_FAILED = "payment.failed"
    SUBSCRIPTION_ACTIVATED = "subscription.activated"
    SUBSCRIPTION_CANCELLED = "subscription.cancelled"
    
    # System Events
    SYSTEM_ERROR_OCCURRED = "system.error_occurred"
    SYSTEM_MAINTENANCE_STARTED = "system.maintenance_started"
    SYSTEM_MAINTENANCE_COMPLETED = "system.maintenance_completed"


@dataclass
class BaseEvent(ABC):
    """
    Base class for all Plant Care domain events.
    """
    
    event_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    event_type: EventType = field(init=False)
    timestamp: datetime = field(default_factory=datetime.utcnow)
    user_id: Optional[str] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization to set event type."""
        if not hasattr(self, 'event_type') or self.event_type is None:
            raise ValueError("Event must define event_type")
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert event to dictionary for serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type.value,
            "timestamp": self.timestamp.isoformat(),
            "user_id": self.user_id,
            "correlation_id": self.correlation_id,
            "metadata": self.metadata,
            "data": self._get_event_data()
        }
    
    @abstractmethod
    def _get_event_data(self) -> Dict[str, Any]:
        """Get event-specific data."""
        pass


@dataclass
class PlantEvent(BaseEvent):
    """Base class for plant-related events."""
    
    plant_id: str = None
    plant_name: str = None
    species: str = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "plant_id": self.plant_id,
            "plant_name": self.plant_name,
            "species": self.species
        }


@dataclass
class CareEvent(BaseEvent):
    """Base class for care-related events."""
    
    plant_id: str = None
    care_type: str = None
    scheduled_date: Optional[datetime] = None
    completed_date: Optional[datetime] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "plant_id": self.plant_id,
            "care_type": self.care_type,
            "scheduled_date": self.scheduled_date.isoformat() if self.scheduled_date else None,
            "completed_date": self.completed_date.isoformat() if self.completed_date else None
        }


@dataclass
class HealthEvent(BaseEvent):
    """Base class for health-related events."""
    
    plant_id: str = None
    health_status: str = None
    severity: str = None
    symptoms: List[str] = field(default_factory=list)
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "plant_id": self.plant_id,
            "health_status": self.health_status,
            "severity": self.severity,
            "symptoms": self.symptoms
        }


@dataclass
class CommunityEvent(BaseEvent):
    """Base class for community-related events."""
    
    post_id: Optional[str] = None
    author_id: Optional[str] = None
    content_type: Optional[str] = None
    
    def _get_event_data(self) -> Dict[str, Any]:
        return {
            "post_id": self.post_id,
            "author_id": self.author_id,
            "content_type": self.content_type
        }


# Event Handler type
EventHandler = Callable[[BaseEvent], Awaitable[None]]


class EventBus:
    """
    Event bus for Plant Care Application.
    Handles event publishing, subscription, and delivery.
    """
    
    def __init__(self):
        self._handlers: Dict[EventType, List[EventHandler]] = {}
        self._redis_manager = None
        
    async def _get_redis_client(self):
        """Get Redis client for event persistence."""
        if not self._redis_manager:
            self._redis_manager = get_redis_manager()
        return await self._redis_manager.get_client()
    
    def subscribe(self, event_type: EventType, handler: EventHandler):
        """
        Subscribe to an event type.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Async function to handle the event
        """
        if event_type not in self._handlers:
            self._handlers[event_type] = []
        
        self._handlers[event_type].append(handler)
        
        logger.info(
            "Event handler subscribed",
            event_type=event_type.value,
            handler=handler.__name__
        )
    
    def unsubscribe(self, event_type: EventType, handler: EventHandler):
        """
        Unsubscribe from an event type.
        
        Args:
            event_type: Type of event to unsubscribe from
            handler: Handler function to remove
        """
        if event_type in self._handlers:
            try:
                self._handlers[event_type].remove(handler)
                logger.info(
                    "Event handler unsubscribed",
                    event_type=event_type.value,
                    handler=handler.__name__
                )
            except ValueError:
                logger.warning(
                    "Handler not found for unsubscription",
                    event_type=event_type.value,
                    handler=handler.__name__
                )
    
    async def publish(self, event: BaseEvent, persist: bool = True):
        """
        Publish an event to all subscribers.
        
        Args:
            event: Event to publish
            persist: Whether to persist event for audit trail
        """
        try:
            logger.info(
                "Publishing event",
                event_id=event.event_id,
                event_type=event.event_type.value,
                user_id=event.user_id
            )
            
            # Persist event if requested
            if persist:
                await self._persist_event(event)
            
            # Get handlers for this event type
            handlers = self._handlers.get(event.event_type, [])
            
            if not handlers:
                logger.debug(
                    "No handlers registered for event type",
                    event_type=event.event_type.value
                )
                return
            
            # Execute all handlers concurrently
            tasks = []
            for handler in handlers:
                task = asyncio.create_task(self._safe_handle_event(handler, event))
                tasks.append(task)
            
            # Wait for all handlers to complete
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            # Log any handler failures
            for i, result in enumerate(results):
                if isinstance(result, Exception):
                    logger.error(
                        "Event handler failed",
                        event_id=event.event_id,
                        event_type=event.event_type.value,
                        handler=handlers[i].__name__,
                        error=str(result)
                    )
            
            logger.info(
                "Event published successfully",
                event_id=event.event_id,
                event_type=event.event_type.value,
                handlers_executed=len(handlers)
            )
            
        except Exception as e:
            logger.error(
                "Error publishing event",
                event_id=event.event_id,
                event_type=event.event_type.value,
                error=str(e)
            )
            raise
    
    async def _safe_handle_event(self, handler: EventHandler, event: BaseEvent):
        """
        Safely execute an event handler with error handling.
        
        Args:
            handler: Event handler function
            event: Event to handle
        """
        try:
            await handler(event)
        except Exception as e:
            logger.error(
                "Event handler error",
                event_id=event.event_id,
                handler=handler.__name__,
                error=str(e)
            )
            # Don't re-raise to prevent one handler failure from affecting others
    
    async def _persist_event(self, event: BaseEvent):
        """
        Persist event to Redis for audit trail.
        
        Args:
            event: Event to persist
        """
        try:
            redis_client = await self._get_redis_client()
            
            # Store event data
            event_key = f"events:{event.event_type.value}:{event.event_id}"
            event_data = event.to_dict()
            
            # Store with TTL (30 days for audit trail)
            import json
            await redis_client.setex(
                event_key,
                30 * 24 * 60 * 60,  # 30 days
                json.dumps(event_data, default=str)
            )
            
            # Add to event stream for real-time processing
            stream_key = f"event_stream:{event.event_type.value}"
            await redis_client.xadd(
                stream_key,
                event_data,
                maxlen=1000  # Keep last 1000 events per type
            )
            
            logger.debug(
                "Event persisted",
                event_id=event.event_id,
                event_type=event.event_type.value
            )
            
        except Exception as e:
            logger.error(
                "Error persisting event",
                event_id=event.event_id,
                error=str(e)
            )
            # Don't fail event publishing if persistence fails
    
    async def get_events(
        self,
        event_type: Optional[EventType] = None,
        user_id: Optional[str] = None,
        limit: int = 100
    ) -> List[Dict[str, Any]]:
        """
        Retrieve events from the audit trail.
        
        Args:
            event_type: Filter by event type
            user_id: Filter by user ID
            limit: Maximum number of events to return
            
        Returns:
            List of event dictionaries
        """
        try:
            redis_client = await self._get_redis_client()
            events = []
            
            if event_type:
                # Get events for specific type from stream
                stream_key = f"event_stream:{event_type.value}"
                stream_events = await redis_client.xrevrange(stream_key, count=limit)
                
                for event_id, event_data in stream_events:
                    if user_id and event_data.get("user_id") != user_id:
                        continue
                    
                    events.append({
                        "stream_id": event_id,
                        **event_data
                    })
            
            return events
            
        except Exception as e:
            logger.error("Error retrieving events", error=str(e))
            return []


# Global event bus instance
_event_bus = None


def get_event_bus() -> EventBus:
    """Get the global event bus instance."""
    global _event_bus
    if _event_bus is None:
        _event_bus = EventBus()
    return _event_bus


# Convenience functions for common operations
async def publish_event(event: BaseEvent, persist: bool = True):
    """Publish an event using the global event bus."""
    event_bus = get_event_bus()
    await event_bus.publish(event, persist)


def subscribe_to_event(event_type: EventType):
    """Decorator for subscribing functions to events."""
    def decorator(handler: EventHandler):
        event_bus = get_event_bus()
        event_bus.subscribe(event_type, handler)
        return handler
    return decorator


# Event creation helpers
def create_correlation_id() -> str:
    """Create a correlation ID for tracking related events."""
    return str(uuid.uuid4())


def add_event_metadata(event: BaseEvent, **kwargs):
    """Add metadata to an event."""
    event.metadata.update(kwargs)