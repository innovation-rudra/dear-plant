"""
app/shared/core/__init__.py
Plant Care Application - Core Package Initialization

Central core package for Plant Care Application providing:
- Security and authentication utilities
- Exception handling and error management
- Circuit breaker patterns for resilience
- Event bus for module communication
- Rate limiting and abuse prevention
- FastAPI dependencies and middleware
"""

# Import core components
from app.shared.core.security import (
    security_manager,
    validate_jwt_token,
    check_permissions,
    hash_password,
    verify_password,
    generate_secure_token,
    generate_plant_care_api_key,
    encrypt_user_data,
    decrypt_user_data
)

from app.shared.core.exceptions import (
    PlantCareException,
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,
    ValidationError,
    ResourceNotFoundError,
    ResourceAlreadyExistsError,
    ExternalAPIError,
    ExternalAPIUnavailableError,
    RateLimitExceededError,
    CircuitBreakerOpenError,
    EventProcessingError
)

from app.shared.core.dependencies import (
    get_current_active_user,
    get_premium_user,
    get_expert_user,
    get_admin_user,
    get_plant_care_context,
    get_database_session,
    get_redis_session,
    CurrentUser,
    PremiumUser,
    ExpertUser,
    AdminUser,
    DatabaseSession,
    RedisSession,
    PlantCareContext
)

from app.shared.core.circuit_breaker import (
    PlantCareCircuitBreaker,
    CircuitBreakerConfig,
    CircuitState,
    get_circuit_breaker,
    circuit_breaker,
    with_circuit_breaker,
    get_all_circuit_breaker_stats,
    reset_circuit_breaker,
    reset_all_circuit_breakers
)

from app.shared.core.event_bus import (
    PlantCareEventBus,
    EventPriority,
    get_event_bus,
    publish_plant_care_event,
    subscribe_to_plant_care_event,
    publish_user_event,
    publish_plant_event,
    publish_care_event,
    publish_health_alert,
    publish_system_event,
    get_event_bus_stats,
    get_event_bus_health,
    replay_plant_care_events
)

from app.shared.core.rate_limiter import (
    PlantCareRateLimiter,
    RateLimitRule,
    RateLimitResult,
    RateLimitAlgorithm,
    RateLimitScope,
    get_rate_limiter,
    check_plant_care_rate_limit,
    check_user_rate_limit,
    check_ip_rate_limit,
    check_feature_rate_limit,
    check_plant_identification_limit,
    check_ai_chat_limit,
    check_file_upload_limit,
    check_analytics_limit,
    enforce_rate_limit,
    reset_user_rate_limits,
    get_rate_limit_stats
)

from app.shared.core.middleware import (
    setup_cors_middleware,
    setup_logging_middleware,
    setup_security_middleware,
    setup_rate_limiting_middleware
)

__version__ = "1.0.0"

__all__ = [
    # Security
    "security_manager",
    "validate_jwt_token", 
    "check_permissions",
    "hash_password",
    "verify_password",
    "generate_secure_token",
    "generate_plant_care_api_key",
    "encrypt_user_data",
    "decrypt_user_data",
    
    # Exceptions
    "PlantCareException",
    "AuthenticationError",
    "AuthorizationError", 
    "TokenExpiredError",
    "InvalidTokenError",
    "ValidationError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ExternalAPIError",
    "ExternalAPIUnavailableError",
    "RateLimitExceededError",
    "CircuitBreakerOpenError",
    "EventProcessingError",
    
    # Dependencies
    "get_current_active_user",
    "get_premium_user",
    "get_expert_user", 
    "get_admin_user",
    "get_plant_care_context",
    "get_database_session",
    "get_redis_session",
    "CurrentUser",
    "PremiumUser",
    "ExpertUser",
    "AdminUser",
    "DatabaseSession",
    "RedisSession",
    "PlantCareContext",
    
    # Circuit Breaker
    "PlantCareCircuitBreaker",
    "CircuitBreakerConfig",
    "CircuitState",
    "get_circuit_breaker",
    "circuit_breaker",
    "with_circuit_breaker",
    "get_all_circuit_breaker_stats",
    "reset_circuit_breaker",
    "reset_all_circuit_breakers",
    
    # Event Bus
    "PlantCareEventBus",
    "EventPriority",
    "get_event_bus",
    "publish_plant_care_event",
    "subscribe_to_plant_care_event",
    "publish_user_event",
    "publish_plant_event", 
    "publish_care_event",
    "publish_health_alert",
    "publish_system_event",
    "get_event_bus_stats",
    "get_event_bus_health",
    "replay_plant_care_events",
    
    # Rate Limiter
    "PlantCareRateLimiter",
    "RateLimitRule",
    "RateLimitResult",
    "RateLimitAlgorithm",
    "RateLimitScope",
    "get_rate_limiter",
    "check_plant_care_rate_limit",
    "check_user_rate_limit",
    "check_ip_rate_limit",
    "check_feature_rate_limit",
    "check_plant_identification_limit",
    "check_ai_chat_limit",
    "check_file_upload_limit",
    "check_analytics_limit",
    "enforce_rate_limit",
    "reset_user_rate_limits",
    "get_rate_limit_stats",
    
    # Middleware
    "setup_cors_middleware",
    "setup_logging_middleware",
    "setup_security_middleware",
    "setup_rate_limiting_middleware"
]

# Plant Care Application core configuration
PLANT_CARE_CORE_CONFIG = {
    "version": __version__,
    "components": {
        "security": {
            "enabled": True,
            "supabase_integration": True,
            "jwt_validation": True,
            "api_key_support": True,
            "rbac_enabled": True
        },
        "circuit_breaker": {
            "enabled": True,
            "services_monitored": [
                "plant_identification",
                "weather_api", 
                "ai_services",
                "supabase_storage",
                "redis_cache",
                "notification_delivery",
                "payment_gateway"
            ]
        },
        "event_bus": {
            "enabled": True,
            "persistence": True,
            "dead_letter_queue": True,
            "module_routing": True,
            "replay_support": True
        },
        "rate_limiter": {
            "enabled": True,
            "algorithms": ["sliding_window", "fixed_window", "token_bucket", "leaky_bucket"],
            "tier_support": True,
            "feature_limits": True,
            "abuse_prevention": True
        },
        "middleware": {
            "cors": True,
            "logging": True,
            "security": True,
            "rate_limiting": True,
            "error_handling": True
        }
    },
    "integrations": {
        "supabase": True,
        "redis": True,
        "fastapi": True,
        "prometheus": True,
        "sentry": True
    }
}

# Plant Care specific core utilities
class PlantCareCore:
    """
    Central manager for Plant Care Application core functionality.
    Provides unified access to all core components.
    """
    
    def __init__(self):
        self.security = security_manager
        self.circuit_breakers = {}
        self.event_bus = get_event_bus()
        self.rate_limiter = get_rate_limiter()
        self.initialized = False
    
    async def initialize(self):
        """Initialize all core components."""
        if self.initialized:
            return
        
        try:
            # Initialize circuit breakers for Plant Care services
            services = [
                "plant_identification",
                "weather_api",
                "ai_services", 
                "supabase_storage",
                "redis_cache",
                "notification_delivery",
                "payment_gateway"
            ]
            
            for service in services:
                self.circuit_breakers[service] = get_circuit_breaker(service)
            
            self.initialized = True
            
            # Publish system initialization event
            from app.shared.events.base import BaseEvent, EventType
            
            class SystemInitializedEvent(BaseEvent):
                event_type = EventType.SYSTEM_MAINTENANCE_COMPLETED
                
                def _get_event_data(self):
                    return {
                        "component": "plant_care_core",
                        "services_initialized": list(self.circuit_breakers.keys()),
                        "version": __version__
                    }
            
            await publish_system_event(SystemInitializedEvent())
            
        except Exception as e:
            import structlog
            logger = structlog.get_logger(__name__)
            logger.error("Failed to initialize Plant Care core", error=str(e))
            raise
    
    def get_status(self) -> dict:
        """Get status of all core components."""
        return {
            "initialized": self.initialized,
            "version": __version__,
            "components": {
                "security": {"enabled": True, "healthy": True},
                "circuit_breakers": {
                    name: cb.get_stats() 
                    for name, cb in self.circuit_breakers.items()
                },
                "event_bus": self.event_bus.get_stats() if self.initialized else {},
                "rate_limiter": get_rate_limit_stats()
            },
            "config": PLANT_CARE_CORE_CONFIG
        }
    
    async def health_check(self) -> dict:
        """Perform health check on all core components."""
        health = {
            "healthy": True,
            "components": {}
        }
        
        try:
            # Check event bus health
            if self.initialized:
                event_bus_health = await self.event_bus.get_health_status()
                health["components"]["event_bus"] = event_bus_health
                if not event_bus_health.get("healthy", False):
                    health["healthy"] = False
            
            # Check circuit breaker health
            circuit_health = await get_all_circuit_breaker_stats()
            health["components"]["circuit_breakers"] = circuit_health
            
            # Check if any circuit breakers are open
            for stats in circuit_health.values():
                if stats.get("state") == "open":
                    health["healthy"] = False
            
            # Rate limiter is always healthy if Redis is working
            health["components"]["rate_limiter"] = {"healthy": True}
            
        except Exception as e:
            health["healthy"] = False
            health["error"] = str(e)
        
        return health

# Global Plant Care core instance
_plant_care_core: PlantCareCore = None

def get_plant_care_core() -> PlantCareCore:
    """Get the global Plant Care core instance."""
    global _plant_care_core
    if _plant_care_core is None:
        _plant_care_core = PlantCareCore()
    return _plant_care_core

# Convenience functions for core functionality
async def initialize_plant_care_core():
    """Initialize Plant Care core components."""
    core = get_plant_care_core()
    await core.initialize()

def get_core_status() -> dict:
    """Get Plant Care core status."""
    core = get_plant_care_core()
    return core.get_status()

async def get_core_health() -> dict:
    """Get Plant Care core health status."""
    core = get_plant_care_core()
    return await core.health_check()

# Export the global instance for easy access
plant_care_core = get_plant_care_core()

def get_core_config() -> dict:
    """Get Plant Care core configuration."""
    return PLANT_CARE_CORE_CONFIG.copy()