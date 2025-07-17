"""
app/shared/infrastructure/external_apis/api_rotation.py
Plant Care Application - API Rotation Logic

Manages API rotation, fallback strategies, and usage tracking for external APIs.
Ensures high availability by automatically switching between API providers.
"""
import time
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, field
from enum import Enum
import asyncio

import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import PlantCareCache
from app.shared.infrastructure.external_apis.api_client import APIProvider, APIResponse
from app.shared.core.exceptions import ExternalAPIError, ExternalAPIRateLimitError
from app.shared.utils.logging import log_api_call

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class APITier(Enum):
    """API usage tiers for Plant Care Application."""
    FREE = "free"
    PREMIUM = "premium"


@dataclass
class APILimits:
    """API usage limits configuration."""
    free_daily_limit: int
    premium_daily_limit: int
    free_monthly_limit: int
    premium_monthly_limit: int
    reset_period: str = "daily"  # daily, monthly
    priority: int = 1  # Lower number = higher priority


@dataclass
class APIUsageStats:
    """API usage statistics."""
    provider: APIProvider
    daily_usage: int = 0
    monthly_usage: int = 0
    success_rate: float = 1.0
    avg_response_time: float = 0.0
    last_error: Optional[str] = None
    last_success: Optional[float] = None
    consecutive_failures: int = 0
    is_healthy: bool = True


class PlantCareAPIRotationManager:
    """
    API rotation manager for Plant Care Application.
    Handles intelligent API selection, fallback, and usage tracking.
    """
    
    def __init__(self):
        self.cache = PlantCareCache()
        
        # API limits configuration for Plant Care services
        self.api_limits = {
            # Plant Identification APIs
            APIProvider.PLANTNET: APILimits(
                free_daily_limit=5,
                premium_daily_limit=50,
                free_monthly_limit=150,
                premium_monthly_limit=1500,
                priority=1
            ),
            APIProvider.TREFLE: APILimits(
                free_daily_limit=10,
                premium_daily_limit=100,
                free_monthly_limit=300,
                premium_monthly_limit=3000,
                priority=2
            ),
            APIProvider.PLANT_ID: APILimits(
                free_daily_limit=3,
                premium_daily_limit=30,
                free_monthly_limit=90,
                premium_monthly_limit=900,
                priority=3
            ),
            APIProvider.KINDWISE: APILimits(
                free_daily_limit=5,
                premium_daily_limit=50,
                free_monthly_limit=150,
                premium_monthly_limit=1500,
                priority=4
            ),
            
            # Weather APIs
            APIProvider.OPENWEATHER: APILimits(
                free_daily_limit=1000,
                premium_daily_limit=10000,
                free_monthly_limit=30000,
                premium_monthly_limit=300000,
                priority=1
            ),
            APIProvider.TOMORROW_IO: APILimits(
                free_daily_limit=100,
                premium_daily_limit=1000,
                free_monthly_limit=3000,
                premium_monthly_limit=30000,
                priority=2
            ),
            APIProvider.WEATHERSTACK: APILimits(
                free_daily_limit=250,
                premium_daily_limit=2500,
                free_monthly_limit=7500,
                premium_monthly_limit=75000,
                reset_period="monthly",
                priority=3
            ),
            APIProvider.VISUAL_CROSSING: APILimits(
                free_daily_limit=1000,
                premium_daily_limit=10000,
                free_monthly_limit=30000,
                premium_monthly_limit=300000,
                priority=4
            ),
            
            # AI Services
            APIProvider.OPENAI: APILimits(
                free_daily_limit=20,
                premium_daily_limit=200,
                free_monthly_limit=600,
                premium_monthly_limit=6000,
                priority=1
            ),
            APIProvider.GOOGLE_AI: APILimits(
                free_daily_limit=15,
                premium_daily_limit=150,
                free_monthly_limit=450,
                premium_monthly_limit=4500,
                priority=2
            ),
            APIProvider.ANTHROPIC: APILimits(
                free_daily_limit=10,
                premium_daily_limit=100,
                free_monthly_limit=300,
                premium_monthly_limit=3000,
                priority=3
            ),
        }
        
        # Service groups for rotation
        self.service_groups = {
            "plant_identification": [
                APIProvider.PLANTNET,
                APIProvider.TREFLE,
                APIProvider.PLANT_ID,
                APIProvider.KINDWISE
            ],
            "weather": [
                APIProvider.OPENWEATHER,
                APIProvider.TOMORROW_IO,
                APIProvider.WEATHERSTACK,
                APIProvider.VISUAL_CROSSING
            ],
            "ai_chat": [
                APIProvider.OPENAI,
                APIProvider.GOOGLE_AI,
                APIProvider.ANTHROPIC
            ]
        }
    
    async def get_best_provider(
        self,
        service_type: str,
        user_id: str,
        user_tier: APITier = APITier.FREE,
        exclude_providers: Optional[List[APIProvider]] = None
    ) -> Optional[APIProvider]:
        """
        Get the best available API provider for a service.
        
        Args:
            service_type: Service type (plant_identification, weather, ai_chat)
            user_id: User ID for usage tracking
            user_tier: User's subscription tier
            exclude_providers: Providers to exclude from selection
            
        Returns:
            Optional[APIProvider]: Best available provider or None
        """
        providers = self.service_groups.get(service_type, [])
        if not providers:
            return None
        
        exclude_providers = exclude_providers or []
        available_providers = [p for p in providers if p not in exclude_providers]
        
        if not available_providers:
            return None
        
        # Get usage statistics for all providers
        provider_stats = []
        for provider in available_providers:
            stats = await self._get_provider_stats(provider, user_id)
            
            # Check if provider is within limits
            if await self._is_within_limits(provider, user_id, user_tier):
                provider_stats.append((provider, stats))
        
        if not provider_stats:
            logger.warning(
                "No providers within limits",
                service_type=service_type,
                user_id=user_id,
                user_tier=user_tier.value
            )
            return None
        
        # Sort providers by priority and health
        provider_stats.sort(key=lambda x: (
            self.api_limits[x[0]].priority,  # Priority (lower is better)
            not x[1].is_healthy,  # Healthy providers first
            x[1].consecutive_failures,  # Fewer failures first
            -x[1].success_rate,  # Higher success rate first
            x[1].avg_response_time  # Faster response time first
        ))
        
        best_provider = provider_stats[0][0]
        
        logger.debug(
            "Selected API provider",
            service_type=service_type,
            provider=best_provider.value,
            user_id=user_id,
            user_tier=user_tier.value
        )
        
        return best_provider
    
    async def get_fallback_providers(
        self,
        service_type: str,
        user_id: str,
        user_tier: APITier = APITier.FREE,
        primary_provider: Optional[APIProvider] = None
    ) -> List[APIProvider]:
        """
        Get fallback providers for a service in priority order.
        
        Args:
            service_type: Service type
            user_id: User ID
            user_tier: User's subscription tier
            primary_provider: Primary provider to exclude
            
        Returns:
            List[APIProvider]: Fallback providers in priority order
        """
        exclude = [primary_provider] if primary_provider else []
        providers = []
        
        for _ in range(3):  # Get up to 3 fallback providers
            provider = await self.get_best_provider(
                service_type=service_type,
                user_id=user_id,
                user_tier=user_tier,
                exclude_providers=exclude
            )
            
            if provider:
                providers.append(provider)
                exclude.append(provider)
            else:
                break
        
        return providers
    
    async def record_api_usage(
        self,
        provider: APIProvider,
        user_id: str,
        response: APIResponse,
        error: Optional[Exception] = None
    ) -> None:
        """
        Record API usage statistics.
        
        Args:
            provider: API provider
            user_id: User ID
            response: API response
            error: Exception if call failed
        """
        try:
            # Update usage counters
            await self.cache.track_api_usage(user_id, provider.value, 1)
            
            # Update provider statistics
            stats = await self._get_provider_stats(provider, user_id)
            
            if response.success:
                stats.consecutive_failures = 0
                stats.last_success = time.time()
                stats.is_healthy = True
                
                # Update success rate (exponential moving average)
                stats.success_rate = 0.9 * stats.success_rate + 0.1 * 1.0
                
                # Update response time (exponential moving average)
                stats.avg_response_time = 0.9 * stats.avg_response_time + 0.1 * response.response_time
                
            else:
                stats.consecutive_failures += 1
                stats.last_error = str(error) if error else "Unknown error"
                
                # Mark as unhealthy after 3 consecutive failures
                if stats.consecutive_failures >= 3:
                    stats.is_healthy = False
                
                # Update success rate
                stats.success_rate = 0.9 * stats.success_rate + 0.1 * 0.0
            
            # Store updated statistics
            await self._save_provider_stats(provider, user_id, stats)
            
            # Log usage for monitoring
            log_api_call(
                api_name=provider.value,
                endpoint="api_usage",
                response_time=response.response_time,
                status_code=response.status_code,
                user_id=user_id,
                success=response.success
            )
            
        except Exception as e:
            logger.error(
                "Failed to record API usage",
                provider=provider.value,
                user_id=user_id,
                error=str(e)
            )
    
    async def check_api_health(self, provider: APIProvider) -> bool:
        """
        Check if an API provider is healthy.
        
        Args:
            provider: API provider to check
            
        Returns:
            bool: True if healthy
        """
        try:
            # Get recent stats for this provider
            cache_key = f"api_health:{provider.value}"
            health_data = await self.cache.get(cache_key)
            
            if not health_data:
                return True  # Assume healthy if no data
            
            # Check health criteria
            success_rate = health_data.get("success_rate", 1.0)
            consecutive_failures = health_data.get("consecutive_failures", 0)
            last_success = health_data.get("last_success", time.time())
            
            # Unhealthy if:
            # - Success rate below 50%
            # - More than 5 consecutive failures
            # - No success in last hour
            is_healthy = (
                success_rate >= 0.5 and
                consecutive_failures < 5 and
                (time.time() - last_success) < 3600
            )
            
            return is_healthy
            
        except Exception as e:
            logger.error(
                "Failed to check API health",
                provider=provider.value,
                error=str(e)
            )
            return True  # Default to healthy on error
    
    async def get_usage_report(
        self,
        user_id: str,
        service_type: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Get API usage report for a user.
        
        Args:
            user_id: User ID
            service_type: Optional service type filter
            
        Returns:
            Dict: Usage report
        """
        report = {
            "user_id": user_id,
            "timestamp": time.time(),
            "providers": {}
        }
        
        providers = []
        if service_type and service_type in self.service_groups:
            providers = self.service_groups[service_type]
        else:
            # All providers
            for group in self.service_groups.values():
                providers.extend(group)
        
        for provider in providers:
            try:
                daily_usage = await self.cache.get_api_usage(user_id, provider.value)
                stats = await self._get_provider_stats(provider, user_id)
                limits = self.api_limits.get(provider)
                
                report["providers"][provider.value] = {
                    "daily_usage": daily_usage,
                    "daily_limit_free": limits.free_daily_limit if limits else 0,
                    "daily_limit_premium": limits.premium_daily_limit if limits else 0,
                    "success_rate": stats.success_rate,
                    "avg_response_time": stats.avg_response_time,
                    "is_healthy": stats.is_healthy,
                    "consecutive_failures": stats.consecutive_failures,
                    "last_success": stats.last_success
                }
                
            except Exception as e:
                logger.error(
                    "Failed to get usage stats",
                    provider=provider.value,
                    user_id=user_id,
                    error=str(e)
                )
        
        return report
    
    async def reset_daily_usage(self) -> None:
        """Reset daily usage counters for all users and providers."""
        try:
            # This would typically be called by a background job
            # Reset usage counters in Redis
            await self.cache.delete_pattern("api_usage:*")
            
            logger.info("Daily API usage counters reset")
            
        except Exception as e:
            logger.error("Failed to reset daily usage", error=str(e))
    
    async def _get_provider_stats(
        self,
        provider: APIProvider,
        user_id: str
    ) -> APIUsageStats:
        """Get or create provider statistics."""
        cache_key = f"api_stats:{provider.value}:{user_id}"
        
        try:
            stats_data = await self.cache.get(cache_key)
            if stats_data:
                return APIUsageStats(
                    provider=provider,
                    daily_usage=stats_data.get("daily_usage", 0),
                    monthly_usage=stats_data.get("monthly_usage", 0),
                    success_rate=stats_data.get("success_rate", 1.0),
                    avg_response_time=stats_data.get("avg_response_time", 0.0),
                    last_error=stats_data.get("last_error"),
                    last_success=stats_data.get("last_success"),
                    consecutive_failures=stats_data.get("consecutive_failures", 0),
                    is_healthy=stats_data.get("is_healthy", True)
                )
        except Exception:
            pass
        
        # Return default stats
        return APIUsageStats(provider=provider)
    
    async def _save_provider_stats(
        self,
        provider: APIProvider,
        user_id: str,
        stats: APIUsageStats
    ) -> None:
        """Save provider statistics to cache."""
        cache_key = f"api_stats:{provider.value}:{user_id}"
        
        stats_data = {
            "daily_usage": stats.daily_usage,
            "monthly_usage": stats.monthly_usage,
            "success_rate": stats.success_rate,
            "avg_response_time": stats.avg_response_time,
            "last_error": stats.last_error,
            "last_success": stats.last_success,
            "consecutive_failures": stats.consecutive_failures,
            "is_healthy": stats.is_healthy
        }
        
        # Cache for 24 hours
        await self.cache.set(cache_key, stats_data, ttl=86400)
    
    async def _is_within_limits(
        self,
        provider: APIProvider,
        user_id: str,
        user_tier: APITier
    ) -> bool:
        """Check if provider is within usage limits."""
        limits = self.api_limits.get(provider)
        if not limits:
            return True
        
        current_usage = await self.cache.get_api_usage(user_id, provider.value)
        
        if user_tier == APITier.PREMIUM:
            daily_limit = limits.premium_daily_limit
        else:
            daily_limit = limits.free_daily_limit
        
        return current_usage < daily_limit


# Global API rotation manager instance
_rotation_manager: Optional[PlantCareAPIRotationManager] = None


def get_rotation_manager() -> PlantCareAPIRotationManager:
    """
    Get the global API rotation manager instance.
    
    Returns:
        PlantCareAPIRotationManager: Rotation manager instance
    """
    global _rotation_manager
    if _rotation_manager is None:
        _rotation_manager = PlantCareAPIRotationManager()
    return _rotation_manager


# Export rotation manager utilities
__all__ = [
    "PlantCareAPIRotationManager",
    "APITier",
    "APILimits",
    "APIUsageStats",
    "get_rotation_manager",
]