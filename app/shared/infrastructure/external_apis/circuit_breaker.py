"""
app/shared/infrastructure/external_apis/circuit_breaker.py
Plant Care Application - Circuit Breaker

Implements circuit breaker pattern for external API calls to prevent cascade failures.
Protects Plant Care Application from failing external services (plant ID, weather, AI APIs).
"""
import time
import asyncio
from typing import Any, Callable, Dict, Optional, TypeVar, Generic
from dataclasses import dataclass
from enum import Enum
import functools

import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import PlantCareCache
from app.shared.core.exceptions import ExternalAPIError, ExternalAPIUnavailableError
from app.shared.utils.logging import log_api_call

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)

T = TypeVar('T')


class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"      # Normal operation
    OPEN = "open"          # Circuit is open, failing fast
    HALF_OPEN = "half_open"  # Testing if service recovered


@dataclass
class CircuitBreakerConfig:
    """Configuration for circuit breaker."""
    failure_threshold: int = 5      # Number of failures to open circuit
    recovery_timeout: int = 60      # Seconds to wait before trying again
    success_threshold: int = 3      # Successes needed to close circuit
    timeout: int = 30              # Request timeout in seconds
    expected_exception: type = Exception


@dataclass
class CircuitBreakerStats:
    """Statistics for circuit breaker."""
    state: CircuitState = CircuitState.CLOSED
    failure_count: int = 0
    success_count: int = 0
    last_failure_time: Optional[float] = None
    last_success_time: Optional[float] = None
    total_requests: int = 0
    total_failures: int = 0
    total_successes: int = 0


class PlantCareCircuitBreaker:
    """
    Circuit breaker for Plant Care Application external API calls.
    Prevents cascade failures and provides graceful degradation.
    """
    
    def __init__(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ):
        self.name = name
        self.config = config or CircuitBreakerConfig()
        self.cache = PlantCareCache()
        
        # Plant Care specific circuit breaker configurations
        self.service_configs = {
            "plant_identification": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=30,
                success_threshold=2,
                timeout=45,
                expected_exception=ExternalAPIError
            ),
            "weather_api": CircuitBreakerConfig(
                failure_threshold=5,
                recovery_timeout=60,
                success_threshold=3,
                timeout=20,
                expected_exception=ExternalAPIError
            ),
            "ai_services": CircuitBreakerConfig(
                failure_threshold=3,
                recovery_timeout=120,
                success_threshold=2,
                timeout=60,
                expected_exception=ExternalAPIError
            ),
            "notification_services": CircuitBreakerConfig(
                failure_threshold=10,
                recovery_timeout=30,
                success_threshold=5,
                timeout=15,
                expected_exception=ExternalAPIError
            ),
            "payment_gateway": CircuitBreakerConfig(
                failure_threshold=2,
                recovery_timeout=300,  # 5 minutes
                success_threshold=3,
                timeout=30,
                expected_exception=ExternalAPIError
            )
        }
        
        # Use service-specific config if available
        if name in self.service_configs:
            self.config = self.service_configs[name]
    
    async def call(self, func: Callable[..., T], *args, **kwargs) -> T:
        """
        Execute function with circuit breaker protection.
        
        Args:
            func: Function to execute
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            T: Function result
            
        Raises:
            ExternalAPIUnavailableError: When circuit is open
            Exception: Original exception from function
        """
        stats = await self._get_stats()
        
        # Check if circuit should be opened
        if stats.state == CircuitState.CLOSED:
            if stats.failure_count >= self.config.failure_threshold:
                await self._open_circuit(stats)
        
        # Check if circuit should transition to half-open
        elif stats.state == CircuitState.OPEN:
            if self._should_attempt_reset(stats):
                await self._set_half_open(stats)
            else:
                # Circuit is open, fail fast
                logger.warning(
                    "Circuit breaker is open, failing fast",
                    circuit_name=self.name,
                    failure_count=stats.failure_count,
                    last_failure=stats.last_failure_time
                )
                raise ExternalAPIUnavailableError(
                    api_name=self.name,
                    details={
                        "circuit_state": "open",
                        "failure_count": stats.failure_count,
                        "recovery_time": stats.last_failure_time + self.config.recovery_timeout if stats.last_failure_time else None
                    }
                )
        
        # Execute the function
        start_time = time.time()
        try:
            # Apply timeout
            if asyncio.iscoroutinefunction(func):
                result = await asyncio.wait_for(
                    func(*args, **kwargs),
                    timeout=self.config.timeout
                )
            else:
                result = func(*args, **kwargs)
            
            # Record success
            await self._record_success(stats)
            
            response_time = time.time() - start_time
            log_api_call(
                api_name=self.name,
                endpoint="circuit_breaker_call",
                response_time=response_time,
                status_code=200,
                success=True
            )
            
            return result
            
        except asyncio.TimeoutError:
            response_time = time.time() - start_time
            logger.error(
                "Circuit breaker timeout",
                circuit_name=self.name,
                timeout=self.config.timeout,
                response_time=response_time
            )
            
            await self._record_failure(stats)
            raise ExternalAPIError(
                api_name=self.name,
                message=f"Request timeout after {self.config.timeout}s"
            )
            
        except self.config.expected_exception as e:
            response_time = time.time() - start_time
            logger.error(
                "Circuit breaker expected exception",
                circuit_name=self.name,
                error=str(e),
                response_time=response_time
            )
            
            await self._record_failure(stats)
            raise
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                "Circuit breaker unexpected exception",
                circuit_name=self.name,
                error=str(e),
                error_type=type(e).__name__,
                response_time=response_time
            )
            
            await self._record_failure(stats)
            raise
    
    async def get_stats(self) -> CircuitBreakerStats:
        """Get current circuit breaker statistics."""
        return await self._get_stats()
    
    async def reset(self) -> None:
        """Manually reset circuit breaker to closed state."""
        stats = CircuitBreakerStats(state=CircuitState.CLOSED)
        await self._save_stats(stats)
        
        logger.info("Circuit breaker manually reset", circuit_name=self.name)
    
    async def force_open(self) -> None:
        """Manually force circuit breaker to open state."""
        stats = await self._get_stats()
        stats.state = CircuitState.OPEN
        stats.last_failure_time = time.time()
        await self._save_stats(stats)
        
        logger.warning("Circuit breaker manually opened", circuit_name=self.name)
    
    def _should_attempt_reset(self, stats: CircuitBreakerStats) -> bool:
        """Check if circuit should attempt to reset."""
        if not stats.last_failure_time:
            return True
        
        return (time.time() - stats.last_failure_time) >= self.config.recovery_timeout
    
    async def _open_circuit(self, stats: CircuitBreakerStats) -> None:
        """Open the circuit breaker."""
        stats.state = CircuitState.OPEN
        stats.last_failure_time = time.time()
        await self._save_stats(stats)
        
        logger.warning(
            "Circuit breaker opened",
            circuit_name=self.name,
            failure_count=stats.failure_count,
            threshold=self.config.failure_threshold
        )
    
    async def _set_half_open(self, stats: CircuitBreakerStats) -> None:
        """Set circuit breaker to half-open state."""
        stats.state = CircuitState.HALF_OPEN
        stats.success_count = 0  # Reset success count for half-open state
        await self._save_stats(stats)
        
        logger.info(
            "Circuit breaker set to half-open",
            circuit_name=self.name
        )
    
    async def _record_success(self, stats: CircuitBreakerStats) -> None:
        """Record successful call."""
        stats.total_requests += 1
        stats.total_successes += 1
        stats.last_success_time = time.time()
        
        if stats.state == CircuitState.HALF_OPEN:
            stats.success_count += 1
            if stats.success_count >= self.config.success_threshold:
                # Close the circuit
                stats.state = CircuitState.CLOSED
                stats.failure_count = 0
                stats.success_count = 0
                
                logger.info(
                    "Circuit breaker closed after recovery",
                    circuit_name=self.name,
                    success_count=stats.success_count
                )
        
        elif stats.state == CircuitState.CLOSED:
            # Reset failure count on success
            stats.failure_count = 0
        
        await self._save_stats(stats)
    
    async def _record_failure(self, stats: CircuitBreakerStats) -> None:
        """Record failed call."""
        stats.total_requests += 1
        stats.total_failures += 1
        stats.last_failure_time = time.time()
        
        if stats.state == CircuitState.HALF_OPEN:
            # Go back to open state
            stats.state = CircuitState.OPEN
            stats.success_count = 0
            
            logger.warning(
                "Circuit breaker reopened from half-open",
                circuit_name=self.name
            )
        
        elif stats.state == CircuitState.CLOSED:
            stats.failure_count += 1
        
        await self._save_stats(stats)
    
    async def _get_stats(self) -> CircuitBreakerStats:
        """Get circuit breaker statistics from cache."""
        cache_key = f"circuit_breaker:{self.name}"
        
        try:
            stats_data = await self.cache.get(cache_key)
            if stats_data:
                return CircuitBreakerStats(
                    state=CircuitState(stats_data.get("state", "closed")),
                    failure_count=stats_data.get("failure_count", 0),
                    success_count=stats_data.get("success_count", 0),
                    last_failure_time=stats_data.get("last_failure_time"),
                    last_success_time=stats_data.get("last_success_time"),
                    total_requests=stats_data.get("total_requests", 0),
                    total_failures=stats_data.get("total_failures", 0),
                    total_successes=stats_data.get("total_successes", 0)
                )
        except Exception as e:
            logger.error(
                "Failed to get circuit breaker stats",
                circuit_name=self.name,
                error=str(e)
            )
        
        # Return default stats
        return CircuitBreakerStats()
    
    async def _save_stats(self, stats: CircuitBreakerStats) -> None:
        """Save circuit breaker statistics to cache."""
        cache_key = f"circuit_breaker:{self.name}"
        
        stats_data = {
            "state": stats.state.value,
            "failure_count": stats.failure_count,
            "success_count": stats.success_count,
            "last_failure_time": stats.last_failure_time,
            "last_success_time": stats.last_success_time,
            "total_requests": stats.total_requests,
            "total_failures": stats.total_failures,
            "total_successes": stats.total_successes
        }
        
        # Cache for 24 hours
        await self.cache.set(cache_key, stats_data, ttl=86400)


class PlantCareCircuitBreakerManager:
    """
    Manager for Plant Care Application circuit breakers.
    """
    
    def __init__(self):
        self._circuit_breakers: Dict[str, PlantCareCircuitBreaker] = {}
    
    def get_circuit_breaker(
        self,
        name: str,
        config: Optional[CircuitBreakerConfig] = None
    ) -> PlantCareCircuitBreaker:
        """
        Get or create a circuit breaker for a service.
        
        Args:
            name: Service name
            config: Optional custom configuration
            
        Returns:
            PlantCareCircuitBreaker: Circuit breaker instance
        """
        if name not in self._circuit_breakers:
            self._circuit_breakers[name] = PlantCareCircuitBreaker(name, config)
        
        return self._circuit_breakers[name]
    
    async def get_all_stats(self) -> Dict[str, CircuitBreakerStats]:
        """Get statistics for all circuit breakers."""
        stats = {}
        
        for name, breaker in self._circuit_breakers.items():
            try:
                stats[name] = await breaker.get_stats()
            except Exception as e:
                logger.error(
                    "Failed to get stats for circuit breaker",
                    circuit_name=name,
                    error=str(e)
                )
        
        return stats
    
    async def reset_all(self) -> None:
        """Reset all circuit breakers."""
        for name, breaker in self._circuit_breakers.items():
            try:
                await breaker.reset()
            except Exception as e:
                logger.error(
                    "Failed to reset circuit breaker",
                    circuit_name=name,
                    error=str(e)
                )


# Decorator for circuit breaker
def circuit_breaker(
    name: str,
    config: Optional[CircuitBreakerConfig] = None
):
    """
    Decorator to add circuit breaker protection to functions.
    
    Args:
        name: Circuit breaker name
        config: Optional configuration
    """
    def decorator(func):
        breaker = _circuit_breaker_manager.get_circuit_breaker(name, config)
        
        @functools.wraps(func)
        async def async_wrapper(*args, **kwargs):
            return await breaker.call(func, *args, **kwargs)
        
        @functools.wraps(func)
        def sync_wrapper(*args, **kwargs):
            return asyncio.run(breaker.call(func, *args, **kwargs))
        
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return sync_wrapper
    
    return decorator


# Global circuit breaker manager
_circuit_breaker_manager = PlantCareCircuitBreakerManager()


def get_circuit_breaker_manager() -> PlantCareCircuitBreakerManager:
    """
    Get the global circuit breaker manager.
    
    Returns:
        PlantCareCircuitBreakerManager: Circuit breaker manager
    """
    return _circuit_breaker_manager


# Plant Care specific circuit breakers
def get_plant_identification_circuit_breaker() -> PlantCareCircuitBreaker:
    """Get circuit breaker for plant identification APIs."""
    return _circuit_breaker_manager.get_circuit_breaker("plant_identification")


def get_weather_api_circuit_breaker() -> PlantCareCircuitBreaker:
    """Get circuit breaker for weather APIs."""
    return _circuit_breaker_manager.get_circuit_breaker("weather_api")


def get_ai_services_circuit_breaker() -> PlantCareCircuitBreaker:
    """Get circuit breaker for AI services."""
    return _circuit_breaker_manager.get_circuit_breaker("ai_services")


def get_notification_services_circuit_breaker() -> PlantCareCircuitBreaker:
    """Get circuit breaker for notification services."""
    return _circuit_breaker_manager.get_circuit_breaker("notification_services")


def get_payment_gateway_circuit_breaker() -> PlantCareCircuitBreaker:
    """Get circuit breaker for payment gateways."""
    return _circuit_breaker_manager.get_circuit_breaker("payment_gateway")


# Export circuit breaker utilities
__all__ = [
    "PlantCareCircuitBreaker",
    "PlantCareCircuitBreakerManager",
    "CircuitState",
    "CircuitBreakerConfig",
    "CircuitBreakerStats",
    "circuit_breaker",
    "get_circuit_breaker_manager",
    "get_plant_identification_circuit_breaker",
    "get_weather_api_circuit_breaker",
    "get_ai_services_circuit_breaker",
    "get_notification_services_circuit_breaker",
    "get_payment_gateway_circuit_breaker",
]