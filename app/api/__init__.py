"""
app/api/__init__.py
Plant Care Application - API Package Initialization

API layer for the Plant Care Application providing RESTful endpoints,
WebSocket connections, and middleware for plant care operations.
"""

from app.api.v1.router import api_router
from app.api.middleware.authentication import AuthenticationMiddleware
from app.api.middleware.rate_limiting import RateLimitingMiddleware
from app.api.middleware.logging import LoggingMiddleware
from app.api.middleware.cors import CORSMiddleware
from app.api.middleware.error_handling import ErrorHandlingMiddleware

__version__ = "1.0.0"

__all__ = [
    "api_router",
    "AuthenticationMiddleware",
    "RateLimitingMiddleware", 
    "LoggingMiddleware",
    "CORSMiddleware",
    "ErrorHandlingMiddleware",
]

# API Configuration
API_CONFIG = {
    "title": "Plant Care API",
    "description": "RESTful API for Plant Care Application - Manage plants, care schedules, health monitoring, and community features",
    "version": __version__,
    "prefix": "/api",
    "docs_url": "/docs",
    "redoc_url": "/redoc",
    "openapi_url": "/openapi.json",
    "include_in_schema": True,
    "tags_metadata": [
        {
            "name": "authentication",
            "description": "User authentication and authorization using Supabase Auth"
        },
        {
            "name": "plants",
            "description": "Plant management operations - CRUD, identification, collections"
        },
        {
            "name": "care",
            "description": "Care management - schedules, tasks, reminders, history"
        },
        {
            "name": "health",
            "description": "Plant health monitoring - diagnosis, treatments, alerts"
        },
        {
            "name": "growth",
            "description": "Growth tracking - photos, measurements, milestones, analytics"
        },
        {
            "name": "community",
            "description": "Social features - posts, comments, expert advice, sharing"
        },
        {
            "name": "ai",
            "description": "AI-powered features - chat assistant, recommendations, automation"
        },
        {
            "name": "weather",
            "description": "Weather integration - forecasts, alerts, care adjustments"
        },
        {
            "name": "analytics",
            "description": "Analytics and insights - performance metrics, trends, reports"
        },
        {
            "name": "notifications",
            "description": "Notification management - preferences, delivery, history"
        },
        {
            "name": "payments",
            "description": "Payment processing - subscriptions, billing, premium features"
        },
        {
            "name": "admin",
            "description": "Administrative operations - user management, system monitoring"
        },
        {
            "name": "health-check",
            "description": "System health and monitoring endpoints"
        }
    ]
}

# WebSocket Configuration
WEBSOCKET_CONFIG = {
    "path": "/ws",
    "allowed_origins": [
        "https://plantcare.app",
        "https://app.plantcare.app", 
        "http://localhost:3000",
        "http://localhost:8080"
    ],
    "max_connections": 1000,
    "heartbeat_interval": 30,
    "connection_timeout": 300
}

# Middleware Configuration
MIDDLEWARE_CONFIG = {
    "authentication": {
        "enabled": True,
        "exclude_paths": ["/health", "/docs", "/redoc", "/openapi.json"],
        "supabase_integration": True
    },
    "rate_limiting": {
        "enabled": True,
        "default_rate": "100/hour",
        "burst_rate": "10/minute",
        "premium_multiplier": 5
    },
    "cors": {
        "enabled": True,
        "allow_origins": [
            "https://plantcare.app",
            "https://app.plantcare.app",
            "http://localhost:3000"
        ],
        "allow_methods": ["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-Requested-With",
            "X-API-Key",
            "X-Device-ID",
            "X-App-Version"
        ],
        "expose_headers": ["X-Total-Count", "X-Rate-Limit-Remaining"],
        "allow_credentials": True,
        "max_age": 3600
    },
    "logging": {
        "enabled": True,
        "include_request_body": False,
        "include_response_body": False,
        "log_level": "INFO"
    },
    "error_handling": {
        "enabled": True,
        "include_stack_trace": False,
        "sentry_integration": True
    }
}