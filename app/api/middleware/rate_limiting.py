"""
app/api/middleware/rate_limiting.py
Plant Care Application - Rate Limiting Middleware

Advanced rate limiting middleware with Plant Care specific features:
- User-based rate limiting with premium tiers
- Endpoint-specific limits
- IP-based limiting for anonymous users
- Burst allowance and sliding windows
"""
import time
import json
from typing import Callable, Dict, Optional, Tuple
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.utils.formatters import format_error_response
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class RateLimitingMiddleware:
    """
    Rate limiting middleware for Plant Care Application.
    
    Implements multiple rate limiting strategies:
    1. User-based limits with premium tiers
    2. IP-based limits for anonymous users
    3. Endpoint-specific limits
    4. Sliding window algorithm
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
        # Rate limiting configuration
        self.limits = {
            # Default limits for authenticated users
            "user": {
                "requests_per_minute": 60,
                "requests_per_hour": 1000,
                "burst_allowance": 10
            },
            # Premium user limits
            "premium": {
                "requests_per_minute": 300,
                "requests_per_hour": 5000,
                "burst_allowance": 50
            },
            # Expert user limits
            "expert": {
                "requests_per_minute": 200,
                "requests_per_hour": 3000,
                "burst_allowance": 30
            },
            # Admin user limits (very high)
            "admin": {
                "requests_per_minute": 1000,
                "requests_per_hour": 10000,
                "burst_allowance": 100
            },
            # Anonymous/IP-based limits
            "anonymous": {
                "requests_per_minute": 20,
                "requests_per_hour": 200,
                "burst_allowance": 5
            }
        }
        
        # Endpoint-specific limits
        self.endpoint_limits = {
            # Authentication endpoints (stricter)
            "/api/v1/auth/login": {
                "requests_per_minute": 5,
                "requests_per_hour": 50,
                "burst_allowance": 2
            },
            "/api/v1/auth/register": {
                "requests_per_minute": 3,
                "requests_per_hour": 30,
                "burst_allowance": 1
            },
            "/api/v1/auth/forgot-password": {
                "requests_per_minute": 2,
                "requests_per_hour": 20,
                "burst_allowance": 1
            },
            # File upload endpoints
            "/api/v1/plants/upload": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "burst_allowance": 3
            },
            "/api/v1/growth/upload": {
                "requests_per_minute": 15,
                "requests_per_hour": 150,
                "burst_allowance": 5
            },
            # AI endpoints (resource intensive)
            "/api/v1/ai/chat": {
                "requests_per_minute": 20,
                "requests_per_hour": 200,
                "burst_allowance": 5
            },
            "/api/v1/ai/identify": {
                "requests_per_minute": 10,
                "requests_per_hour": 100,
                "burst_allowance": 3
            },
            # Analytics endpoints (premium only)
            "/api/v1/analytics": {
                "requests_per_minute": 30,
                "requests_per_hour": 300,
                "burst_allowance": 10
            }
        }
        
        # Paths excluded from rate limiting
        self.exclude_paths = {
            "/health",
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        # Redis client for storing rate limit data
        self.redis_manager = get_redis_manager()
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process rate limiting for incoming requests."""
        try:
            # Skip rate limiting for excluded paths
            if self._should_skip_rate_limiting(request.url.path):
                return await call_next(request)
            
            # Get rate limit info for this request
            limit_info = await self._get_rate_limit_info(request)
            
            # Check if request is within limits
            is_allowed, current_usage, reset_time = await self._check_rate_limits(
                limit_info["key"],
                limit_info["limits"]
            )
            
            if not is_allowed:
                # Log rate limit exceeded
                log_security_event(
                    event_type="rate_limit_exceeded",
                    user_id=limit_info.get("user_id"),
                    ip_address=request.client.host,
                    path=request.url.path,
                    limit_key=limit_info["key"]
                )
                
                # Return rate limit error
                return JSONResponse(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    content=format_error_response(
                        error_code="RATE_LIMIT_EXCEEDED",
                        message="Rate limit exceeded. Please try again later.",
                        status_code=429
                    ),
                    headers=self._get_rate_limit_headers(
                        current_usage,
                        limit_info["limits"],
                        reset_time
                    )
                )
            
            # Process request
            response = await call_next(request)
            
            # Add rate limit headers to response
            rate_limit_headers = self._get_rate_limit_headers(
                current_usage + 1,  # Account for current request
                limit_info["limits"],
                reset_time
            )
            
            for header, value in rate_limit_headers.items():
                response.headers[header] = value
            
            return response
            
        except Exception as e:
            logger.error("Rate limiting middleware error", error=str(e), path=request.url.path)
            # Don't block requests if rate limiting fails
            return await call_next(request)
    
    def _should_skip_rate_limiting(self, path: str) -> bool:
        """Check if rate limiting should be skipped for this path."""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    async def _get_rate_limit_info(self, request: Request) -> Dict:
        """Get rate limiting information for the request."""
        # Get user information from request state (set by auth middleware)
        user = getattr(request.state, "user", None)
        
        # Determine rate limit key and limits
        if user:
            # Authenticated user
            user_id = user["user_id"]
            user_role = user.get("role", "user")
            is_premium = user.get("is_premium", False)
            
            # Determine user tier for rate limiting
            if user_role == "admin":
                tier = "admin"
            elif user_role == "expert":
                tier = "expert"
            elif is_premium:
                tier = "premium"
            else:
                tier = "user"
            
            limit_key = f"rate_limit:user:{user_id}"
            limits = self.limits[tier].copy()
            
        else:
            # Anonymous user - use IP-based limiting
            ip_address = self._get_client_ip(request)
            limit_key = f"rate_limit:ip:{ip_address}"
            limits = self.limits["anonymous"].copy()
            user_id = None
        
        # Check for endpoint-specific limits
        endpoint_limits = self._get_endpoint_limits(request.url.path)
        if endpoint_limits:
            limits.update(endpoint_limits)
        
        return {
            "key": limit_key,
            "limits": limits,
            "user_id": user_id,
            "path": request.url.path
        }
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address."""
        # Check for forwarded headers
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fallback to direct client IP
        return request.client.host
    
    def _get_endpoint_limits(self, path: str) -> Optional[Dict]:
        """Get endpoint-specific rate limits."""
        # Check exact path matches first
        if path in self.endpoint_limits:
            return self.endpoint_limits[path]
        
        # Check prefix matches
        for endpoint_path, limits in self.endpoint_limits.items():
            if path.startswith(endpoint_path):
                return limits
        
        return None
    
    async def _check_rate_limits(
        self, 
        limit_key: str, 
        limits: Dict
    ) -> Tuple[bool, int, int]:
        """
        Check if request is within rate limits using sliding window.
        
        Returns:
            Tuple[bool, int, int]: (is_allowed, current_usage, reset_time)
        """
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = int(time.time())
            
            # Check minute window
            minute_key = f"{limit_key}:minute:{current_time // 60}"
            minute_count = await redis_client.get(minute_key)
            minute_count = int(minute_count) if minute_count else 0
            
            # Check hour window  
            hour_key = f"{limit_key}:hour:{current_time // 3600}"
            hour_count = await redis_client.get(hour_key)
            hour_count = int(hour_count) if hour_count else 0
            
            # Check burst allowance (last 10 seconds)
            burst_key = f"{limit_key}:burst:{current_time // 10}"
            burst_count = await redis_client.get(burst_key)
            burst_count = int(burst_count) if burst_count else 0
            
            # Check limits
            minute_limit = limits["requests_per_minute"]
            hour_limit = limits["requests_per_hour"]
            burst_limit = limits["burst_allowance"]
            
            if (minute_count >= minute_limit or 
                hour_count >= hour_limit or 
                burst_count >= burst_limit):
                return False, max(minute_count, hour_count, burst_count), current_time + 60
            
            # Increment counters
            pipe = redis_client.pipeline()
            
            # Increment minute counter
            pipe.incr(minute_key)
            pipe.expire(minute_key, 120)  # Keep for 2 minutes
            
            # Increment hour counter
            pipe.incr(hour_key)
            pipe.expire(hour_key, 7200)  # Keep for 2 hours
            
            # Increment burst counter
            pipe.incr(burst_key)
            pipe.expire(burst_key, 20)  # Keep for 20 seconds
            
            await pipe.execute()
            
            return True, max(minute_count, hour_count, burst_count), current_time + 60
            
        except Exception as e:
            logger.error("Rate limit check error", error=str(e), limit_key=limit_key)
            # Allow request if rate limiting check fails
            return True, 0, current_time + 60
    
    def _get_rate_limit_headers(
        self, 
        current_usage: int, 
        limits: Dict, 
        reset_time: int
    ) -> Dict[str, str]:
        """Get rate limit headers for response."""
        minute_limit = limits["requests_per_minute"]
        hour_limit = limits["requests_per_hour"]
        
        return {
            "X-RateLimit-Limit-Minute": str(minute_limit),
            "X-RateLimit-Limit-Hour": str(hour_limit),
            "X-RateLimit-Remaining-Minute": str(max(0, minute_limit - current_usage)),
            "X-RateLimit-Remaining-Hour": str(max(0, hour_limit - current_usage)),
            "X-RateLimit-Reset": str(reset_time),
            "X-RateLimit-Reset-After": str(max(0, reset_time - int(time.time())))
        }
    
    async def get_rate_limit_status(self, limit_key: str) -> Dict:
        """Get current rate limit status for a key."""
        try:
            redis_client = await self.redis_manager.get_client()
            current_time = int(time.time())
            
            # Get current usage
            minute_key = f"{limit_key}:minute:{current_time // 60}"
            hour_key = f"{limit_key}:hour:{current_time // 3600}"
            burst_key = f"{limit_key}:burst:{current_time // 10}"
            
            minute_count = await redis_client.get(minute_key)
            hour_count = await redis_client.get(hour_key)
            burst_count = await redis_client.get(burst_key)
            
            return {
                "minute_usage": int(minute_count) if minute_count else 0,
                "hour_usage": int(hour_count) if hour_count else 0,
                "burst_usage": int(burst_count) if burst_count else 0,
                "reset_time": current_time + 60
            }
            
        except Exception as e:
            logger.error("Error getting rate limit status", error=str(e))
            return {
                "minute_usage": 0,
                "hour_usage": 0,
                "burst_usage": 0,
                "reset_time": int(time.time()) + 60
            }
    
    async def reset_rate_limits(self, limit_key: str) -> bool:
        """Reset rate limits for a specific key (admin function)."""
        try:
            redis_client = await self.redis_manager.get_client()
            
            # Delete all rate limit keys for this user/IP
            keys_pattern = f"{limit_key}:*"
            keys = await redis_client.keys(keys_pattern)
            
            if keys:
                await redis_client.delete(*keys)
                return True
            
            return False
            
        except Exception as e:
            logger.error("Error resetting rate limits", error=str(e))
            return False
    
    def get_middleware_status(self) -> Dict:
        """Get rate limiting middleware status."""
        return {
            "name": "RateLimitingMiddleware",
            "enabled": True,
            "limits_configured": len(self.limits),
            "endpoint_limits_configured": len(self.endpoint_limits),
            "exclude_paths_count": len(self.exclude_paths),
            "redis_connected": self.redis_manager is not None
        }


# Standalone rate limiting functions
async def check_user_rate_limit(user_id: str, limits: Dict) -> Tuple[bool, Dict]:
    """
    Check rate limits for a specific user.
    
    Args:
        user_id: User ID to check
        limits: Rate limit configuration
        
    Returns:
        Tuple[bool, Dict]: (is_within_limits, status_info)
    """
    middleware = RateLimitingMiddleware(None)
    limit_key = f"rate_limit:user:{user_id}"
    
    is_allowed, current_usage, reset_time = await middleware._check_rate_limits(
        limit_key, limits
    )
    
    status_info = await middleware.get_rate_limit_status(limit_key)
    
    return is_allowed, status_info


async def reset_user_rate_limits(user_id: str) -> bool:
    """Reset rate limits for a specific user (admin function)."""
    middleware = RateLimitingMiddleware(None)
    limit_key = f"rate_limit:user:{user_id}"
    return await middleware.reset_rate_limits(limit_key)