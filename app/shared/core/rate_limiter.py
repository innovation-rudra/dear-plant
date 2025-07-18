"""
app/shared/core/rate_limiter.py
Plant Care Application - Core Rate Limiting Logic

Core rate limiting utilities for Plant Care Application.
Provides advanced rate limiting algorithms and Plant Care specific policies.
Integrates with existing Redis infrastructure and user management.
"""
import time
import asyncio
from typing import Dict, Optional, Tuple, List, Any, Union,Callable
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum
import structlog
import math

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.core.exceptions import RateLimitExceededError, PlantCareException
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class RateLimitAlgorithm(Enum):
    """Rate limiting algorithms for Plant Care."""
    FIXED_WINDOW = "fixed_window"
    SLIDING_WINDOW = "sliding_window" 
    TOKEN_BUCKET = "token_bucket"
    LEAKY_BUCKET = "leaky_bucket"

class RateLimitScope(Enum):
    """Rate limit scopes for Plant Care operations."""
    GLOBAL = "global"                    # Global limits
    USER = "user"                        # Per-user limits
    IP = "ip"                           # Per-IP limits
    API_KEY = "api_key"                 # Per-API key limits
    ENDPOINT = "endpoint"               # Per-endpoint limits
    FEATURE = "feature"                 # Per-feature limits (AI, uploads, etc.)

@dataclass
class RateLimitRule:
    """Rate limiting rule configuration."""
    name: str
    requests: int                        # Number of requests allowed
    window: int                         # Time window in seconds
    algorithm: RateLimitAlgorithm = RateLimitAlgorithm.SLIDING_WINDOW
    scope: RateLimitScope = RateLimitScope.USER
    burst_allowance: int = 0            # Additional burst requests
    penalty_multiplier: float = 1.0    # Penalty for violations
    exceptions: List[str] = field(default_factory=list)  # Exceptions (user IDs, IPs)

@dataclass
class RateLimitResult:
    """Result of rate limit check."""
    allowed: bool
    current_usage: int
    limit: int
    reset_time: int
    retry_after: Optional[int] = None
    headers: Dict[str, str] = field(default_factory=dict)

class PlantCareRateLimiter:
    """
    Advanced rate limiter for Plant Care Application.
    
    Provides multiple rate limiting strategies for different Plant Care operations:
    - API endpoint limits
    - Feature-specific limits (AI, file uploads, plant identification)
    - User tier-based limits (free, premium, expert, admin)
    - Abuse prevention
    - Dynamic adjustments based on system load
    """
    
    def __init__(self):
        self.redis_manager = get_redis_manager()
        
        # Plant Care specific rate limit rules
        self.rules = self._setup_plant_care_rules()
        
        # User tier multipliers
        self.tier_multipliers = {
            "free": 1.0,
            "premium_monthly": 5.0,
            "premium_yearly": 5.0,
            "expert": 3.0,
            "admin": 100.0,
            "service": 1000.0
        }
        
        # Feature-specific limits
        self.feature_limits = {
            "plant_identification": {
                "free": {"requests": 5, "window": 3600},       # 5 per hour
                "premium": {"requests": 50, "window": 3600},    # 50 per hour
                "expert": {"requests": 100, "window": 3600}     # 100 per hour
            },
            "ai_chat": {
                "free": {"requests": 10, "window": 3600},      # 10 per hour
                "premium": {"requests": 200, "window": 3600},   # 200 per hour
                "expert": {"requests": 500, "window": 3600}     # 500 per hour
            },
            "file_upload": {
                "free": {"requests": 20, "window": 3600},      # 20 per hour
                "premium": {"requests": 500, "window": 3600},   # 500 per hour
                "expert": {"requests": 1000, "window": 3600}   # 1000 per hour
            },
            "care_reminders": {
                "free": {"requests": 100, "window": 86400},    # 100 per day
                "premium": {"requests": 1000, "window": 86400}, # 1000 per day
                "expert": {"requests": 2000, "window": 86400}   # 2000 per day
            },
            "analytics_queries": {
                "free": {"requests": 0, "window": 3600},       # Not available
                "premium": {"requests": 50, "window": 3600},    # 50 per hour
                "expert": {"requests": 200, "window": 3600}     # 200 per hour
            }
        }
    
    def _setup_plant_care_rules(self) -> Dict[str, RateLimitRule]:
        """Setup Plant Care specific rate limiting rules."""
        return {
            # General API limits
            "api_general": RateLimitRule(
                name="api_general",
                requests=1000,
                window=3600,  # 1 hour
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER,
                burst_allowance=50
            ),
            
            # Authentication limits
            "auth_login": RateLimitRule(
                name="auth_login",
                requests=5,
                window=300,  # 5 minutes
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                scope=RateLimitScope.IP,
                penalty_multiplier=2.0
            ),
            "auth_register": RateLimitRule(
                name="auth_register",
                requests=3,
                window=3600,  # 1 hour
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                scope=RateLimitScope.IP
            ),
            "password_reset": RateLimitRule(
                name="password_reset",
                requests=3,
                window=3600,  # 1 hour
                algorithm=RateLimitAlgorithm.FIXED_WINDOW,
                scope=RateLimitScope.USER
            ),
            
            # Plant Care feature limits
            "plant_identification": RateLimitRule(
                name="plant_identification",
                requests=5,  # Base for free users
                window=3600,
                algorithm=RateLimitAlgorithm.TOKEN_BUCKET,
                scope=RateLimitScope.USER,
                burst_allowance=2
            ),
            "ai_chat": RateLimitRule(
                name="ai_chat",
                requests=10,  # Base for free users
                window=3600,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER,
                burst_allowance=3
            ),
            "file_upload": RateLimitRule(
                name="file_upload",
                requests=20,  # Base for free users
                window=3600,
                algorithm=RateLimitAlgorithm.LEAKY_BUCKET,
                scope=RateLimitScope.USER,
                burst_allowance=5
            ),
            
            # Content creation limits
            "plant_creation": RateLimitRule(
                name="plant_creation",
                requests=10,
                window=3600,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER
            ),
            "community_post": RateLimitRule(
                name="community_post",
                requests=5,
                window=3600,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER
            ),
            "community_comment": RateLimitRule(
                name="community_comment",
                requests=20,
                window=3600,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.USER
            ),
            
            # Abuse prevention
            "ip_global": RateLimitRule(
                name="ip_global",
                requests=10000,
                window=3600,
                algorithm=RateLimitAlgorithm.SLIDING_WINDOW,
                scope=RateLimitScope.IP,
                penalty_multiplier=5.0
            )
        }
    
    async def check_rate_limit(
        self,
        rule_name: str,
        identifier: str,
        user_tier: str = "free",
        feature: Optional[str] = None,
        custom_limit: Optional[int] = None
    ) -> RateLimitResult:
        """
        Check rate limit for Plant Care operation.
        
        Args:
            rule_name: Name of rate limit rule
            identifier: Unique identifier (user_id, ip, api_key)
            user_tier: User subscription tier
            feature: Optional feature name for feature-specific limits
            custom_limit: Optional custom limit override
            
        Returns:
            RateLimitResult with decision and metadata
        """
        try:
            # Get rate limit rule
            rule = self.rules.get(rule_name)
            if not rule:
                logger.warning("Rate limit rule not found", rule_name=rule_name)
                return RateLimitResult(allowed=True, current_usage=0, limit=0, reset_time=0)
            
            # Calculate effective limits based on user tier and feature
            effective_limit = self._calculate_effective_limit(rule, user_tier, feature, custom_limit)
            
            # Check rate limit based on algorithm
            if rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                result = await self._check_sliding_window(rule, identifier, effective_limit)
            elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                result = await self._check_fixed_window(rule, identifier, effective_limit)
            elif rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                result = await self._check_token_bucket(rule, identifier, effective_limit)
            elif rule.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                result = await self._check_leaky_bucket(rule, identifier, effective_limit)
            else:
                result = await self._check_sliding_window(rule, identifier, effective_limit)
            
            # Add rate limit headers
            result.headers = self._generate_rate_limit_headers(result, rule)
            
            # Log rate limit check
            if not result.allowed:
                logger.warning(
                    "Rate limit exceeded",
                    rule_name=rule_name,
                    identifier=identifier,
                    user_tier=user_tier,
                    current_usage=result.current_usage,
                    limit=result.limit
                )
                
                # Log security event for potential abuse
                if result.current_usage > result.limit * 2:
                    log_security_event(
                        event_type="rate_limit_abuse",
                        rule_name=rule_name,
                        identifier=identifier,
                        usage=result.current_usage,
                        limit=result.limit
                    )
            
            return result
            
        except Exception as e:
            logger.error("Rate limit check failed", rule_name=rule_name, error=str(e))
            # Fail open - allow request if rate limiting fails
            return RateLimitResult(allowed=True, current_usage=0, limit=0, reset_time=0)
    
    def _calculate_effective_limit(
        self,
        rule: RateLimitRule,
        user_tier: str,
        feature: Optional[str],
        custom_limit: Optional[int]
    ) -> int:
        """Calculate effective rate limit based on user tier and feature."""
        if custom_limit:
            return custom_limit
        
        base_limit = rule.requests
        
        # Apply feature-specific limits
        if feature and feature in self.feature_limits:
            feature_config = self.feature_limits[feature]
            tier_key = "premium" if user_tier.startswith("premium") else user_tier
            
            if tier_key in feature_config:
                base_limit = feature_config[tier_key]["requests"]
        
        # Apply tier multiplier
        multiplier = self.tier_multipliers.get(user_tier, 1.0)
        effective_limit = int(base_limit * multiplier)
        
        return max(effective_limit, 1)  # Ensure at least 1 request
    
    async def _check_sliding_window(
        self,
        rule: RateLimitRule,
        identifier: str,
        limit: int
    ) -> RateLimitResult:
        """Check rate limit using sliding window algorithm."""
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = time.time()
            window_start = current_time - rule.window
            
            # Create Redis key
            key = f"rate_limit:sliding:{rule.name}:{identifier}"
            
            # Remove old entries and count current requests
            pipe = redis_client.pipeline()
            pipe.zremrangebyscore(key, 0, window_start)
            pipe.zcard(key)
            pipe.expire(key, rule.window + 60)  # Add buffer to TTL
            
            results = await pipe.execute()
            current_usage = results[1]
            
            reset_time = int(current_time + rule.window)
            
            if current_usage >= limit:
                return RateLimitResult(
                    allowed=False,
                    current_usage=current_usage,
                    limit=limit,
                    reset_time=reset_time,
                    retry_after=int(rule.window)
                )
            
            # Add current request
            await redis_client.zadd(key, {str(current_time): current_time})
            
            return RateLimitResult(
                allowed=True,
                current_usage=current_usage + 1,
                limit=limit,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error("Sliding window rate limit check failed", error=str(e))
            return RateLimitResult(allowed=True, current_usage=0, limit=limit, reset_time=0)
    
    async def _check_fixed_window(
        self,
        rule: RateLimitRule,
        identifier: str,
        limit: int
    ) -> RateLimitResult:
        """Check rate limit using fixed window algorithm."""
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = int(time.time())
            window_start = (current_time // rule.window) * rule.window
            
            key = f"rate_limit:fixed:{rule.name}:{identifier}:{window_start}"
            
            current_usage = await redis_client.get(key)
            current_usage = int(current_usage) if current_usage else 0
            
            reset_time = window_start + rule.window
            
            if current_usage >= limit:
                return RateLimitResult(
                    allowed=False,
                    current_usage=current_usage,
                    limit=limit,
                    reset_time=reset_time,
                    retry_after=reset_time - current_time
                )
            
            # Increment counter
            pipe = redis_client.pipeline()
            pipe.incr(key)
            pipe.expire(key, rule.window + 60)
            await pipe.execute()
            
            return RateLimitResult(
                allowed=True,
                current_usage=current_usage + 1,
                limit=limit,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error("Fixed window rate limit check failed", error=str(e))
            return RateLimitResult(allowed=True, current_usage=0, limit=limit, reset_time=0)
    
    async def _check_token_bucket(
        self,
        rule: RateLimitRule,
        identifier: str,
        limit: int
    ) -> RateLimitResult:
        """Check rate limit using token bucket algorithm."""
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = time.time()
            
            key = f"rate_limit:bucket:{rule.name}:{identifier}"
            
            # Get current bucket state
            bucket_data = await redis_client.hmget(key, "tokens", "last_refill")
            tokens = float(bucket_data[0]) if bucket_data[0] else float(limit)
            last_refill = float(bucket_data[1]) if bucket_data[1] else current_time
            
            # Calculate tokens to add based on time elapsed
            time_elapsed = current_time - last_refill
            refill_rate = limit / rule.window  # tokens per second
            tokens_to_add = time_elapsed * refill_rate
            tokens = min(limit, tokens + tokens_to_add)
            
            reset_time = int(current_time + (limit - tokens) / refill_rate)
            
            if tokens < 1:
                # Update bucket state
                await redis_client.hmset(key, {
                    "tokens": tokens,
                    "last_refill": current_time
                })
                await redis_client.expire(key, rule.window + 60)
                
                return RateLimitResult(
                    allowed=False,
                    current_usage=int(limit - tokens),
                    limit=limit,
                    reset_time=reset_time,
                    retry_after=int(1 / refill_rate)
                )
            
            # Consume one token
            tokens -= 1
            
            # Update bucket state
            await redis_client.hmset(key, {
                "tokens": tokens,
                "last_refill": current_time
            })
            await redis_client.expire(key, rule.window + 60)
            
            return RateLimitResult(
                allowed=True,
                current_usage=int(limit - tokens),
                limit=limit,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error("Token bucket rate limit check failed", error=str(e))
            return RateLimitResult(allowed=True, current_usage=0, limit=limit, reset_time=0)
    
    async def _check_leaky_bucket(
        self,
        rule: RateLimitRule,
        identifier: str,
        limit: int
    ) -> RateLimitResult:
        """Check rate limit using leaky bucket algorithm."""
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = time.time()
            
            key = f"rate_limit:leaky:{rule.name}:{identifier}"
            
            # Get current bucket state
            bucket_data = await redis_client.hmget(key, "level", "last_leak")
            level = float(bucket_data[0]) if bucket_data[0] else 0.0
            last_leak = float(bucket_data[1]) if bucket_data[1] else current_time
            
            # Calculate how much has leaked out
            time_elapsed = current_time - last_leak
            leak_rate = limit / rule.window  # requests per second that leak out
            leaked = time_elapsed * leak_rate
            level = max(0, level - leaked)
            
            reset_time = int(current_time + (level / leak_rate))
            
            if level >= limit:
                # Update bucket state
                await redis_client.hmset(key, {
                    "level": level,
                    "last_leak": current_time
                })
                await redis_client.expire(key, rule.window + 60)
                
                return RateLimitResult(
                    allowed=False,
                    current_usage=int(level),
                    limit=limit,
                    reset_time=reset_time,
                    retry_after=int(1 / leak_rate)
                )
            
            # Add current request to bucket
            level += 1
            
            # Update bucket state
            await redis_client.hmset(key, {
                "level": level,
                "last_leak": current_time
            })
            await redis_client.expire(key, rule.window + 60)
            
            return RateLimitResult(
                allowed=True,
                current_usage=int(level),
                limit=limit,
                reset_time=reset_time
            )
            
        except Exception as e:
            logger.error("Leaky bucket rate limit check failed", error=str(e))
            return RateLimitResult(allowed=True, current_usage=0, limit=limit, reset_time=0)
    
    def _generate_rate_limit_headers(
        self,
        result: RateLimitResult,
        rule: RateLimitRule
    ) -> Dict[str, str]:
        """Generate rate limit headers for HTTP responses."""
        headers = {
            "X-RateLimit-Limit": str(result.limit),
            "X-RateLimit-Remaining": str(max(0, result.limit - result.current_usage)),
            "X-RateLimit-Reset": str(result.reset_time),
            "X-RateLimit-Window": str(rule.window),
            "X-RateLimit-Algorithm": rule.algorithm.value
        }
        
        if result.retry_after:
            headers["Retry-After"] = str(result.retry_after)
        
        return headers
    
    async def reset_rate_limit(self, rule_name: str, identifier: str) -> bool:
        """Reset rate limit for specific identifier (admin function)."""
        try:
            redis_client = await self.redis_manager.get_client()
            rule = self.rules.get(rule_name)
            
            if not rule:
                return False
            
            # Delete all rate limit keys for this identifier and rule
            patterns = [
                f"rate_limit:sliding:{rule_name}:{identifier}",
                f"rate_limit:fixed:{rule_name}:{identifier}:*",
                f"rate_limit:bucket:{rule_name}:{identifier}",
                f"rate_limit:leaky:{rule_name}:{identifier}"
            ]
            
            for pattern in patterns:
                if "*" in pattern:
                    keys = await redis_client.keys(pattern)
                    if keys:
                        await redis_client.delete(*keys)
                else:
                    await redis_client.delete(pattern)
            
            logger.info(
                "Rate limit reset",
                rule_name=rule_name,
                identifier=identifier
            )
            
            return True
            
        except Exception as e:
            logger.error("Failed to reset rate limit", error=str(e))
            return False
    
    async def get_rate_limit_status(
        self,
        rule_name: str,
        identifier: str
    ) -> Optional[Dict[str, Any]]:
        """Get current rate limit status for identifier."""
        try:
            rule = self.rules.get(rule_name)
            if not rule:
                return None
            
            redis_client = await self.redis_manager.get_client()
            
            if rule.algorithm == RateLimitAlgorithm.SLIDING_WINDOW:
                key = f"rate_limit:sliding:{rule_name}:{identifier}"
                current_usage = await redis_client.zcard(key)
            elif rule.algorithm == RateLimitAlgorithm.FIXED_WINDOW:
                current_time = int(time.time())
                window_start = (current_time // rule.window) * rule.window
                key = f"rate_limit:fixed:{rule_name}:{identifier}:{window_start}"
                usage = await redis_client.get(key)
                current_usage = int(usage) if usage else 0
            elif rule.algorithm == RateLimitAlgorithm.TOKEN_BUCKET:
                key = f"rate_limit:bucket:{rule_name}:{identifier}"
                bucket_data = await redis_client.hmget(key, "tokens")
                tokens = float(bucket_data[0]) if bucket_data[0] else float(rule.requests)
                current_usage = rule.requests - int(tokens)
            elif rule.algorithm == RateLimitAlgorithm.LEAKY_BUCKET:
                key = f"rate_limit:leaky:{rule_name}:{identifier}"
                bucket_data = await redis_client.hmget(key, "level")
                current_usage = int(float(bucket_data[0])) if bucket_data[0] else 0
            else:
                current_usage = 0
            
            return {
                "rule_name": rule_name,
                "identifier": identifier,
                "current_usage": current_usage,
                "limit": rule.requests,
                "window": rule.window,
                "algorithm": rule.algorithm.value,
                "reset_time": int(time.time() + rule.window)
            }
            
        except Exception as e:
            logger.error("Failed to get rate limit status", error=str(e))
            return None
    
    def add_rule(self, rule: RateLimitRule):
        """Add custom rate limit rule."""
        self.rules[rule.name] = rule
        
        logger.info(
            "Rate limit rule added",
            rule_name=rule.name,
            requests=rule.requests,
            window=rule.window,
            algorithm=rule.algorithm.value
        )
    
    def remove_rule(self, rule_name: str) -> bool:
        """Remove rate limit rule."""
        if rule_name in self.rules:
            del self.rules[rule_name]
            logger.info("Rate limit rule removed", rule_name=rule_name)
            return True
        return False
    
    def get_all_rules(self) -> Dict[str, Dict[str, Any]]:
        """Get all rate limit rules."""
        return {
            name: {
                "requests": rule.requests,
                "window": rule.window,
                "algorithm": rule.algorithm.value,
                "scope": rule.scope.value,
                "burst_allowance": rule.burst_allowance,
                "penalty_multiplier": rule.penalty_multiplier
            }
            for name, rule in self.rules.items()
        }

# Global rate limiter instance
_plant_care_rate_limiter: Optional[PlantCareRateLimiter] = None

def get_rate_limiter() -> PlantCareRateLimiter:
    """Get the global Plant Care rate limiter instance."""
    global _plant_care_rate_limiter
    if _plant_care_rate_limiter is None:
        _plant_care_rate_limiter = PlantCareRateLimiter()
    return _plant_care_rate_limiter

# Convenience functions for Plant Care rate limiting
async def check_plant_care_rate_limit(
    operation: str,
    identifier: str,
    user_tier: str = "free",
    feature: Optional[str] = None
) -> RateLimitResult:
    """Check rate limit for Plant Care operation."""
    rate_limiter = get_rate_limiter()
    return await rate_limiter.check_rate_limit(
        rule_name=operation,
        identifier=identifier,
        user_tier=user_tier,
        feature=feature
    )

async def check_user_rate_limit(
    user_id: str,
    operation: str,
    user_tier: str = "free"
) -> RateLimitResult:
    """Check rate limit for user operation."""
    return await check_plant_care_rate_limit(
        operation=operation,
        identifier=user_id,
        user_tier=user_tier
    )

async def check_ip_rate_limit(ip_address: str, operation: str) -> RateLimitResult:
    """Check rate limit for IP address."""
    return await check_plant_care_rate_limit(
        operation=operation,
        identifier=ip_address,
        user_tier="free"  # IPs get free tier limits
    )

async def check_feature_rate_limit(
    user_id: str,
    feature: str,
    user_tier: str = "free"
) -> RateLimitResult:
    """Check rate limit for specific Plant Care feature."""
    return await check_plant_care_rate_limit(
        operation=feature,
        identifier=user_id,
        user_tier=user_tier,
        feature=feature
    )

# Plant Care specific rate limit checks
async def check_plant_identification_limit(
    user_id: str,
    user_tier: str = "free"
) -> RateLimitResult:
    """Check plant identification rate limit."""
    return await check_feature_rate_limit(
        user_id=user_id,
        feature="plant_identification",
        user_tier=user_tier
    )

async def check_ai_chat_limit(user_id: str, user_tier: str = "free") -> RateLimitResult:
    """Check AI chat rate limit."""
    return await check_feature_rate_limit(
        user_id=user_id,
        feature="ai_chat",
        user_tier=user_tier
    )

async def check_file_upload_limit(
    user_id: str,
    user_tier: str = "free"
) -> RateLimitResult:
    """Check file upload rate limit."""
    return await check_feature_rate_limit(
        user_id=user_id,
        feature="file_upload",
        user_tier=user_tier
    )

async def check_analytics_limit(
    user_id: str,
    user_tier: str = "free"
) -> RateLimitResult:
    """Check analytics query rate limit."""
    return await check_feature_rate_limit(
        user_id=user_id,
        feature="analytics_queries",
        user_tier=user_tier
    )

# Rate limit enforcement decorator
def enforce_rate_limit(
    operation: str,
    get_identifier: Callable = None,
    get_user_tier: Callable = None,
    feature: Optional[str] = None
):
    """
    Decorator to enforce rate limiting on Plant Care functions.
    
    Usage:
        @enforce_rate_limit("plant_identification", feature="plant_identification")
        async def identify_plant(user_id: str, image_data: bytes):
            # Function implementation
            pass
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract identifier (default to first argument as user_id)
            if get_identifier:
                identifier = get_identifier(*args, **kwargs)
            else:
                identifier = args[0] if args else kwargs.get("user_id", "unknown")
            
            # Extract user tier (default to "free")
            if get_user_tier:
                user_tier = get_user_tier(*args, **kwargs)
            else:
                user_tier = kwargs.get("user_tier", "free")
            
            # Check rate limit
            result = await check_plant_care_rate_limit(
                operation=operation,
                identifier=identifier,
                user_tier=user_tier,
                feature=feature
            )
            
            if not result.allowed:
                raise RateLimitExceededError(
                    f"Rate limit exceeded for {operation}. "
                    f"Try again in {result.retry_after} seconds."
                )
            
            # Execute function
            return await func(*args, **kwargs)
        
        return wrapper
    return decorator

# Admin functions
async def reset_user_rate_limits(user_id: str) -> Dict[str, bool]:
    """Reset all rate limits for a user (admin function)."""
    rate_limiter = get_rate_limiter()
    results = {}
    
    for rule_name in rate_limiter.rules.keys():
        results[rule_name] = await rate_limiter.reset_rate_limit(rule_name, user_id)
    
    return results

async def get_rate_limit_stats() -> Dict[str, Any]:
    """Get rate limiting statistics."""
    rate_limiter = get_rate_limiter()
    
    return {
        "total_rules": len(rate_limiter.rules),
        "rules": rate_limiter.get_all_rules(),
        "tier_multipliers": rate_limiter.tier_multipliers,
        "feature_limits": rate_limiter.feature_limits
    }