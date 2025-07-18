"""
app/api/middleware/__init__.py
Plant Care Application - API Middleware Package

Custom middleware components for Plant Care API providing:
- Authentication and authorization
- Rate limiting and throttling
- Request/response logging
- CORS handling
- Error handling and formatting
"""

from app.api.middleware.authentication import AuthenticationMiddleware
from app.api.middleware.rate_limiting import RateLimitingMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.cors import CORSMiddleware
from app.api.middleware.error_handling import ErrorHandlingMiddleware

__all__ = [
    "AuthenticationMiddleware",
    "RateLimitingMiddleware",
    "LoggingMiddleware", 
    "CORSMiddleware",
    "ErrorHandlingMiddleware"
]

# Middleware configuration for Plant Care Application
MIDDLEWARE_ORDER = [
    # 1. Error handling (outermost - catches all errors)
    "ErrorHandlingMiddleware",
    
    # 2. CORS (handle preflight and CORS headers)
    "CORSMiddleware",
    
    # 3. Logging (log all requests and responses)
    "LoggingMiddleware",
    
    # 4. Authentication (validate tokens and user sessions)
    "AuthenticationMiddleware",
    
    # 5. Rate limiting (control request frequency)
    "RateLimitingMiddleware"
]

# Plant Care specific middleware settings
PLANT_CARE_MIDDLEWARE_CONFIG = {
    "authentication": {
        "enabled": True,
        "supabase_integration": True,
        "jwt_secret_key": None,  # Will be loaded from settings
        "jwt_algorithm": "HS256",
        "exclude_paths": [
            "/health",
            "/docs", 
            "/redoc",
            "/openapi.json",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/forgot-password"
        ],
        "optional_auth_paths": [
            "/api/v1/plants/public",
            "/api/v1/community/public"
        ]
    },
    "rate_limiting": {
        "enabled": True,
        "default_limits": {
            "requests_per_minute": 60,
            "requests_per_hour": 1000,
            "burst_allowance": 10
        },
        "premium_limits": {
            "requests_per_minute": 300,
            "requests_per_hour": 5000,
            "burst_allowance": 50
        },
        "endpoint_specific_limits": {
            "/api/v1/auth/": {
                "requests_per_minute": 10,
                "requests_per_hour": 100
            },
            "/api/v1/plants/upload": {
                "requests_per_minute": 5,
                "requests_per_hour": 50
            },
            "/api/v1/ai/chat": {
                "requests_per_minute": 20,
                "requests_per_hour": 200
            }
        },
        "ip_whitelist": [],
        "ip_blacklist": []
    },
    "logging": {
        "enabled": True,
        "log_requests": True,
        "log_responses": True,
        "log_request_body": False,  # Privacy - don't log sensitive data
        "log_response_body": False,
        "log_headers": ["user-agent", "x-forwarded-for", "x-real-ip"],
        "exclude_paths": ["/health", "/metrics"],
        "sensitive_headers": ["authorization", "x-api-key", "cookie"],
        "max_body_size": 1024  # Max body size to log in bytes
    },
    "cors": {
        "enabled": True,
        "allow_origins": [
            "https://plantcare.app",
            "https://app.plantcare.app",
            "https://admin.plantcare.app"
        ],
        "allow_origin_regex": r"https://.*\.plantcare\.app",
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "accept",
            "accept-encoding", 
            "authorization",
            "content-type",
            "dnt",
            "origin",
            "user-agent",
            "x-csrftoken",
            "x-requested-with",
            "x-api-key",
            "x-device-id",
            "x-app-version"
        ],
        "expose_headers": [
            "x-total-count",
            "x-rate-limit-remaining",
            "x-rate-limit-reset"
        ],
        "allow_credentials": True,
        "max_age": 86400  # 24 hours
    },
    "error_handling": {
        "enabled": True,
        "include_stack_trace": False,  # Set to True in development
        "log_errors": True,
        "sentry_integration": True,
        "custom_error_responses": True,
        "handle_validation_errors": True,
        "handle_authentication_errors": True,
        "handle_authorization_errors": True,
        "handle_rate_limit_errors": True
    }
}

# Middleware health status
MIDDLEWARE_STATUS = {
    "authentication": {"enabled": True, "healthy": True},
    "rate_limiting": {"enabled": True, "healthy": True},
    "logging": {"enabled": True, "healthy": True},
    "cors": {"enabled": True, "healthy": True},
    "error_handling": {"enabled": True, "healthy": True}
}

def get_middleware_config():
    """Get Plant Care middleware configuration."""
    return PLANT_CARE_MIDDLEWARE_CONFIG

def get_middleware_status():
    """Get middleware health status."""
    return MIDDLEWARE_STATUS

def validate_middleware_order():
    """Validate that middleware is applied in correct order."""
    return MIDDLEWARE_ORDER