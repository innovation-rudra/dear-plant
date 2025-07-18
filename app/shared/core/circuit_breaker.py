"""
app/shared/core/circuit_breaker.py
Plant Care Application - Circuit Breaker Pattern

Implements circuit breaker pattern for the Plant Care Application core services.
Provides resilience and graceful degradation for internal and external service calls.
Integrates with existing Plant Care infrastructure.
"""
import time
import asyncio
from typing import Any, Callable, Dict, Optional, TypeVar, Generic, Union
from dataclasses import dataclass, field
from enum import Enum
import functools
import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.core.exceptions import (
    PlantCareException,
    ExternalAPIError,
    ExternalAPIUnavailableError,
    CircuitBreakerOpenError
)
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

T = TypeVar('T')

class CircuitState(Enum):
    """Circuit breaker states for Plant Care services."""
    CLOSED = "closed"      # Normal operation - requests flow through
    OPEN = "open"          # Circuit is open - failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered

@dataclass
class CircuitBreakerConfig:
    """Configuration for Plant Care circuit breaker."""
    failure_threshold: int = 5          # Number of failures to open circuit
    recovery_timeout: int = 60          # Seconds to wait before trying again
    success_threshold: int = 3          # Successes needed to close circuit
    timeout: int = 30                   # Request timeout in seconds
    expected_exception: type = Exception
    name: str = "default"

@dataclass
class CircuitBreakerStats:
    """Statistics for Plant Care circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0
    consecutive_failures: int = 0
    consecutive_successes: int = 0

class PlantCareCircuitBreaker:
    """
    Circuit breaker for Plant Care Application services.
    
    Provides resilience patterns for:
    - External API calls (Plant ID, Weather, AI)
    - Database operations
    - Cache operations  
    - Background job processing
    - File operations
    """
    
    def __init__(self, name: str, config: Optional[CircuitBreakerConfig] = None):
        self.name = name
        self.config = config or self._get_default_config(name)
        self.stats = CircuitBreakerStats()
        self._lock = asyncio.Lock()
        
        # Plant Care specific service configurations
        self.service_configs = {
            # External API services
            "plant_identification": CircuitBreakerConfig(
                name="plant_identification",
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2,
                timeout=45,
                expected_exception=ExternalAPIError
            ),
            "weather_api": CircuitBreakerConfig(
                name="weather_api", 
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=3,
                timeout=20,
                expected_exception=ExternalAPIError
            ),
            "ai_services": CircuitBreakerConfig(
                name="ai_services",
                failure_threshold=3,
                recovery_timeout=120,
                success_threshold=2,
                timeout=60,
                expected_exception=ExternalAPIError
            ),
            # Infrastructure services
            "supabase_storage": CircuitBreakerConfig(
                name="supabase_storage",
                failure_threshold=5,
                recovery_timeout=45,
                success_threshold=3,
                timeout=30,
                expected_exception=Exception
            ),
            "redis_cache": CircuitBreakerConfig(
                name="redis_cache",
                failure_threshold=10,
                recovery_timeout=30,
                success_threshold=5,
                timeout=10,
                expected_exception=Exception
            ),
            # Background services
            "notification_delivery": CircuitBreakerConfig(
                name="notification_delivery",
                failure_threshold=10,
                recovery_timeout=30,
                success_threshold=5,
                timeout=15,
                expected_exception=Exception
            ),
            "care_reminder_service": CircuitBreakerConfig(
                name="care_reminder_service",
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=3,
                timeout=30,
                expected_exception=Exception
            ),
            # Payment services
            "payment_gateway": CircuitBreakerConfig(
                name="payment_gateway",
                failure_threshold=2,
                recovery_timeout=300,  # 5 minutes for payment issues
                success_threshold=3,
                timeout=30,
                expected_exception=Exception
            )
        }
        
        # Use service-specific config if available
        if name in self.service_configs:
            self.config = self.service_configs[name]
    
    def _get_default_config(self, name: str) -> CircuitBreakerConfig:
        """Get default configuration for service."""
        return CircuitBreakerConfig(name=name)
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            CircuitBreakerOpenError: If circuit is open
            Original exception: If function fails
        """
        async with self._lock:
            self.stats.total_requests += 1
            
            # Check if circuit should be opened
            if self._should_open_circuit():
                await self._open_circuit()
            
            # If circuit is open, fail fast
            if self.stats.state == CircuitState.OPEN:
                if not self._should_attempt_reset():
                    await self._log_circuit_open()
                    raise CircuitBreakerOpenError(
                        f"Circuit breaker '{self.name}' is open. Service unavailable."
                    )
                else:
                    # Move to half-open to test service
                    await self._half_open_circuit()
        
        # Execute function
        try:
            # Add timeout if configured
            if self.config.timeout > 0:
                result = await asyncio.wait_for(
                    self._execute_function(func, *args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                result = await self._execute_function(func, *args, **kwargs)
            
            # Record success
            await self._record_success()
            return result
            
        except asyncio.TimeoutError:
            await self._record_failure("timeout")
            raise ExternalAPIError(f"Service '{self.name}' timeout after {self.config.timeout}s")
            
        except self.config.expected_exception as e:
            await self._record_failure(str(e))
            raise
            
        except Exception as e:
            await self._record_failure(str(e))
            raise
    
    async def _execute_function(self, func: Callable[..., T], *args, **kwargs) -> T:
        """Execute the function (sync or async)."""
        if asyncio.iscoroutinefunction(func):
            return await func(*args, **kwargs)
        else:
            # Run sync function in executor to avoid blocking
            loop = asyncio.get_event_loop()
            return await loop.run_in_executor(None, functools.partial(func, *args, **kwargs))
    
    def _should_open_circuit(self) -> bool:
        """Check if circuit should be opened based on failure threshold."""
        return (
            self.stats.state == CircuitState.CLOSED and
            self.stats.consecutive_failures >= self.config.failure_threshold
        )
    
    def _should_attempt_reset(self) -> bool:
        """Check if circuit should attempt reset (move to half-open)."""
        if self.stats.state != CircuitState.OPEN:
            return False
        
        if not self.stats.last_failure_time:
            return True
        
        return (time.time() - self.stats.last_failure_time) >= self.config.recovery_timeout
    
    async def _open_circuit(self):
        """Open the circuit."""
        self.stats.state = CircuitState.OPEN
        self.stats.failure_count += 1
        
        logger.warning(
            "Circuit breaker opened",
            service_name=self.name,
            failure_count=self.stats.failure_count,
            consecutive_failures=self.stats.consecutive_failures
        )
        
        # Log security event for critical services
        if self.name in ["payment_gateway", "supabase_storage"]:
            log_security_event(
                event_type="circuit_breaker_opened",
                service_name=self.name,
                failure_count=self.stats.failure_count
            )
        
        # Store circuit state in Redis for monitoring
        await self._persist_circuit_state()
    
    async def _half_open_circuit(self):
        """Move circuit to half-open state."""
        self.stats.state = CircuitState.HALF_OPEN
        self.stats.success_count = 0  # Reset success counter
        
        logger.info(
            "Circuit breaker half-opened",
            service_name=self.name,
            recovery_attempt=True
        )
    
    async def _close_circuit(self):
        """Close the circuit (back to normal operation)."""
        self.stats.state = CircuitState.CLOSED
        self.stats.failure_count = 0
        self.stats.consecutive_failures = 0
        
        logger.info(
            "Circuit breaker closed",
            service_name=self.name,
            recovery_successful=True
        )
        
        # Clear persisted state
        await self._clear_circuit_state()
    
    async def _record_success(self):
        """Record successful function execution."""
        async with self._lock:
            self.stats.total_successes += 1
            self.stats.consecutive_successes += 1
            self.stats.consecutive_failures = 0
            self.stats.last_success_time = time.time()
            
            # If in half-open state, check if we should close
            if self.stats.state == CircuitState.HALF_OPEN:
                self.stats.success_count += 1
                if self.stats.success_count >= self.config.success_threshold:
                    await self._close_circuit()
    
    async def _record_failure(self, error: str):
        """Record failed function execution."""
        async with self._lock:
            self.stats.total_failures += 1
            self.stats.consecutive_failures += 1
            self.stats.consecutive_successes = 0
            self.stats.last_failure_time = time.time()
            
            logger.warning(
                "Circuit breaker recorded failure",
                service_name=self.name,
                error=error,
                consecutive_failures=self.stats.consecutive_failures,
                failure_threshold=self.config.failure_threshold
            )
            
            # If in half-open state, immediately go back to open
            if self.stats.state == CircuitState.HALF_OPEN:
                await self._open_circuit()
    
    async def _log_circuit_open(self):
        """Log circuit open event."""
        logger.error(
            "Circuit breaker is open - failing fast",
            service_name=self.name,
            state=self.stats.state.value,
            last_failure_time=self.stats.last_failure_time,
            recovery_timeout=self.config.recovery_timeout
        )
    
    async def _persist_circuit_state(self):
        """Persist circuit breaker state to Redis for monitoring."""
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            
            circuit_data = {
                "state": self.stats.state.value,
                "failure_count": self.stats.failure_count,
                "consecutive_failures": self.stats.consecutive_failures,
                "last_failure_time": self.stats.last_failure_time,
                "recovery_timeout": self.config.recovery_timeout,
                "service_name": self.name
            }
            
            await redis_client.setex(
                f"circuit_breaker:{self.name}",
                300,  # 5 minutes TTL
                str(circuit_data)
            )
            
        except Exception as e:
            logger.error("Failed to persist circuit state", error=str(e))
    
    async def _clear_circuit_state(self):
        """Clear persisted circuit state."""
        try:
            redis_manager = get_redis_manager()
            redis_client = await redis_manager.get_client()
            await redis_client.delete(f"circuit_breaker:{self.name}")
        except Exception as e:
            logger.error("Failed to clear circuit state", error=str(e))
    
    def get_stats(self) -> Dict[str, Any]:
        """Get current circuit breaker statistics."""
        return {
            "name": self.name,
            "state": self.stats.state.value,
            "total_requests": self.stats.total_requests,
            "total_successes": self.stats.total_successes,
            "total_failures": self.stats.total_failures,
            "consecutive_failures": self.stats.consecutive_failures,
            "consecutive_successes": self.stats.consecutive_successes,
            "failure_threshold": self.config.failure_threshold,
            "success_threshold": self.config.success_threshold,
            "recovery_timeout": self.config.recovery_timeout,
            "last_failure_time": self.stats.last_failure_time,
            "last_success_time": self.stats.last_success_time,
            "success_rate": (
                self.stats.total_successes / self.stats.total_requests 
                if self.stats.total_requests > 0 else 0
            )
        }
    
    async def reset(self):
        """Manually reset circuit breaker (admin function)."""
        async with self._lock:
            self.stats = CircuitBreakerStats()
            await self._clear_circuit_state()
            
            logger.info(
                "Circuit breaker manually reset",
                service_name=self.name
            )

# Global circuit breakers for Plant Care services
_circuit_breakers: Dict[str, PlantCareCircuitBreaker] = {}

def get_circuit_breaker(service_name: str) -> PlantCareCircuitBreaker:
    """Get or create circuit breaker for a service."""
    if service_name not in _circuit_breakers:
        _circuit_breakers[service_name] = PlantCareCircuitBreaker(service_name)
    return _circuit_breakers[service_name]

# Decorator for easy circuit breaker usage
def circuit_breaker(service_name: str, config: Optional[CircuitBreakerConfig] = None):
    """
    Decorator to add circuit breaker protection to functions.
    
    Usage:
        @circuit_breaker("plant_identification")
        async def identify_plant(image_data):
            # Function implementation
            pass
    """
    def decorator(func: Callable[..., T]) -> Callable[..., T]:
        cb = PlantCareCircuitBreaker(service_name, config)
        
        @functools.wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await cb.call(func, *args, **kwargs)
        
        return wrapper
    return decorator

# Convenience functions for Plant Care services
async def with_circuit_breaker(
    service_name: str, 
    func: Callable[..., T], 
    *args, 
    **kwargs
) -> T:
    """Execute function with circuit breaker protection."""
    cb = get_circuit_breaker(service_name)
    return await cb.call(func, *args, **kwargs)

async def get_all_circuit_breaker_stats() -> Dict[str, Dict[str, Any]]:
    """Get stats for all active circuit breakers."""
    return {
        name: cb.get_stats() 
        for name, cb in _circuit_breakers.items()
    }

async def reset_circuit_breaker(service_name: str) -> bool:
    """Reset specific circuit breaker (admin function)."""
    if service_name in _circuit_breakers:
        await _circuit_breakers[service_name].reset()
        return True
    return False

async def reset_all_circuit_breakers():
    """Reset all circuit breakers (admin function)."""
    for cb in _circuit_breakers.values():
        await cb.reset()
    
    logger.info("All circuit breakers reset", count=len(_circuit_breakers))