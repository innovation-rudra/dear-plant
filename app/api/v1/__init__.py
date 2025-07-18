"""
app/api/v1/__init__.py
Plant Care Application - API V1 Package

Version 1 of the Plant Care API providing stable endpoints for:
- Plant management and identification
- Care scheduling and task management  
- Health monitoring and diagnosis
- Growth tracking and analytics
- Community features and social interactions
- AI-powered assistance and recommendations
"""

from app.api.v1.router import api_router
from app.api.v1.health import health_router
from app.api.v1.admin import admin_router

__version__ = "1.0.0"
__api_version__ = "v1"

__all__ = [
    "api_router",
    "health_router", 
    "admin_router",
]

# API V1 Configuration
API_V1_CONFIG = {
    "version": __version__,
    "api_version": __api_version__,
    "prefix": "/api/v1",
    "title": "Plant Care API v1",
    "description": """
    # Plant Care API v1
    
    Comprehensive API for plant care management with the following features:
    
    ## 🌱 Core Features
    - **Plant Management**: Add, update, track your plant collection
    - **Care Scheduling**: Automated reminders for watering, fertilizing, etc.
    - **Health Monitoring**: AI-powered diagnosis and treatment recommendations
    - **Growth Tracking**: Photo journaling and milestone tracking
    
    ## 🤖 AI Features
    - **Plant Identification**: Identify plants from photos
    - **AI Chat Assistant**: Get personalized plant care advice
    - **Smart Recommendations**: Automated care suggestions
    
    ## 👥 Social Features
    - **Community**: Share plants and experiences
    - **Expert Advice**: Connect with plant care experts
    - **Plant Collections**: Showcase your plant journey
    
    ## 📱 Mobile Integration
    - **Push Notifications**: Care reminders and alerts
    - **Offline Support**: Core features work offline
    - **Photo Upload**: High-quality plant photography
    
    ## 🔒 Authentication
    All endpoints (except public ones) require authentication via:
    - **Bearer Token**: Include JWT token in Authorization header
    - **API Key**: Use X-API-Key header for service integrations
    
    ## 📊 Rate Limiting
    - **Free Users**: 100 requests/hour, 10/minute burst
    - **Premium Users**: 500 requests/hour, 50/minute burst
    - **API Keys**: Custom limits based on plan
    
    ## 🌍 Internationalization  
    - **Languages**: English, Spanish, French, German, Japanese
    - **Units**: Metric and Imperial support
    - **Timezones**: Automatic timezone detection
    """,
    "contact": {
        "name": "Plant Care API Support",
        "email": "api-support@plantcare.app",
        "url": "https://plantcare.app/support"
    },
    "license": {
        "name": "MIT",
        "url": "https://opensource.org/licenses/MIT"
    },
    "servers": [
        {
            "url": "https://api.plantcare.app/api/v1",
            "description": "Production server"
        },
        {
            "url": "https://staging-api.plantcare.app/api/v1", 
            "description": "Staging server"
        },
        {
            "url": "http://localhost:8000/api/v1",
            "description": "Development server"
        }
    ]
}

# Module endpoint mappings
MODULE_ENDPOINTS = {
    "user_management": "/users",
    "plant_management": "/plants", 
    "care_management": "/care",
    "health_monitoring": "/health",
    "growth_tracking": "/growth",
    "community_social": "/community",
    "ai_smart_features": "/ai",
    "weather_environmental": "/weather", 
    "analytics_insights": "/analytics",
    "notification_communication": "/notifications",
    "payment_subscription": "/payments",
    "content_management": "/content"
}

# Response schemas for consistent API responses
RESPONSE_SCHEMAS = {
    "success": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "status_code": {"type": "integer", "example": 200},
            "message": {"type": "string", "example": "Operation completed successfully"},
            "data": {"type": "object"},
            "timestamp": {"type": "string", "format": "date-time"},
            "api_version": {"type": "string", "example": "v1"}
        }
    },
    "error": {
        "type": "object", 
        "properties": {
            "success": {"type": "boolean", "example": False},
            "status_code": {"type": "integer", "example": 400},
            "error": {
                "type": "object",
                "properties": {
                    "code": {"type": "string", "example": "VALIDATION_ERROR"},
                    "message": {"type": "string", "example": "Invalid input data"},
                    "details": {"type": "object"}
                }
            },
            "timestamp": {"type": "string", "format": "date-time"},
            "api_version": {"type": "string", "example": "v1"}
        }
    },
    "paginated": {
        "type": "object",
        "properties": {
            "success": {"type": "boolean", "example": True},
            "status_code": {"type": "integer", "example": 200},
            "message": {"type": "string", "example": "Data retrieved successfully"},
            "data": {"type": "array"},
            "metadata": {
                "type": "object",
                "properties": {
                    "pagination": {
                        "type": "object",
                        "properties": {
                            "total_items": {"type": "integer", "example": 150},
                            "current_page": {"type": "integer", "example": 1},
                            "page_size": {"type": "integer", "example": 20},
                            "total_pages": {"type": "integer", "example": 8},
                            "has_next_page": {"type": "boolean", "example": True},
                            "has_previous_page": {"type": "boolean", "example": False}
                        }
                    }
                }
            },
            "timestamp": {"type": "string", "format": "date-time"},
            "api_version": {"type": "string", "example": "v1"}
        }
    }
}

# Security schemes for OpenAPI documentation
SECURITY_SCHEMES = {
    "BearerAuth": {
        "type": "http",
        "scheme": "bearer",
        "bearerFormat": "JWT",
        "description": "JWT token from Supabase authentication"
    },
    "ApiKeyAuth": {
        "type": "apiKey",
        "in": "header", 
        "name": "X-API-Key",
        "description": "API key for service integrations"
    }
}

# Common HTTP status codes and their meanings in Plant Care context
HTTP_STATUS_CODES = {
    200: "Success - Operation completed successfully",
    201: "Created - Resource created (plant, care task, etc.)",
    202: "Accepted - Request accepted for processing (AI analysis, etc.)",
    204: "No Content - Operation successful, no data returned",
    400: "Bad Request - Invalid input data or parameters",
    401: "Unauthorized - Authentication required or token invalid",
    402: "Payment Required - Premium feature requires subscription",
    403: "Forbidden - Insufficient permissions or feature not available",
    404: "Not Found - Plant, task, or resource not found",
    409: "Conflict - Resource already exists or conflicting operation",
    422: "Unprocessable Entity - Validation errors in request data",
    429: "Too Many Requests - Rate limit exceeded",
    500: "Internal Server Error - Unexpected server error",
    502: "Bad Gateway - External service unavailable (Plant ID API, etc.)",
    503: "Service Unavailable - Temporary service outage"
}