# app/shared/config/redis.py
"""
Plant Care Application - Redis Configuration

Redis configuration and connection management for Plant Care Application.
Provides caching, session storage, rate limiting, and pub/sub functionality
specifically designed for Plant Care features.

This configuration works alongside the Redis client manager for complete Redis access.
"""

import asyncio
import json
import time
from typing import Dict, Any, Optional, List, Union
from functools import lru_cache
from urllib.parse import urlparse

import redis.asyncio as redis
from redis.asyncio import ConnectionPool, Redis
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    CacheError,
    CacheConnectionError,
    ConfigurationError
)

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class RedisConfig:
    """
    Redis configuration for Plant Care Application.
    Manages Redis connection settings and Plant Care specific configurations.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self._validate_config()
    
    def _validate_config(self) -> None:
        """Validate Redis configuration."""
        if not self.settings.REDIS_URL:
            raise ConfigurationError("REDIS_URL is required")
        
        # Parse Redis URL to validate format
        try:
            parsed = urlparse(self.settings.REDIS_URL)
            if not parsed.scheme.startswith('redis'):
                raise ValueError("Invalid Redis URL scheme")
        except Exception as e:
            raise ConfigurationError(f"Invalid REDIS_URL: {str(e)}")
    
    @property
    def connection_kwargs(self) -> Dict[str, Any]:
        """
        Get Redis connection parameters for Plant Care Application.
        
        Returns:
            Dict[str, Any]: Connection parameters for redis-py
        """
        return {
            "url": self.settings.REDIS_URL,
            "password": self.settings.REDIS_PASSWORD,
            "db": self.settings.REDIS_DB,
            "socket_timeout": self.settings.REDIS_SOCKET_TIMEOUT,
            "socket_connect_timeout": 5,
            "socket_keepalive": True,
            "socket_keepalive_options": {},
            "retry_on_timeout": True,
            "encoding": "utf-8",
            "decode_responses": True,
            "health_check_interval": 30,
        }
    
    @property
    def pool_kwargs(self) -> Dict[str, Any]:
        """
        Get connection pool parameters for Plant Care Application.
        
        Returns:
            Dict[str, Any]: Pool configuration optimized for Plant Care
        """
        return {
            "max_connections": self.settings.REDIS_MAX_CONNECTIONS,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }
    
    @property
    def plant_care_settings(self) -> Dict[str, Any]:
        """
        Get Plant Care specific Redis settings.
        
        Returns:
            Dict[str, Any]: Plant Care application settings
        """
        return {
            # Cache TTL settings
            "user_data_ttl": self.settings.CACHE_TTL_USER_DATA,
            "plant_library_ttl": self.settings.CACHE_TTL_PLANT_LIBRARY,
            "weather_data_ttl": self.settings.CACHE_TTL_WEATHER_DATA,
            "api_response_ttl": self.settings.CACHE_TTL_API_RESPONSE,
            "care_schedule_ttl": self.settings.CACHE_TTL_CARE_SCHEDULE,
            
            # Rate limiting settings
            "rate_limit_requests": self.settings.RATE_LIMIT_REQUESTS,
            "rate_limit_period": self.settings.RATE_LIMIT_PERIOD,
            "premium_multiplier": self.settings.PREMIUM_RATE_LIMIT_MULTIPLIER,
            
            # Plant Care specific prefixes
            "key_prefixes": {
                "user": "plant_care:user:",
                "plant": "plant_care:plant:",
                "care_schedule": "plant_care:schedule:",
                "weather": "plant_care:weather:",
                "api_usage": "plant_care:api:",
                "library": "plant_care:library:",
                "session": "plant_care:session:",
                "rate_limit": "plant_care:rate:",
                "notification": "plant_care:notification:",
            }
        }


class RedisManager:
    """
    Redis manager for Plant Care Application.
    Provides connection management, health monitoring, and Plant Care specific operations.
    """
    
    def __init__(self):
        self.config = RedisConfig()
        self._client: Optional[Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._initialized = False
        self._health_check_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool and client."""
        if self._initialized:
            return
        
        try:
            logger.info("Initializing Redis manager for Plant Care Application")
            
            # Create connection pool
            self._connection_pool = ConnectionPool.from_url(
                **self.config.connection_kwargs,
                **self.config.pool_kwargs
            )
            
            # Create Redis client
            self._client = Redis(connection_pool=self._connection_pool)
            
            # Verify connection
            await self._verify_connection()
            
            self._initialized = True
            logger.info("Redis manager initialized successfully",
                       max_connections=self.config.pool_kwargs["max_connections"])
            
        except Exception as e:
            logger.error("Failed to initialize Redis manager", error=str(e))
            raise CacheConnectionError(f"Redis initialization failed: {str(e)}")
    
    async def _verify_connection(self) -> None:
        """Verify Redis connection."""
        try:
            # Basic ping test
            pong = await self._client.ping()
            if not pong:
                raise ValueError("Redis ping failed")
            
            # Test Plant Care specific operations
            test_key = "plant_care:health_check"
            await self._client.set(test_key, "ok", ex=10)
            result = await self._client.get(test_key)
            await self._client.delete(test_key)
            
            if result != "ok":
                raise ValueError("Redis read/write test failed")
            
            logger.info("Redis connection verification successful")
            
        except Exception as e:
            logger.error("Redis connection verification failed", error=str(e))
            raise CacheConnectionError(f"Redis verification failed: {str(e)}")
    
    async def get_client(self) -> Redis:
        """
        Get Redis client.
        
        Returns:
            Redis: Redis client instance
            
        Raises:
            CacheConnectionError: If client is not initialized
        """
        if not self._initialized or not self._client:
            raise CacheConnectionError("Redis manager not initialized")
        
        return self._client
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None, 
                  namespace: str = None) -> bool:
        """
        Set value in Redis with Plant Care namespace.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            namespace: Plant Care namespace (user, plant, etc.)
            
        Returns:
            bool: True if successful
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            # Serialize value if needed
            if isinstance(value, (dict, list)):
                value = json.dumps(value)
            
            # Set with TTL
            if ttl:
                result = await client.set(key, value, ex=ttl)
            else:
                result = await client.set(key, value)
            
            return bool(result)
            
        except Exception as e:
            logger.error("Redis set operation failed", key=key, error=str(e))
            raise CacheError(f"Failed to set key {key}: {str(e)}")
    
    async def get(self, key: str, namespace: str = None) -> Optional[Any]:
        """
        Get value from Redis with Plant Care namespace.
        
        Args:
            key: Cache key
            namespace: Plant Care namespace (user, plant, etc.)
            
        Returns:
            Optional[Any]: Cached value or None
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Try to deserialize JSON
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
            
        except Exception as e:
            logger.error("Redis get operation failed", key=key, error=str(e))
            return None
    
    async def delete(self, key: str, namespace: str = None) -> bool:
        """
        Delete key from Redis with Plant Care namespace.
        
        Args:
            key: Cache key
            namespace: Plant Care namespace
            
        Returns:
            bool: True if key was deleted
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            result = await client.delete(key)
            return bool(result)
            
        except Exception as e:
            logger.error("Redis delete operation failed", key=key, error=str(e))
            return False
    
    async def exists(self, key: str, namespace: str = None) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
            namespace: Plant Care namespace
            
        Returns:
            bool: True if key exists
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            result = await client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error("Redis exists operation failed", key=key, error=str(e))
            return False
    
    async def incr(self, key: str, amount: int = 1, namespace: str = None) -> int:
        """
        Increment key value in Redis.
        
        Args:
            key: Cache key
            amount: Amount to increment
            namespace: Plant Care namespace
            
        Returns:
            int: New value after increment
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            if amount == 1:
                result = await client.incr(key)
            else:
                result = await client.incrby(key, amount)
            
            return result
            
        except Exception as e:
            logger.error("Redis incr operation failed", key=key, error=str(e))
            raise CacheError(f"Failed to increment key {key}: {str(e)}")
    
    async def expire(self, key: str, ttl: int, namespace: str = None) -> bool:
        """
        Set expiration time for key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            namespace: Plant Care namespace
            
        Returns:
            bool: True if expiration was set
        """
        try:
            client = await self.get_client()
            
            # Add Plant Care namespace if provided
            if namespace:
                prefixes = self.config.plant_care_settings["key_prefixes"]
                prefix = prefixes.get(namespace, f"plant_care:{namespace}:")
                key = f"{prefix}{key}"
            
            result = await client.expire(key, ttl)
            return bool(result)
            
        except Exception as e:
            logger.error("Redis expire operation failed", key=key, error=str(e))
            return False
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check for Plant Care Application.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        async with self._health_check_lock:
            start_time = time.time()
            
            try:
                if not self._client:
                    return {
                        "status": "unhealthy",
                        "error": "Redis client not initialized",
                        "response_time": 0
                    }
                
                # Test basic connectivity
                await self._client.ping()
                
                # Test Plant Care specific operations
                test_key = "plant_care:health_check"
                test_value = {"timestamp": time.time(), "test": True}
                
                # Test set operation
                await self._client.set(test_key, json.dumps(test_value), ex=10)
                
                # Test get operation
                result = await self._client.get(test_key)
                retrieved_value = json.loads(result) if result else None
                
                # Test delete operation
                await self._client.delete(test_key)
                
                # Get Redis info
                info = await self._client.info()
                
                response_time = time.time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "keyspace_hits": info.get("keyspace_hits"),
                    "keyspace_misses": info.get("keyspace_misses"),
                    "operations_test": "passed" if retrieved_value else "failed",
                    "cache_type": "redis"
                }
                
            except Exception as e:
                response_time = time.time() - start_time
                logger.error("Redis health check failed", error=str(e))
                
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "response_time": response_time,
                    "cache_type": "redis"
                }
    
    async def close(self) -> None:
        """Close Redis connection pool."""
        if self._client:
            logger.info("Closing Redis connection pool")
            await self._client.close()
            self._client = None
            self._initialized = False


# Global Redis manager instance
_redis_manager: Optional[RedisManager] = None


@lru_cache()
def get_redis_config() -> RedisConfig:
    """
    Get Redis configuration for Plant Care Application.
    
    Returns:
        RedisConfig: Redis configuration instance
    """
    return RedisConfig()


def get_redis_manager() -> RedisManager:
    """
    Get Redis manager singleton for Plant Care Application.
    
    Returns:
        RedisManager: Redis manager instance
    """
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


async def get_redis_client() -> Redis:
    """
    Get Redis client for Plant Care Application.
    
    Returns:
        Redis: Redis client instance
    """
    manager = get_redis_manager()
    return await manager.get_client()


# Plant Care Application specific Redis utilities
class PlantCareRedis:
    """Plant Care Application specific Redis utilities."""
    
    @staticmethod
    async def cache_user_session(user_id: str, session_data: Dict[str, Any], 
                                ttl: int = None) -> bool:
        """
        Cache user session data for Plant Care Application.
        
        Args:
            user_id: User ID
            session_data: Session data to cache
            ttl: Session TTL (default: 24 hours)
            
        Returns:
            bool: True if cached successfully
        """
        manager = get_redis_manager()
        ttl = ttl or 86400  # 24 hours default
        
        return await manager.set(
            key=user_id,
            value=session_data,
            ttl=ttl,
            namespace="session"
        )
    
    @staticmethod
    async def get_user_session(user_id: str) -> Optional[Dict[str, Any]]:
        """
        Get user session data from cache.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[Dict[str, Any]]: Session data or None
        """
        manager = get_redis_manager()
        return await manager.get(key=user_id, namespace="session")
    
    @staticmethod
    async def invalidate_user_session(user_id: str) -> bool:
        """
        Invalidate user session.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if invalidated
        """
        manager = get_redis_manager()
        return await manager.delete(key=user_id, namespace="session")
    
    @staticmethod
    async def track_api_usage(user_id: str, api_name: str, 
                             window_seconds: int = 3600) -> int:
        """
        Track API usage for rate limiting in Plant Care Application.
        
        Args:
            user_id: User ID
            api_name: API endpoint name
            window_seconds: Rate limit window (default: 1 hour)
            
        Returns:
            int: Current usage count
        """
        manager = get_redis_manager()
        
        # Create rate limit key
        window_start = int(time.time() // window_seconds) * window_seconds
        key = f"{user_id}:{api_name}:{window_start}"
        
        # Increment usage count
        count = await manager.incr(key=key, namespace="rate_limit")
        
        # Set expiration if this is the first increment
        if count == 1:
            await manager.expire(key=key, ttl=window_seconds, namespace="rate_limit")
        
        return count
    
    @staticmethod
    async def get_api_usage(user_id: str, api_name: str, 
                           window_seconds: int = 3600) -> int:
        """
        Get current API usage count.
        
        Args:
            user_id: User ID
            api_name: API endpoint name
            window_seconds: Rate limit window
            
        Returns:
            int: Current usage count
        """
        manager = get_redis_manager()
        
        # Create rate limit key
        window_start = int(time.time() // window_seconds) * window_seconds
        key = f"{user_id}:{api_name}:{window_start}"
        
        result = await manager.get(key=key, namespace="rate_limit")
        return int(result) if result else 0
    
    @staticmethod
    async def cache_plant_library_data(species: str, data: Dict[str, Any]) -> bool:
        """
        Cache plant library data for Plant Care Application.
        
        Args:
            species: Plant species
            data: Plant library data
            
        Returns:
            bool: True if cached successfully
        """
        manager = get_redis_manager()
        config = get_redis_config()
        ttl = config.plant_care_settings["plant_library_ttl"]
        
        return await manager.set(
            key=species.lower().replace(" ", "_"),
            value=data,
            ttl=ttl,
            namespace="library"
        )
    
    @staticmethod
    async def get_plant_library_data(species: str) -> Optional[Dict[str, Any]]:
        """
        Get cached plant library data.
        
        Args:
            species: Plant species
            
        Returns:
            Optional[Dict[str, Any]]: Plant library data or None
        """
        manager = get_redis_manager()
        return await manager.get(
            key=species.lower().replace(" ", "_"),
            namespace="library"
        )
    
    @staticmethod
    async def cache_weather_data(location: str, data: Dict[str, Any]) -> bool:
        """
        Cache weather data for Plant Care Application.
        
        Args:
            location: Location identifier
            data: Weather data
            
        Returns:
            bool: True if cached successfully
        """
        manager = get_redis_manager()
        config = get_redis_config()
        ttl = config.plant_care_settings["weather_data_ttl"]
        
        return await manager.set(
            key=location.lower().replace(" ", "_"),
            value=data,
            ttl=ttl,
            namespace="weather"
        )
    
    @staticmethod
    async def get_weather_data(location: str) -> Optional[Dict[str, Any]]:
        """
        Get cached weather data.
        
        Args:
            location: Location identifier
            
        Returns:
            Optional[Dict[str, Any]]: Weather data or None
        """
        manager = get_redis_manager()
        return await manager.get(
            key=location.lower().replace(" ", "_"),
            namespace="weather"
        )
    
    @staticmethod
    async def queue_notification(user_id: str, notification: Dict[str, Any]) -> bool:
        """
        Queue notification for Plant Care Application.
        
        Args:
            user_id: User ID
            notification: Notification data
            
        Returns:
            bool: True if queued successfully
        """
        try:
            manager = get_redis_manager()
            client = await manager.get_client()
            
            # Add to user's notification queue
            queue_key = f"plant_care:notification:queue:{user_id}"
            notification_data = json.dumps(notification)
            
            # Add with timestamp
            score = time.time()
            await client.zadd(queue_key, {notification_data: score})
            
            # Set expiration for queue
            await client.expire(queue_key, 604800)  # 7 days
            
            return True
            
        except Exception as e:
            logger.error("Failed to queue notification", 
                        user_id=user_id, error=str(e))
            return False
    
    @staticmethod
    async def get_pending_notifications(user_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Get pending notifications for user.
        
        Args:
            user_id: User ID
            limit: Maximum notifications to return
            
        Returns:
            List[Dict[str, Any]]: List of notifications
        """
        try:
            manager = get_redis_manager()
            client = await manager.get_client()
            
            queue_key = f"plant_care:notification:queue:{user_id}"
            
            # Get notifications ordered by timestamp
            notifications = await client.zrange(queue_key, 0, limit-1, withscores=True)
            
            result = []
            for notification_data, timestamp in notifications:
                try:
                    notification = json.loads(notification_data)
                    notification["timestamp"] = timestamp
                    result.append(notification)
                except json.JSONDecodeError:
                    continue
            
            return result
            
        except Exception as e:
            logger.error("Failed to get pending notifications", 
                        user_id=user_id, error=str(e))
            return []