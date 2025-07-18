"""
app/shared/core/event_bus.py
Plant Care Application - Internal Event System

Core event bus for Plant Care Application module communication.
Implements domain-driven design patterns for decoupled module interaction.
Integrates with existing Plant Care infrastructure and event base classes.
"""
import asyncio
import uuid
from typing import Any, Dict, List, Callable, Optional, Type, Union
from datetime import datetime,timedelta
from dataclasses import dataclass, field
from enum import Enum
import structlog
import json

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.events.base import BaseEvent, EventType, publish_event
from app.shared.core.exceptions import PlantCareException, EventProcessingError
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class EventPriority(Enum):
    """Event priority levels for Plant Care operations."""
    LOW = "low"           # Analytics, non-critical updates
    NORMAL = "normal"     # Standard operations
    HIGH = "high"         # Care reminders, health alerts
    CRITICAL = "critical" # Security events, payment failures

@dataclass
class EventBusConfig:
    """Configuration for Plant Care event bus."""
    max_retries: int = 3
    retry_delay: float = 1.0  # seconds
    dead_letter_queue: bool = True
    persistence_enabled: bool = True
    redis_stream_name: str = "plant_care_events"
    max_stream_length: int = 10000

class PlantCareEventBus:
    """
    Internal event bus for Plant Care Application.
    
    Provides decoupled communication between modules:
    - User Management events
    - Plant Management events  
    - Care Management events
    - Health Monitoring events
    - Growth Tracking events
    - Community events
    - AI Feature events
    - Analytics events
    """
    
    def __init__(self, config: Optional[EventBusConfig] = None):
        self.config = config or EventBusConfig()
        self._handlers: Dict[EventType, List[Callable]] = {}
        self._async_handlers: Dict[EventType, List[Callable]] = {}
        self._middleware: List[Callable] = []
        self._subscribers: Dict[str, List[EventType]] = {}
        self._processing_stats = {
            "total_events": 0,
            "successful_events": 0,
            "failed_events": 0,
            "retry_attempts": 0
        }
        
        # Plant Care specific event routing
        self.module_routing = {
            # User Management events
            EventType.USER_REGISTERED: ["analytics_insights", "notification_communication"],
            EventType.USER_SUBSCRIPTION_CHANGED: ["payment_subscription", "analytics_insights"],
            
            # Plant Management events
            EventType.PLANT_ADDED: ["care_management", "analytics_insights", "ai_smart_features"],
            EventType.PLANT_IDENTIFIED: ["care_management", "content_management"],
            EventType.PLANT_PHOTO_UPLOADED: ["growth_tracking", "ai_smart_features"],
            
            # Care Management events
            EventType.CARE_TASK_COMPLETED: ["analytics_insights", "growth_tracking"],
            EventType.CARE_TASK_OVERDUE: ["notification_communication", "analytics_insights"],
            EventType.CARE_REMINDER_SENT: ["analytics_insights"],
            
            # Health Monitoring events
            EventType.HEALTH_ALERT_TRIGGERED: ["notification_communication", "care_management"],
            EventType.HEALTH_DIAGNOSIS_COMPLETED: ["care_management", "ai_smart_features"],
            
            # Growth Tracking events
            EventType.GROWTH_MILESTONE_ACHIEVED: ["notification_communication", "community_social"],
            EventType.GROWTH_PHOTO_ADDED: ["ai_smart_features", "analytics_insights"],
            
            # Community events
            EventType.COMMUNITY_POST_CREATED: ["notification_communication", "analytics_insights"],
            EventType.COMMUNITY_EXPERT_ADVICE_PROVIDED: ["notification_communication"],
            
            # AI events
            EventType.AI_RECOMMENDATION_GENERATED: ["care_management", "analytics_insights"],
            
            # Weather events
            EventType.WEATHER_ALERT_ISSUED: ["care_management", "notification_communication"],
            
            # Analytics events
            EventType.ANALYTICS_INSIGHT_GENERATED: ["notification_communication"],
            
            # Payment events
            EventType.SUBSCRIPTION_ACTIVATED: ["user_management", "analytics_insights"],
            EventType.PAYMENT_FAILED: ["notification_communication", "user_management"]
        }
    
    def subscribe(
        self, 
        event_type: EventType, 
        handler: Callable, 
        subscriber_id: str,
        async_handler: bool = True
    ):
        """
        Subscribe to Plant Care events.
        
        Args:
            event_type: Type of event to subscribe to
            handler: Function to handle the event
            subscriber_id: Unique identifier for subscriber (module name)
            async_handler: Whether handler is async
        """
        try:
            if async_handler:
                if event_type not in self._async_handlers:
                    self._async_handlers[event_type] = []
                self._async_handlers[event_type].append(handler)
            else:
                if event_type not in self._handlers:
                    self._handlers[event_type] = []
                self._handlers[event_type].append(handler)
            
            # Track subscriber
            if subscriber_id not in self._subscribers:
                self._subscribers[subscriber_id] = []
            if event_type not in self._subscribers[subscriber_id]:
                self._subscribers[subscriber_id].append(event_type)
            
            logger.info(
                "Event handler subscribed",
                event_type=event_type.value,
                subscriber_id=subscriber_id,
                handler_name=handler.__name__,
                async_handler=async_handler
            )
            
        except Exception as e:
            logger.error(
                "Failed to subscribe event handler",
                event_type=event_type.value,
                subscriber_id=subscriber_id,
                error=str(e)
            )
            raise
    
    def unsubscribe(self, event_type: EventType, handler: Callable, subscriber_id: str):
        """Unsubscribe from events."""
        try:
            # Remove from async handlers
            if event_type in self._async_handlers:
                if handler in self._async_handlers[event_type]:
                    self._async_handlers[event_type].remove(handler)
            
            # Remove from sync handlers
            if event_type in self._handlers:
                if handler in self._handlers[event_type]:
                    self._handlers[event_type].remove(handler)
            
            # Update subscriber tracking
            if subscriber_id in self._subscribers:
                if event_type in self._subscribers[subscriber_id]:
                    self._subscribers[subscriber_id].remove(event_type)
            
            logger.info(
                "Event handler unsubscribed",
                event_type=event_type.value,
                subscriber_id=subscriber_id,
                handler_name=handler.__name__
            )
            
        except Exception as e:
            logger.error(
                "Failed to unsubscribe event handler",
                error=str(e)
            )
    
    async def publish(
        self, 
        event: BaseEvent, 
        priority: EventPriority = EventPriority.NORMAL,
        correlation_id: Optional[str] = None
    ):
        """
        Publish event to Plant Care event bus.
        
        Args:
            event: Event to publish
            priority: Event priority level
            correlation_id: Optional correlation ID for tracking
        """
        try:
            # Set correlation ID if provided
            if correlation_id:
                event.correlation_id = correlation_id
            
            # Add metadata
            event.metadata.update({
                "priority": priority.value,
                "bus_timestamp": datetime.utcnow().isoformat(),
                "source_module": "event_bus"
            })
            
            self._processing_stats["total_events"] += 1
            
            logger.info(
                "Publishing event",
                event_type=event.event_type.value,
                event_id=event.event_id,
                priority=priority.value,
                correlation_id=correlation_id
            )
            
            # Apply middleware
            processed_event = await self._apply_middleware(event)
            
            # Persist event if enabled
            if self.config.persistence_enabled:
                await self._persist_event(processed_event)
            
            # Route to specific modules based on event type
            await self._route_to_modules(processed_event)
            
            # Publish to registered handlers
            await self._publish_to_handlers(processed_event)
            
            # Use the base event system for additional processing
            await publish_event(processed_event, persist=False)  # Already persisted above
            
            self._processing_stats["successful_events"] += 1
            
            logger.info(
                "Event published successfully",
                event_type=event.event_type.value,
                event_id=event.event_id
            )
            
        except Exception as e:
            self._processing_stats["failed_events"] += 1
            
            logger.error(
                "Failed to publish event",
                event_type=event.event_type.value,
                event_id=event.event_id,
                error=str(e)
            )
            
            # Send to dead letter queue if enabled
            if self.config.dead_letter_queue:
                await self._send_to_dead_letter_queue(event, str(e))
            
            raise EventProcessingError(f"Failed to publish event: {str(e)}")
    
    async def _apply_middleware(self, event: BaseEvent) -> BaseEvent:
        """Apply middleware to event."""
        processed_event = event
        
        for middleware in self._middleware:
            try:
                if asyncio.iscoroutinefunction(middleware):
                    processed_event = await middleware(processed_event)
                else:
                    processed_event = middleware(processed_event)
            except Exception as e:
                logger.error(
                    "Middleware processing failed",
                    middleware=middleware.__name__,
                    error=str(e)
                )
                # Continue with unprocessed event
                break
        
        return processed_event
    
    async def _route_to_modules(self, event: BaseEvent):
        """Route event to specific Plant Care modules."""
        target_modules = self.module_routing.get(event.event_type, [])
        
        for module_name in target_modules:
            try:
                # Create module-specific event routing
                module_event_key = f"module_events:{module_name}"
                
                # This would integrate with module-specific event queues
                # For now, we'll log the routing
                logger.debug(
                    "Routing event to module",
                    event_type=event.event_type.value,
                    target_module=module_name,
                    event_id=event.event_id
                )
                
            except Exception as e:
                logger.error(
                    "Failed to route event to module",
                    module_name=module_name,
                    event_type=event.event_type.value,
                    error=str(e)
                )
    
    async def _publish_to_handlers(self, event: BaseEvent):
        """Publish event to registered handlers."""
        # Get handlers for this event type
        async_handlers = self._async_handlers.get(event.event_type, [])
        sync_handlers = self._handlers.get(event.event_type, [])
        
        # Execute async handlers concurrently
        if async_handlers:
            tasks = []
            for handler in async_handlers:
                task = asyncio.create_task(
                    self._execute_async_handler(handler, event)
                )
                tasks.append(task)
            
            # Wait for all handlers with timeout
            try:
                await asyncio.wait_for(
                    asyncio.gather(*tasks, return_exceptions=True),
                    timeout=30.0  # 30 second timeout
                )
            except asyncio.TimeoutError:
                logger.warning(
                    "Some event handlers timed out",
                    event_type=event.event_type.value,
                    handler_count=len(async_handlers)
                )
        
        # Execute sync handlers
        for handler in sync_handlers:
            try:
                handler(event)
            except Exception as e:
                logger.error(
                    "Sync event handler failed",
                    handler=handler.__name__,
                    event_type=event.event_type.value,
                    error=str(e)
                )
    
    async def _execute_async_handler(self, handler: Callable, event: BaseEvent):
        """Execute async event handler with error handling and retries."""
        retry_count = 0
        
        while retry_count <= self.config.max_retries:
            try:
                await handler(event)
                return  # Success
                
            except Exception as e:
                retry_count += 1
                self._processing_stats["retry_attempts"] += 1
                
                logger.warning(
                    "Event handler failed",
                    handler=handler.__name__,
                    event_type=event.event_type.value,
                    retry_count=retry_count,
                    max_retries=self.config.max_retries,
                    error=str(e)
                )
                
                if retry_count <= self.config.max_retries:
                    # Wait before retry
                    await asyncio.sleep(self.config.retry_delay * retry_count)
                else:
                    # Max retries exceeded
                    logger.error(
                        "Event handler failed after max retries",
                        handler=handler.__name__,
                        event_type=event.event_type.value,
                        error=str(e)
                    )
                    
                    # Send to dead letter queue
                    if self.config.dead_letter_queue:
                        await self._send_to_dead_letter_queue(event, str(e))
    
    async def _persist_event(self, event: BaseEvent):
        """Persist event to Redis stream for audit and replay."""
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            
            # Prepare event data for Redis stream
            event_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "user_id": event.user_id or "",
                "correlation_id": event.correlation_id or "",
                "metadata": json.dumps(event.metadata),
                "data": json.dumps(event._get_event_data())
            }
            
            # Add to Redis stream
            await redis_client.xadd(
                self.config.redis_stream_name,
                event_data,
                maxlen=self.config.max_stream_length
            )
            
            logger.debug(
                "Event persisted to Redis stream",
                event_id=event.event_id,
                stream_name=self.config.redis_stream_name
            )
            
        except Exception as e:
            logger.error(
                "Failed to persist event",
                event_id=event.event_id,
                error=str(e)
            )
            # Don't fail event processing if persistence fails
    
    async def _send_to_dead_letter_queue(self, event: BaseEvent, error: str):
        """Send failed event to dead letter queue."""
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            
            dlq_data = {
                "event_id": event.event_id,
                "event_type": event.event_type.value,
                "timestamp": event.timestamp.isoformat(),
                "error": error,
                "retry_count": self.config.max_retries,
                "failed_at": datetime.utcnow().isoformat(),
                "data": json.dumps(event._get_event_data())
            }
            
            await redis_client.xadd(
                f"{self.config.redis_stream_name}_dlq",
                dlq_data,
                maxlen=1000  # Keep last 1000 failed events
            )
            
            logger.info(
                "Event sent to dead letter queue",
                event_id=event.event_id,
                error=error
            )
            
        except Exception as e:
            logger.error(
                "Failed to send event to dead letter queue",
                event_id=event.event_id,
                error=str(e)
            )
    
    def add_middleware(self, middleware: Callable):
        """Add middleware to event processing pipeline."""
        self._middleware.append(middleware)
        
        logger.info(
            "Event middleware added",
            middleware=middleware.__name__
        )
    
    def remove_middleware(self, middleware: Callable):
        """Remove middleware from event processing pipeline."""
        if middleware in self._middleware:
            self._middleware.remove(middleware)
            
            logger.info(
                "Event middleware removed",
                middleware=middleware.__name__
            )
    
    async def replay_events(
        self, 
        event_type: Optional[EventType] = None,
        start_time: Optional[datetime] = None,
        end_time: Optional[datetime] = None,
        max_events: int = 1000
    ) -> List[BaseEvent]:
        """
        Replay events from Redis stream.
        
        Args:
            event_type: Filter by event type
            start_time: Start time for replay
            end_time: End time for replay
            max_events: Maximum events to replay
            
        Returns:
            List of replayed events
        """
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            
            # Read from Redis stream
            stream_data = await redis_client.xrevrange(
                self.config.redis_stream_name,
                count=max_events
            )
            
            replayed_events = []
            
            for stream_id, event_data in stream_data:
                try:
                    # Filter by event type if specified
                    if event_type and event_data.get("event_type") != event_type.value:
                        continue
                    
                    # Filter by time range if specified
                    event_timestamp = datetime.fromisoformat(event_data["timestamp"])
                    if start_time and event_timestamp < start_time:
                        continue
                    if end_time and event_timestamp > end_time:
                        continue
                    
                    # This would reconstruct the event object
                    # For now, we'll return the event data
                    replayed_events.append(event_data)
                    
                except Exception as e:
                    logger.error(
                        "Failed to process replayed event",
                        stream_id=stream_id,
                        error=str(e)
                    )
            
            logger.info(
                "Events replayed",
                count=len(replayed_events),
                event_type=event_type.value if event_type else "all"
            )
            
            return replayed_events
            
        except Exception as e:
            logger.error("Failed to replay events", error=str(e))
            return []
    
    def get_stats(self) -> Dict[str, Any]:
        """Get event bus statistics."""
        return {
            "processing_stats": self._processing_stats.copy(),
            "subscribers": {
                subscriber: [et.value for et in event_types]
                for subscriber, event_types in self._subscribers.items()
            },
            "handler_counts": {
                "async_handlers": sum(len(handlers) for handlers in self._async_handlers.values()),
                "sync_handlers": sum(len(handlers) for handlers in self._handlers.values())
            },
            "middleware_count": len(self._middleware),
            "config": {
                "max_retries": self.config.max_retries,
                "retry_delay": self.config.retry_delay,
                "dead_letter_queue": self.config.dead_letter_queue,
                "persistence_enabled": self.config.persistence_enabled
            }
        }
    
    async def get_health_status(self) -> Dict[str, Any]:
        """Get event bus health status."""
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            
            # Check Redis connectivity
            await redis_client.ping()
            redis_healthy = True
            
            # Get stream info
            try:
                stream_info = await redis_client.xinfo_stream(self.config.redis_stream_name)
                stream_length = stream_info.get("length", 0)
            except:
                stream_length = 0
            
        except Exception:
            redis_healthy = False
            stream_length = 0
        
        success_rate = (
            self._processing_stats["successful_events"] / self._processing_stats["total_events"]
            if self._processing_stats["total_events"] > 0 else 0
        )
        
        return {
            "healthy": redis_healthy and success_rate > 0.95,
            "redis_connected": redis_healthy,
            "stream_length": stream_length,
            "success_rate": success_rate,
            "total_events_processed": self._processing_stats["total_events"],
            "failed_events": self._processing_stats["failed_events"],
            "active_subscribers": len(self._subscribers)
        }

# Global event bus instance
_plant_care_event_bus: Optional[PlantCareEventBus] = None

def get_event_bus() -> PlantCareEventBus:
    """Get the global Plant Care event bus instance."""
    global _plant_care_event_bus
    if _plant_care_event_bus is None:
        _plant_care_event_bus = PlantCareEventBus()
    return _plant_care_event_bus

# Convenience functions for Plant Care modules
async def publish_plant_care_event(
    event: BaseEvent,
    priority: EventPriority = EventPriority.NORMAL,
    correlation_id: Optional[str] = None
):
    """Publish event to Plant Care event bus."""
    event_bus = get_event_bus()
    await event_bus.publish(event, priority, correlation_id)

def subscribe_to_plant_care_event(
    event_type: EventType,
    subscriber_id: str,
    async_handler: bool = True
):
    """Decorator for subscribing to Plant Care events."""
    def decorator(handler: Callable):
        event_bus = get_event_bus()
        event_bus.subscribe(event_type, handler, subscriber_id, async_handler)
        return handler
    return decorator

# Plant Care specific event publishing helpers
async def publish_user_event(event: BaseEvent, user_id: str):
    """Publish user-related event."""
    event.user_id = user_id
    await publish_plant_care_event(event, EventPriority.NORMAL)

async def publish_plant_event(event: BaseEvent, user_id: str, plant_id: str):
    """Publish plant-related event."""
    event.user_id = user_id
    event.metadata["plant_id"] = plant_id
    await publish_plant_care_event(event, EventPriority.NORMAL)

async def publish_care_event(event: BaseEvent, user_id: str, plant_id: str):
    """Publish care-related event."""
    event.user_id = user_id
    event.metadata["plant_id"] = plant_id
    await publish_plant_care_event(event, EventPriority.HIGH)

async def publish_health_alert(event: BaseEvent, user_id: str, plant_id: str):
    """Publish health alert event with high priority."""
    event.user_id = user_id
    event.metadata["plant_id"] = plant_id
    await publish_plant_care_event(event, EventPriority.CRITICAL)

async def publish_system_event(event: BaseEvent):
    """Publish system-level event."""
    await publish_plant_care_event(event, EventPriority.HIGH)

# Event bus management functions
async def get_event_bus_stats() -> Dict[str, Any]:
    """Get event bus statistics."""
    event_bus = get_event_bus()
    return event_bus.get_stats()

async def get_event_bus_health() -> Dict[str, Any]:
    """Get event bus health status."""
    event_bus = get_event_bus()
    return await event_bus.get_health_status()

async def replay_plant_care_events(
    event_type: Optional[EventType] = None,
    hours_back: int = 24,
    max_events: int = 1000
) -> List[Any]:
    """Replay Plant Care events from the last N hours."""
    event_bus = get_event_bus()
    start_time = datetime.utcnow() - timedelta(hours=hours_back)
    return await event_bus.replay_events(
        event_type=event_type,
        start_time=start_time,
        max_events=max_events
    )