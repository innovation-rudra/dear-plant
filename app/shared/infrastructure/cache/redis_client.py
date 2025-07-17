"""
Plant Care Application - Redis Cache Manager
"""
import json
import pickle
from typing import Any, Dict, List, Optional, Union
import asyncio
from functools import wraps

import redis.asyncio as redis
from redis.asyncio import ConnectionPool
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import CacheError, CacheConnectionError

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class RedisManager:
    """
    Redis cache manager for Plant Care Application.
    Handles caching, session storage, and pub/sub operations.
    """
    
    def __init__(self):
        self._client: Optional[redis.Redis] = None
        self._connection_pool: Optional[ConnectionPool] = None
        self._initialized = False
        self._health_check_lock = asyncio.Lock()
    
    async def initialize(self) -> None:
        """Initialize Redis connection pool and client."""
        if self._initialized:
            return
        
        try:
            # Parse Redis URL
            redis_url = settings.REDIS_URL
            
            # Create connection pool
            self._connection_pool = ConnectionPool.from_url(
                redis_url,
                max_connections=settings.REDIS_MAX_CONNECTIONS,
                socket_timeout=settings.REDIS_SOCKET_TIMEOUT,
                socket_connect_timeout=5,
                retry_on_timeout=True,
                health_check_interval=30,
                encoding="utf-8",
                decode_responses=True,
            )
            
            # Create Redis client
            self._client = redis.Redis(
                connection_pool=self._connection_pool,
                socket_keepalive=True,
                socket_keepalive_options={},
            )
            
            # Test connection
            await self._test_connection()
            
            self._initialized = True
            logger.info("Redis manager initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Redis manager", error=str(e))
            raise CacheConnectionError(f"Failed to initialize Redis: {str(e)}")
    
    async def _test_connection(self) -> None:
        """Test Redis connection."""
        try:
            await self._client.ping()
            logger.info("Redis connection test passed")
        except Exception as e:
            logger.error("Redis connection test failed", error=str(e))
            raise CacheConnectionError(f"Redis connection test failed: {str(e)}")
    
    async def get_client(self) -> redis.Redis:
        """
        Get Redis client.
        
        Returns:
            redis.Redis: Redis client instance
        """
        if not self._initialized:
            await self.initialize()
        return self._client
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None,
        serialize: bool = True
    ) -> bool:
        """
        Set value in Redis.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Time to live in seconds
            serialize: Whether to serialize the value
            
        Returns:
            bool: True if successful
        """
        try:
            client = await self.get_client()
            
            # Serialize value if needed
            if serialize:
                if isinstance(value, (dict, list)):
                    value = json.dumps(value)
                elif not isinstance(value, (str, bytes, int, float)):
                    value = pickle.dumps(value)
            
            # Set value with TTL
            if ttl:
                result = await client.setex(key, ttl, value)
            else:
                result = await client.set(key, value)
            
            logger.debug("Value set in Redis", key=key, ttl=ttl)
            return result
            
        except Exception as e:
            logger.error("Failed to set value in Redis", key=key, error=str(e))
            raise CacheError(f"Failed to set cache value: {str(e)}")
    
    async def get(self, key: str, deserialize: bool = True) -> Optional[Any]:
        """
        Get value from Redis.
        
        Args:
            key: Cache key
            deserialize: Whether to deserialize the value
            
        Returns:
            Optional[Any]: Cached value or None
        """
        try:
            client = await self.get_client()
            value = await client.get(key)
            
            if value is None:
                return None
            
            # Deserialize value if needed
            if deserialize and isinstance(value, str):
                try:
                    # Try JSON first
                    return json.loads(value)
                except (json.JSONDecodeError, TypeError):
                    try:
                        # Try pickle
                        return pickle.loads(value.encode())
                    except (pickle.PickleError, AttributeError):
                        # Return as string
                        return value
            
            logger.debug("Value retrieved from Redis", key=key)
            return value
            
        except Exception as e:
            logger.error("Failed to get value from Redis", key=key, error=str(e))
            return None
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from Redis.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key was deleted
        """
        try:
            client = await self.get_client()
            result = await client.delete(key)
            
            logger.debug("Key deleted from Redis", key=key)
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to delete key from Redis", key=key, error=str(e))
            return False
    
    async def exists(self, key: str) -> bool:
        """
        Check if key exists in Redis.
        
        Args:
            key: Cache key
            
        Returns:
            bool: True if key exists
        """
        try:
            client = await self.get_client()
            result = await client.exists(key)
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to check key existence in Redis", key=key, error=str(e))
            return False
    
    async def expire(self, key: str, ttl: int) -> bool:
        """
        Set TTL for existing key.
        
        Args:
            key: Cache key
            ttl: Time to live in seconds
            
        Returns:
            bool: True if TTL was set
        """
        try:
            client = await self.get_client()
            result = await client.expire(key, ttl)
            
            logger.debug("TTL set for Redis key", key=key, ttl=ttl)
            return bool(result)
            
        except Exception as e:
            logger.error("Failed to set TTL for Redis key", key=key, error=str(e))
            return False
    
    async def increment(self, key: str, amount: int = 1) -> int:
        """
        Increment value in Redis.
        
        Args:
            key: Cache key
            amount: Amount to increment
            
        Returns:
            int: New value after increment
        """
        try:
            client = await self.get_client()
            result = await client.incrby(key, amount)
            
            logger.debug("Value incremented in Redis", key=key, amount=amount, new_value=result)
            return result
            
        except Exception as e:
            logger.error("Failed to increment value in Redis", key=key, error=str(e))
            raise CacheError(f"Failed to increment cache value: {str(e)}")
    
    async def get_many(self, keys: List[str]) -> Dict[str, Any]:
        """
        Get multiple values from Redis.
        
        Args:
            keys: List of cache keys
            
        Returns:
            Dict[str, Any]: Dictionary of key-value pairs
        """
        try:
            client = await self.get_client()
            values = await client.mget(keys)
            
            result = {}
            for key, value in zip(keys, values):
                if value is not None:
                    try:
                        result[key] = json.loads(value)
                    except (json.JSONDecodeError, TypeError):
                        result[key] = value
            
            logger.debug("Multiple values retrieved from Redis", keys=keys, found=len(result))
            return result
            
        except Exception as e:
            logger.error("Failed to get multiple values from Redis", keys=keys, error=str(e))
            return {}
    
    async def set_many(self, mapping: Dict[str, Any], ttl: Optional[int] = None) -> bool:
        """
        Set multiple values in Redis.
        
        Args:
            mapping: Dictionary of key-value pairs
            ttl: Time to live in seconds
            
        Returns:
            bool: True if successful
        """
        try:
            client = await self.get_client()
            
            # Serialize values
            serialized_mapping = {}
            for key, value in mapping.items():
                if isinstance(value, (dict, list)):
                    serialized_mapping[key] = json.dumps(value)
                else:
                    serialized_mapping[key] = value
            
            # Set multiple values
            result = await client.mset(serialized_mapping)
            
            # Set TTL if specified
            if ttl:
                pipeline = client.pipeline()
                for key in mapping.keys():
                    pipeline.expire(key, ttl)
                await pipeline.execute()
            
            logger.debug("Multiple values set in Redis", keys=list(mapping.keys()), ttl=ttl)
            return result
            
        except Exception as e:
            logger.error("Failed to set multiple values in Redis", keys=list(mapping.keys()), error=str(e))
            return False
    
    async def delete_pattern(self, pattern: str) -> int:
        """
        Delete keys matching pattern.
        
        Args:
            pattern: Key pattern (supports wildcards)
            
        Returns:
            int: Number of keys deleted
        """
        try:
            client = await self.get_client()
            
            # Find matching keys
            keys = await client.keys(pattern)
            
            if not keys:
                return 0
            
            # Delete keys
            result = await client.delete(*keys)
            
            logger.debug("Keys deleted by pattern", pattern=pattern, count=result)
            return result
            
        except Exception as e:
            logger.error("Failed to delete keys by pattern", pattern=pattern, error=str(e))
            return 0
    
    async def health_check(self) -> Dict[str, Any]:
        """
        Perform Redis health check.
        
        Returns:
            Dict[str, Any]: Health check results
        """
        async with self._health_check_lock:
            try:
                start_time = asyncio.get_event_loop().time()
                
                client = await self.get_client()
                
                # Test basic operations
                await client.ping()
                
                # Test set/get operations
                test_key = "health_check_test"
                await client.set(test_key, "test_value", ex=60)
                value = await client.get(test_key)
                await client.delete(test_key)
                
                # Get Redis info
                info = await client.info()
                
                response_time = asyncio.get_event_loop().time() - start_time
                
                return {
                    "status": "healthy",
                    "response_time": response_time,
                    "redis_version": info.get("redis_version"),
                    "connected_clients": info.get("connected_clients"),
                    "used_memory_human": info.get("used_memory_human"),
                    "keyspace": info.get("db0", {}),
                    "redis_url": settings.REDIS_URL.split("@")[1] if "@" in settings.REDIS_URL else "masked",
                }
                
            except Exception as e:
                logger.error("Redis health check failed", error=str(e))
                return {
                    "status": "unhealthy",
                    "error": str(e),
                    "redis_url": settings.REDIS_URL.split("@")[1] if "@" in settings.REDIS_URL else "masked",
                }
    
    async def close(self) -> None:
        """Close Redis connections."""
        if self._client:
            await self._client.close()
        if self._connection_pool:
            await self._connection_pool.disconnect()
        logger.info("Redis connections closed")


# Global Redis manager instance
_redis_manager: Optional[RedisManager] = None


def get_redis_manager() -> RedisManager:
    """
    Get the global Redis manager instance.
    
    Returns:
        RedisManager: Redis manager instance
    """
    global _redis_manager
    if _redis_manager is None:
        _redis_manager = RedisManager()
    return _redis_manager


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client.
    
    Returns:
        redis.Redis: Redis client instance
    """
    manager = get_redis_manager()
    return await manager.get_client()


# Cache utilities for Plant Care Application
class PlantCareCache:
    """Cache utilities specific to Plant Care Application."""
    
    # Cache key patterns
    USER_PATTERN = "user:{user_id}"
    PLANT_PATTERN = "plant:{plant_id}"
    CARE_SCHEDULE_PATTERN = "care_schedule:{plant_id}"
    WEATHER_PATTERN = "weather:{location}"
    API_USAGE_PATTERN = "api_usage:{user_id}:{api_name}"
    PLANT_LIBRARY_PATTERN = "plant_library:{species}"
    
    @staticmethod
    async def cache_user_data(user_id: str, data: dict, ttl: int = None) -> bool:
        """
        Cache user data.
        
        Args:
            user_id: User ID
            data: User data
            ttl: Time to live (default: USER_DATA TTL)
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        key = PlantCareCache.USER_PATTERN.format(user_id=user_id)
        ttl = ttl or settings.CACHE_TTL_USER_DATA
        return await manager.set(key, data, ttl=ttl)
    
    @staticmethod
    async def get_user_data(user_id: str) -> Optional[dict]:
        """
        Get cached user data.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[dict]: Cached user data
        """
        manager = get_redis_manager()
        key = PlantCareCache.USER_PATTERN.format(user_id=user_id)
        return await manager.get(key)
    
    @staticmethod
    async def cache_plant_data(plant_id: str, data: dict, ttl: int = None) -> bool:
        """
        Cache plant data.
        
        Args:
            plant_id: Plant ID
            data: Plant data
            ttl: Time to live (default: USER_DATA TTL)
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        key = PlantCareCache.PLANT_PATTERN.format(plant_id=plant_id)
        ttl = ttl or settings.CACHE_TTL_USER_DATA
        return await manager.set(key, data, ttl=ttl)
    
    @staticmethod
    async def get_plant_data(plant_id: str) -> Optional[dict]:
        """
        Get cached plant data.
        
        Args:
            plant_id: Plant ID
            
        Returns:
            Optional[dict]: Cached plant data
        """
        manager = get_redis_manager()
        key = PlantCareCache.PLANT_PATTERN.format(plant_id=plant_id)
        return await manager.get(key)
    
    @staticmethod
    async def cache_care_schedule(plant_id: str, schedule: dict, ttl: int = None) -> bool:
        """
        Cache care schedule.
        
        Args:
            plant_id: Plant ID
            schedule: Care schedule data
            ttl: Time to live (default: CARE_SCHEDULE TTL)
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        key = PlantCareCache.CARE_SCHEDULE_PATTERN.format(plant_id=plant_id)
        ttl = ttl or settings.CACHE_TTL_CARE_SCHEDULE
        return await manager.set(key, schedule, ttl=ttl)
    
    @staticmethod
    async def get_care_schedule(plant_id: str) -> Optional[dict]:
        """
        Get cached care schedule.
        
        Args:
            plant_id: Plant ID
            
        Returns:
            Optional[dict]: Cached care schedule
        """
        manager = get_redis_manager()
        key = PlantCareCache.CARE_SCHEDULE_PATTERN.format(plant_id=plant_id)
        return await manager.get(key)
    
    @staticmethod
    async def cache_weather_data(location: str, data: dict, ttl: int = None) -> bool:
        """
        Cache weather data.
        
        Args:
            location: Location identifier
            data: Weather data
            ttl: Time to live (default: WEATHER_DATA TTL)
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        key = PlantCareCache.WEATHER_PATTERN.format(location=location)
        ttl = ttl or settings.CACHE_TTL_WEATHER_DATA
        return await manager.set(key, data, ttl=ttl)
    
    @staticmethod
    async def get_weather_data(location: str) -> Optional[dict]:
        """
        Get cached weather data.
        
        Args:
            location: Location identifier
            
        Returns:
            Optional[dict]: Cached weather data
        """
        manager = get_redis_manager()
        key = PlantCareCache.WEATHER_PATTERN.format(location=location)
        return await manager.get(key)
    
    @staticmethod
    async def track_api_usage(user_id: str, api_name: str, increment: int = 1) -> int:
        """
        Track API usage for rate limiting.
        
        Args:
            user_id: User ID
            api_name: API name
            increment: Usage increment
            
        Returns:
            int: Current usage count
        """
        manager = get_redis_manager()
        key = PlantCareCache.API_USAGE_PATTERN.format(user_id=user_id, api_name=api_name)
        
        # Increment usage count
        usage = await manager.increment(key, increment)
        
        # Set TTL if this is the first increment
        if usage == increment:
            await manager.expire(key, 86400)  # 24 hours
        
        return usage
    
    @staticmethod
    async def get_api_usage(user_id: str, api_name: str) -> int:
        """
        Get current API usage count.
        
        Args:
            user_id: User ID
            api_name: API name
            
        Returns:
            int: Current usage count
        """
        manager = get_redis_manager()
        key = PlantCareCache.API_USAGE_PATTERN.format(user_id=user_id, api_name=api_name)
        usage = await manager.get(key, deserialize=False)
        return int(usage) if usage else 0
    
    @staticmethod
    async def cache_plant_library_entry(species: str, data: dict, ttl: int = None) -> bool:
        """
        Cache plant library entry.
        
        Args:
            species: Plant species
            data: Plant library data
            ttl: Time to live (default: PLANT_LIBRARY TTL)
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        key = PlantCareCache.PLANT_LIBRARY_PATTERN.format(species=species.lower().replace(" ", "_"))
        ttl = ttl or settings.CACHE_TTL_PLANT_LIBRARY
        return await manager.set(key, data, ttl=ttl)
    
    @staticmethod
    async def get_plant_library_entry(species: str) -> Optional[dict]:
        """
        Get cached plant library entry.
        
        Args:
            species: Plant species
            
        Returns:
            Optional[dict]: Cached plant library data
        """
        manager = get_redis_manager()
        key = PlantCareCache.PLANT_LIBRARY_PATTERN.format(species=species.lower().replace(" ", "_"))
        return await manager.get(key)
    
    @staticmethod
    async def invalidate_user_cache(user_id: str) -> bool:
        """
        Invalidate all cache entries for a user.
        
        Args:
            user_id: User ID
            
        Returns:
            bool: True if successful
        """
        manager = get_redis_manager()
        patterns = [
            f"user:{user_id}",
            f"plant:*:user:{user_id}",
            f"care_schedule:*:user:{user_id}",
            f"api_usage:{user_id}:*",
        ]
        
        total_deleted = 0
        for pattern in patterns:
            deleted = await manager.delete_pattern(pattern)
            total_deleted += deleted
        
        logger.info("User cache invalidated", user_id=user_id, entries_deleted=total_deleted)
        return total_deleted > 0


# Cache decorator for functions
def cache_result(
    key_pattern: str,
    ttl: int = 3600,
    serialize: bool = True
):
    """
    Decorator to cache function results.
    
    Args:
        key_pattern: Cache key pattern with placeholders
        ttl: Time to live in seconds
        serialize: Whether to serialize the result
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = key_pattern.format(*args, **kwargs)
            
            # Try to get from cache
            manager = get_redis_manager()
            cached_result = await manager.get(cache_key, deserialize=serialize)
            
            if cached_result is not None:
                logger.debug("Cache hit", cache_key=cache_key, function=func.__name__)
                return cached_result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await manager.set(cache_key, result, ttl=ttl, serialize=serialize)
            logger.debug("Cache miss, result cached", cache_key=cache_key, function=func.__name__)
            
            return result
        
        return wrapper
    return decorator


# Export Redis utilities
__all__ = [
    "RedisManager",
    "get_redis_manager",
    "get_redis_client",
    "PlantCareCache",
    "cache_result",
]