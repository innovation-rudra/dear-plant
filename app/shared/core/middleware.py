"""
Plant Care Application - Custom Middleware
"""
import time
import uuid
from typing import Callable, Dict, Any
import asyncio

from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
import structlog

from app.shared.config.settings import get_settings
from app.shared.utils.logging import log_security_event
from app.shared.infrastructure.cache.redis_client import get_redis_manager

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add security headers to responses.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.security_headers = {
            "X-Content-Type-Options": "nosniff",
            "X-Frame-Options": "DENY",
            "X-XSS-Protection": "1; mode=block",
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            "Referrer-Policy": "strict-origin-when-cross-origin",
            "Content-Security-Policy": "default-src 'self'",
            "Permissions-Policy": "geolocation=(), microphone=(), camera=()",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add security headers to response."""
        response = await call_next(request)
        
        # Add security headers
        for header, value in self.security_headers.items():
            response.headers[header] = value
        
        # Add custom headers
        response.headers["X-Plant-Care-Version"] = settings.APP_VERSION
        response.headers["X-Request-ID"] = getattr(request.state, "request_id", str(uuid.uuid4()))
        
        return response


class ProcessTimeMiddleware(BaseHTTPMiddleware):
    """
    Middleware to add process time header and log performance metrics.
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Add process time tracking."""
        start_time = time.time()
        
        # Add request ID to state
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Process request
        response = await call_next(request)
        
        # Calculate process time
        process_time = time.time() - start_time
        
        # Add headers
        response.headers["X-Process-Time"] = str(process_time)
        response.headers["X-Request-ID"] = request_id
        
        # Log performance if slow
        if process_time > 1.0:  # Log requests taking more than 1 second
            logger.warning(
                "Slow request detected",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                process_time=process_time,
                status_code=response.status_code,
            )
        
        return response


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Middleware to log HTTP requests and responses.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.exclude_paths = {
            "/health/live",
            "/health/ready", 
            "/metrics",
            "/favicon.ico",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Log request and response details."""
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get request details
        request_id = getattr(request.state, "request_id", str(uuid.uuid4()))
        start_time = time.time()
        
        # Get client info
        client_ip = self._get_client_ip(request)
        user_agent = request.headers.get("user-agent", "")
        
        # Log request
        logger.info(
            "HTTP request started",
            request_id=request_id,
            method=request.method,
            url=str(request.url),
            client_ip=client_ip,
            user_agent=user_agent,
            headers=dict(request.headers) if settings.DEBUG else {},
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Log response
            process_time = time.time() - start_time
            logger.info(
                "HTTP request completed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                status_code=response.status_code,
                process_time=process_time,
                client_ip=client_ip,
            )
            
            return response
            
        except Exception as e:
            # Log error
            process_time = time.time() - start_time
            logger.error(
                "HTTP request failed",
                request_id=request_id,
                method=request.method,
                url=str(request.url),
                error=str(e),
                process_time=process_time,
                client_ip=client_ip,
                exc_info=True,
            )
            
            # Return error response
            return JSONResponse(
                status_code=500,
                content={
                    "error": {
                        "code": "INTERNAL_SERVER_ERROR",
                        "message": "An internal server error occurred",
                        "request_id": request_id,
                    }
                }
            )
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address from request."""
        # Check X-Forwarded-For header (from load balancer/proxy)
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        # Check X-Real-IP header
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        # Fall back to direct client IP
        return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware for rate limiting requests.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.rate_limit_requests = settings.RATE_LIMIT_REQUESTS
        self.rate_limit_period = settings.RATE_LIMIT_PERIOD
        self.rate_limit_burst = settings.RATE_LIMIT_BURST
        self.exclude_paths = {
            "/health/live",
            "/health/ready",
            "/metrics",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Apply rate limiting."""
        # Skip rate limiting for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        # Get client identifier
        client_id = self._get_client_identifier(request)
        
        # Check rate limit
        try:
            if await self._is_rate_limited(client_id):
                # Log rate limit violation
                log_security_event(
                    event_type="rate_limit_exceeded",
                    client_ip=self._get_client_ip(request),
                    path=request.url.path,
                    method=request.method,
                )
                
                return JSONResponse(
                    status_code=429,
                    content={
                        "error": {
                            "code": "RATE_LIMIT_EXCEEDED",
                            "message": "Too many requests. Please try again later.",
                            "retry_after": self.rate_limit_period,
                        }
                    },
                    headers={
                        "Retry-After": str(self.rate_limit_period),
                        "X-RateLimit-Limit": str(self.rate_limit_requests),
                        "X-RateLimit-Remaining": "0",
                        "X-RateLimit-Reset": str(int(time.time()) + self.rate_limit_period),
                    }
                )
        except Exception as e:
            # If rate limiting fails, log error but don't block request
            logger.error("Rate limiting check failed", error=str(e), client_id=client_id)
        
        # Process request
        response = await call_next(request)
        
        # Add rate limit headers to response
        try:
            remaining = await self._get_remaining_requests(client_id)
            response.headers["X-RateLimit-Limit"] = str(self.rate_limit_requests)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(int(time.time()) + self.rate_limit_period)
        except Exception as e:
            logger.error("Failed to add rate limit headers", error=str(e))
        
        return response
    
    def _get_client_identifier(self, request: Request) -> str:
        """Get unique client identifier for rate limiting."""
        # Try to get user ID from request state (set by auth middleware)
        user_id = getattr(request.state, "user_id", None)
        if user_id:
            return f"user:{user_id}"
        
        # Fall back to IP address
        client_ip = self._get_client_ip(request)
        return f"ip:{client_ip}"
    
    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host if request.client else "unknown"
    
    async def _is_rate_limited(self, client_id: str) -> bool:
        """Check if client is rate limited."""
        try:
            redis_manager = get_redis_manager()
            
            # Rate limit key
            key = f"rate_limit:{client_id}"
            
            # Get current count
            current_count = await redis_manager.get(key, deserialize=False)
            current_count = int(current_count) if current_count else 0
            
            # Check if over limit
            if current_count >= self.rate_limit_requests:
                return True
            
            # Increment counter
            await redis_manager.increment(key, 1)
            
            # Set TTL on first request
            if current_count == 0:
                await redis_manager.expire(key, self.rate_limit_period)
            
            return False
            
        except Exception as e:
            logger.error("Rate limit check failed", error=str(e), client_id=client_id)
            return False
    
    async def _get_remaining_requests(self, client_id: str) -> int:
        """Get remaining requests for client."""
        try:
            redis_manager = get_redis_manager()
            key = f"rate_limit:{client_id}"
            
            current_count = await redis_manager.get(key, deserialize=False)
            current_count = int(current_count) if current_count else 0
            
            remaining = max(0, self.rate_limit_requests - current_count)
            return remaining
            
        except Exception as e:
            logger.error("Failed to get remaining requests", error=str(e), client_id=client_id)
            return self.rate_limit_requests


class AuthenticationMiddleware(BaseHTTPMiddleware):
    """
    Middleware for JWT authentication.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.public_paths = {
            "/",
            "/docs",
            "/redoc",
            "/openapi.json",
            "/health/live",
            "/health/ready",
            "/health/startup",
            "/metrics",
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/refresh",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
        }
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Authenticate requests."""
        # Skip authentication for public paths
        if request.url.path in self.public_paths:
            return await call_next(request)
        
        # Get authorization header
        authorization = request.headers.get("authorization")
        
        if not authorization:
            return self._unauthorized_response("Missing authorization header")
        
        # Extract token
        try:
            scheme, token = authorization.split(" ", 1)
            if scheme.lower() != "bearer":
                return self._unauthorized_response("Invalid authorization scheme")
        except ValueError:
            return self._unauthorized_response("Invalid authorization header format")
        
        # Validate token
        try:
            user_data = await self._validate_token(token)
            if not user_data:
                return self._unauthorized_response("Invalid or expired token")
            
            # Add user data to request state
            request.state.user_id = user_data.get("user_id")
            request.state.user_email = user_data.get("email")
            request.state.user_role = user_data.get("role", "user")
            request.state.is_premium = user_data.get("is_premium", False)
            
        except Exception as e:
            logger.error("Token validation failed", error=str(e), token=token[:10] + "...")
            return self._unauthorized_response("Token validation failed")
        
        return await call_next(request)
    
    def _unauthorized_response(self, message: str) -> JSONResponse:
        """Return unauthorized response."""
        return JSONResponse(
            status_code=401,
            content={
                "error": {
                    "code": "UNAUTHORIZED",
                    "message": message,
                }
            }
        )
    
    async def _validate_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token using Supabase.
        
        Args:
            token: JWT token
            
        Returns:
            Dict[str, Any]: User data if valid
        """
        try:
            from app.shared.config.supabase import get_supabase_auth
            
            # Get Supabase auth client
            auth_client = get_supabase_auth()
            
            # Verify token
            user = auth_client.get_user(token)
            
            if not user or not user.user:
                return None
            
            # Get user profile data
            from app.shared.config.supabase import get_supabase_client
            supabase = get_supabase_client()
            
            profile_result = supabase.table("profiles").select("*").eq("user_id", user.user.id).single().execute()
            profile_data = profile_result.data if profile_result.data else {}
            
            # Get subscription data
            subscription_result = supabase.table("subscriptions").select("*").eq("user_id", user.user.id).single().execute()
            subscription_data = subscription_result.data if subscription_result.data else {}
            
            return {
                "user_id": user.user.id,
                "email": user.user.email,
                "role": user.user.user_metadata.get("role", "user"),
                "is_premium": subscription_data.get("status") == "active",
                "subscription_tier": subscription_data.get("plan_type", "free"),
                "profile": profile_data,
            }
            
        except Exception as e:
            logger.error("Token validation error", error=str(e))
            return None


class CORSMiddleware(BaseHTTPMiddleware):
    """
    Custom CORS middleware with additional Plant Care specific headers.
    """
    
    def __init__(self, app: ASGIApp):
        super().__init__(app)
        self.allowed_origins = settings.cors_origins_list
        self.allowed_methods = settings.CORS_ALLOW_METHODS.split(",")
        self.allowed_headers = ["*"] if settings.CORS_ALLOW_HEADERS == "*" else settings.CORS_ALLOW_HEADERS.split(",")
        self.allow_credentials = settings.CORS_ALLOW_CREDENTIALS
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """Handle CORS headers."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            response = Response()
            self._add_cors_headers(response, origin)
            return response
        
        # Process request
        response = await call_next(request)
        
        # Add CORS headers
        self._add_cors_headers(response, origin)
        
        return response
    
    def _add_cors_headers(self, response: Response, origin: str) -> None:
        """Add CORS headers to response."""
        # Check if origin is allowed
        if origin and (
            "*" in self.allowed_origins or 
            origin in self.allowed_origins or
            self._is_origin_allowed(origin)
        ):
            response.headers["Access-Control-Allow-Origin"] = origin
        elif "*" in self.allowed_origins:
            response.headers["Access-Control-Allow-Origin"] = "*"
        
        # Add other CORS headers
        response.headers["Access-Control-Allow-Methods"] = ", ".join(self.allowed_methods)
        response.headers["Access-Control-Allow-Headers"] = ", ".join(self.allowed_headers)
        
        if self.allow_credentials:
            response.headers["Access-Control-Allow-Credentials"] = "true"
        
        # Add custom headers
        response.headers["Access-Control-Expose-Headers"] = "X-Request-ID, X-Process-Time, X-RateLimit-Limit, X-RateLimit-Remaining"
    
    def _is_origin_allowed(self, origin: str) -> bool:
        """Check if origin is allowed based on patterns."""
        # Add custom logic for dynamic origin checking
        # For example, allow localhost with any port in development
        if settings.is_development and origin.startswith("http://localhost:"):
            return True
        
        return False


def setup_cors_middleware(app) -> None:
    """
    Setup CORS middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.cors import CORSMiddleware as FastAPICORSMiddleware
    from app.shared.config.settings import get_settings
    
    settings = get_settings()
    
    app.add_middleware(
        FastAPICORSMiddleware,
        allow_origins=settings.CORS_ORIGINS.split(",") if settings.CORS_ORIGINS != "*" else ["*"],
        allow_credentials=settings.CORS_ALLOW_CREDENTIALS,
        allow_methods=settings.CORS_ALLOW_METHODS.split(","),
        allow_headers=settings.CORS_ALLOW_HEADERS.split(",") if settings.CORS_ALLOW_HEADERS != "*" else ["*"],
    )

def setup_security_middleware(app) -> None:
    """
    Setup security middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(SecurityHeadersMiddleware)

def setup_request_middleware(app) -> None:
    """
    Setup request processing middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(ProcessTimeMiddleware)
    app.add_middleware(RequestLoggingMiddleware)

def setup_rate_limit_middleware(app) -> None:
    """
    Setup rate limiting middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RateLimitMiddleware)

def setup_authentication_middleware(app) -> None:
    """
    Setup authentication middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(AuthenticationMiddleware)

def setup_all_middleware(app) -> None:
    """
    Setup all middleware for the Plant Care Application in the correct order.
    
    Args:
        app: FastAPI application instance
    """
    # Order matters! Add in reverse order of execution
    setup_cors_middleware(app)
    setup_security_middleware(app)
    setup_rate_limit_middleware(app)
    setup_authentication_middleware(app)
    setup_request_middleware(app)

# Add these additional missing functions to your app/shared/core/middleware.py file
# (Add these AFTER the functions from the previous artifact)

def setup_logging_middleware(app) -> None:
    """
    Setup logging middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RequestLoggingMiddleware)

def setup_compression_middleware(app) -> None:
    """
    Setup compression middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.gzip import GZipMiddleware
    app.add_middleware(GZipMiddleware, minimum_size=1000)

def setup_trusted_host_middleware(app) -> None:
    """
    Setup trusted host middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    from fastapi.middleware.trustedhost import TrustedHostMiddleware
    from app.shared.config.settings import get_settings
    
    settings = get_settings()
    
    # In production, add specific trusted hosts
    if settings.APP_ENV == "production":
        trusted_hosts = ["plantcare.app", "api.plantcare.app", "*.plantcare.app"]
    else:
        # In development, allow localhost and common dev hosts
        trusted_hosts = ["localhost", "127.0.0.1", "*.ngrok.io", "*.localhost"]
    
    app.add_middleware(TrustedHostMiddleware, allowed_hosts=trusted_hosts)

def setup_error_handling_middleware(app) -> None:
    """
    Setup error handling middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    # Note: Error handling is typically done via exception handlers, not middleware
    # But if you have a custom error handling middleware class, add it here
    pass

def setup_plant_care_middleware(app) -> None:
    """
    Setup Plant Care specific middleware.
    
    Args:
        app: FastAPI application instance
    """
    # Add any Plant Care specific middleware here
    # For example, plant data enrichment, care reminders, etc.
    pass

def setup_production_middleware(app) -> None:
    """
    Setup production-specific middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    from app.shared.config.settings import get_settings
    
    settings = get_settings()
    
    if settings.APP_ENV == "production":
        setup_trusted_host_middleware(app)
        setup_compression_middleware(app)
        # Add other production-specific middleware

def setup_development_middleware(app) -> None:
    """
    Setup development-specific middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    from app.shared.config.settings import get_settings
    
    settings = get_settings()
    
    if settings.APP_ENV == "development":
        # Add development-specific middleware
        # For example, request timing, debug headers, etc.
        pass

# Update the complete setup function to include logging
def setup_all_middleware(app) -> None:
    """
    Setup all middleware for the Plant Care Application in the correct order.
    
    Args:
        app: FastAPI application instance
    """
    from app.shared.config.settings import get_settings
    
    settings = get_settings()
    
    # Order matters! Add in reverse order of execution
    # 1. CORS (must be first for preflight requests)
    setup_cors_middleware(app)
    
    # 2. Security headers
    setup_security_middleware(app)
    
    # 3. Trusted hosts (production)
    if settings.APP_ENV == "production":
        setup_trusted_host_middleware(app)
    
    # 4. Compression
    setup_compression_middleware(app)
    
    # 5. Rate limiting
    setup_rate_limit_middleware(app)
    
    # 6. Authentication
    setup_authentication_middleware(app)
    
    # 7. Logging (should be near the end to catch all requests)
    setup_logging_middleware(app)
    
    # 8. Request processing (process time, etc.)
    setup_request_middleware(app)
    
    # 9. Plant Care specific middleware
    setup_plant_care_middleware(app)
    
    # 10. Environment specific middleware
    if settings.APP_ENV == "production":
        setup_production_middleware(app)
    elif settings.APP_ENV == "development":
        setup_development_middleware(app)

# Add this function to your app/shared/core/middleware.py file
# (This provides the exact function name that your __init__.py is looking for)

def setup_rate_limiting_middleware(app) -> None:
    """
    Setup rate limiting middleware for the Plant Care Application.
    (Alternative name for setup_rate_limit_middleware to match imports)
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(RateLimitMiddleware)

# Also add any other missing function names that might be imported
def setup_authentication_middleware_v2(app) -> None:
    """
    Alternative authentication middleware setup.
    
    Args:
        app: FastAPI application instance
    """
    app.add_middleware(AuthenticationMiddleware)

def setup_error_middleware(app) -> None:
    """
    Setup error handling middleware.
    
    Args:
        app: FastAPI application instance
    """
    # Error handling is typically done via exception handlers
    # But add any custom error middleware here if needed
    pass

def setup_monitoring_middleware(app) -> None:
    """
    Setup monitoring and metrics middleware.
    
    Args:
        app: FastAPI application instance
    """
    # Add monitoring middleware like Prometheus metrics, etc.
    pass

def setup_caching_middleware(app) -> None:
    """
    Setup caching middleware for the Plant Care Application.
    
    Args:
        app: FastAPI application instance
    """
    # Add caching middleware if needed
    pass

# Update the __all__ list to include all possible function names
__all__ = [
    "SecurityHeadersMiddleware",
    "ProcessTimeMiddleware", 
    "RequestLoggingMiddleware",
    "RateLimitMiddleware",
    "AuthenticationMiddleware",
    "CORSMiddleware",
    "setup_cors_middleware",
    "setup_security_middleware", 
    "setup_request_middleware",
    "setup_rate_limit_middleware",
    "setup_rate_limiting_middleware",  # Add this line
    "setup_authentication_middleware",
    "setup_authentication_middleware_v2",
    "setup_logging_middleware",
    "setup_compression_middleware",
    "setup_trusted_host_middleware",
    "setup_error_handling_middleware",
    "setup_error_middleware",
    "setup_monitoring_middleware",
    "setup_caching_middleware",
    "setup_plant_care_middleware",
    "setup_production_middleware",
    "setup_development_middleware",
    "setup_all_middleware",
]
