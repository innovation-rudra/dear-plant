"""
app/api/middleware/error_handling.py
Plant Care Application - Error Handling Middleware

Comprehensive error handling middleware for Plant Care API:
- Structured error responses
- Plant Care specific error codes
- Security-focused error handling
- Monitoring and alerting integration
- User-friendly error messages
"""
import traceback
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import ValidationError
from sqlalchemy.exc import SQLAlchemyError
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    PlantCareException,
    AuthenticationError,
    AuthorizationError,
    ValidationError as PlantCareValidationError,
    ResourceNotFoundError,
    RateLimitExceededError
)
from app.shared.utils.formatters import format_error_response
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class ErrorHandlingMiddleware:
    """
    Error handling middleware for Plant Care Application.
    
    Provides centralized error handling with:
    - Consistent error response format
    - Plant Care specific error codes
    - Security-focused error messages
    - Monitoring integration
    - Development vs production error details
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
        # Plant Care specific error mappings
        self.error_mappings = {
            # Authentication errors
            AuthenticationError: {
                "status_code": status.HTTP_401_UNAUTHORIZED,
                "error_code": "AUTHENTICATION_ERROR",
                "user_message": "Authentication failed. Please log in again."
            },
            AuthorizationError: {
                "status_code": status.HTTP_403_FORBIDDEN,
                "error_code": "AUTHORIZATION_ERROR", 
                "user_message": "You don't have permission to access this resource."
            },
            
            # Validation errors
            PlantCareValidationError: {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "VALIDATION_ERROR",
                "user_message": "The provided data is invalid."
            },
            RequestValidationError: {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "REQUEST_VALIDATION_ERROR",
                "user_message": "Invalid request format or missing required fields."
            },
            ValidationError: {
                "status_code": status.HTTP_422_UNPROCESSABLE_ENTITY,
                "error_code": "PYDANTIC_VALIDATION_ERROR",
                "user_message": "Data validation failed."
            },
            
            # Resource errors
            ResourceNotFoundError: {
                "status_code": status.HTTP_404_NOT_FOUND,
                "error_code": "RESOURCE_NOT_FOUND",
                "user_message": "The requested resource was not found."
            },
            
            # Rate limiting
            RateLimitExceededError: {
                "status_code": status.HTTP_429_TOO_MANY_REQUESTS,
                "error_code": "RATE_LIMIT_EXCEEDED",
                "user_message": "Too many requests. Please try again later."
            },
            
            # Database errors
            SQLAlchemyError: {
                "status_code": status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error_code": "DATABASE_ERROR",
                "user_message": "A database error occurred. Please try again."
            }
        }
        
        # Plant Care specific error codes
        self.plant_care_error_codes = {
            "PLANT_NOT_FOUND": "The specified plant was not found in your collection.",
            "CARE_TASK_NOT_FOUND": "The care task was not found or has been removed.",
            "INVALID_PLANT_DATA": "The plant information provided is invalid.",
            "CARE_SCHEDULE_CONFLICT": "This care schedule conflicts with existing schedules.",
            "PHOTO_UPLOAD_FAILED": "Failed to upload plant photo. Please try again.",
            "AI_SERVICE_UNAVAILABLE": "AI service is temporarily unavailable.",
            "PLANT_IDENTIFICATION_FAILED": "Unable to identify the plant from the provided image.",
            "PREMIUM_FEATURE_REQUIRED": "This feature requires a premium subscription.",
            "PLANT_LIMIT_EXCEEDED": "You've reached your plant limit. Upgrade to add more plants.",
            "INVALID_CARE_FREQUENCY": "The specified care frequency is not valid.",
            "HEALTH_RECORD_NOT_FOUND": "Health record not found for this plant.",
            "COMMUNITY_POST_NOT_FOUND": "The community post was not found or has been removed.",
            "EXPERT_NOT_AVAILABLE": "No experts are currently available for consultation.",
            "WEATHER_SERVICE_ERROR": "Weather service is temporarily unavailable.",
            "NOTIFICATION_DELIVERY_FAILED": "Failed to deliver notification."
        }
        
        # Sensitive information that should not be exposed
        self.sensitive_patterns = [
            "password",
            "token",
            "secret",
            "key",
            "credential",
            "authorization"
        ]
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process error handling for requests."""
        try:
            response = await call_next(request)
            return response
            
        except HTTPException as e:
            return self._handle_http_exception(e, request)
            
        except PlantCareException as e:
            return self._handle_plant_care_exception(e, request)
            
        except RequestValidationError as e:
            return self._handle_validation_error(e, request)
            
        except ValidationError as e:
            return self._handle_pydantic_validation_error(e, request)
            
        except SQLAlchemyError as e:
            return self._handle_database_error(e, request)
            
        except Exception as e:
            return self._handle_unexpected_error(e, request)
    
    def _handle_http_exception(self, exc: HTTPException, request: Request) -> JSONResponse:
        """Handle FastAPI HTTP exceptions."""
        try:
            # Extract request context
            request_context = self._get_request_context(request)
            
            # Log the error
            logger.warning(
                "HTTP exception occurred",
                status_code=exc.status_code,
                detail=exc.detail,
                **request_context
            )
            
            # Handle specific Plant Care error codes
            error_code = getattr(exc, 'error_code', None)
            if error_code and error_code in self.plant_care_error_codes:
                user_message = self.plant_care_error_codes[error_code]
            else:
                user_message = str(exc.detail) if exc.detail else "An error occurred"
            
            return JSONResponse(
                status_code=exc.status_code,
                content=format_error_response(
                    error_code=error_code or f"HTTP_{exc.status_code}",
                    message=user_message,
                    status_code=exc.status_code
                )
            )
            
        except Exception as e:
            logger.error("Error handling HTTP exception", error=str(e))
            return self._create_fallback_error_response()
    
    def _handle_plant_care_exception(self, exc: PlantCareException, request: Request) -> JSONResponse:
        """Handle Plant Care specific exceptions."""
        try:
            request_context = self._get_request_context(request)
            
            # Get error mapping
            error_mapping = self.error_mappings.get(type(exc), {
                "status_code": exc.status_code or status.HTTP_500_INTERNAL_SERVER_ERROR,
                "error_code": exc.error_code or "PLANT_CARE_ERROR",
                "user_message": str(exc.message) if hasattr(exc, 'message') else str(exc)
            })
            
            # Log the error with appropriate level
            if error_mapping["status_code"] >= 500:
                logger.error(
                    "Plant Care exception occurred",
                    error_code=error_mapping["error_code"],
                    message=str(exc),
                    **request_context
                )
            else:
                logger.warning(
                    "Plant Care exception occurred",
                    error_code=error_mapping["error_code"],
                    message=str(exc),
                    **request_context
                )
            
            # Log security events for auth/authz errors
            if isinstance(exc, (AuthenticationError, AuthorizationError)):
                log_security_event(
                    event_type="security_exception",
                    error_type=type(exc).__name__,
                    error_message=str(exc),
                    user_id=request_context.get("user_id"),
                    ip_address=request_context.get("client_ip"),
                    path=request_context.get("path")
                )
            
            return JSONResponse(
                status_code=error_mapping["status_code"],
                content=format_error_response(
                    error_code=error_mapping["error_code"],
                    message=error_mapping["user_message"],
                    details=self._get_error_details(exc),
                    status_code=error_mapping["status_code"]
                )
            )
            
        except Exception as e:
            logger.error("Error handling Plant Care exception", error=str(e))
            return self._create_fallback_error_response()
    
    def _handle_validation_error(self, exc: RequestValidationError, request: Request) -> JSONResponse:
        """Handle FastAPI request validation errors."""
        try:
            request_context = self._get_request_context(request)
            
            # Extract validation error details
            error_details = []
            for error in exc.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append({
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"],
                    "value": error.get("input")
                })
            
            logger.warning(
                "Request validation error",
                error_count=len(error_details),
                errors=error_details,
                **request_context
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=format_error_response(
                    error_code="VALIDATION_ERROR",
                    message="Request validation failed",
                    details={"validation_errors": error_details},
                    status_code=422
                )
            )
            
        except Exception as e:
            logger.error("Error handling validation error", error=str(e))
            return self._create_fallback_error_response()
    
    def _handle_pydantic_validation_error(self, exc: ValidationError, request: Request) -> JSONResponse:
        """Handle Pydantic validation errors."""
        try:
            request_context = self._get_request_context(request)
            
            # Extract Pydantic error details
            error_details = []
            for error in exc.errors():
                field_path = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append({
                    "field": field_path,
                    "message": error["msg"],
                    "type": error["type"]
                })
            
            logger.warning(
                "Pydantic validation error",
                error_count=len(error_details),
                errors=error_details,
                **request_context
            )
            
            return JSONResponse(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                content=format_error_response(
                    error_code="PYDANTIC_VALIDATION_ERROR",
                    message="Data validation failed",
                    details={"validation_errors": error_details},
                    status_code=422
                )
            )
            
        except Exception as e:
            logger.error("Error handling Pydantic validation error", error=str(e))
            return self._create_fallback_error_response()
    
    def _handle_database_error(self, exc: SQLAlchemyError, request: Request) -> JSONResponse:
        """Handle database errors."""
        try:
            request_context = self._get_request_context(request)
            
            # Log database error with full details for debugging
            logger.error(
                "Database error occurred",
                error_type=type(exc).__name__,
                error_message=str(exc),
                **request_context
            )
            
            # Don't expose database details to users in production
            if settings.ENVIRONMENT == "development":
                error_message = f"Database error: {str(exc)}"
            else:
                error_message = "A database error occurred. Please try again."
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=format_error_response(
                    error_code="DATABASE_ERROR",
                    message=error_message,
                    status_code=500
                )
            )
            
        except Exception as e:
            logger.error("Error handling database error", error=str(e))
            return self._create_fallback_error_response()
    
    def _handle_unexpected_error(self, exc: Exception, request: Request) -> JSONResponse:
        """Handle unexpected errors."""
        try:
            request_context = self._get_request_context(request)
            
            # Log unexpected error with full traceback
            logger.error(
                "Unexpected error occurred",
                error_type=type(exc).__name__,
                error_message=str(exc),
                traceback=traceback.format_exc() if settings.ENVIRONMENT == "development" else None,
                **request_context
            )
            
            # Send alert for unexpected errors in production
            if settings.ENVIRONMENT == "production":
                self._send_error_alert(exc, request_context)
            
            # Don't expose internal error details in production
            if settings.ENVIRONMENT == "development":
                error_message = f"Unexpected error: {str(exc)}"
                error_details = {"traceback": traceback.format_exc()}
            else:
                error_message = "An unexpected error occurred. Please try again."
                error_details = None
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=format_error_response(
                    error_code="INTERNAL_SERVER_ERROR",
                    message=error_message,
                    details=error_details,
                    status_code=500
                )
            )
            
        except Exception as e:
            logger.error("Error handling unexpected error", error=str(e))
            return self._create_fallback_error_response()
    
    def _get_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract context information from request."""
        context = {
            "path": request.url.path,
            "method": request.method,
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent"),
            "request_id": getattr(request.state, "request_id", None)
        }
        
        # Add user context if available
        user = getattr(request.state, "user", None)
        if user:
            context.update({
                "user_id": user.get("user_id"),
                "user_role": user.get("role")
            })
        
        return context
    
    def _get_client_ip(self, request: Request) -> str:
        """Get the real client IP address."""
        forwarded_for = request.headers.get("x-forwarded-for")
        if forwarded_for:
            return forwarded_for.split(",")[0].strip()
        
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            return real_ip
        
        return request.client.host
    
    def _get_error_details(self, exc: Exception) -> Optional[Dict[str, Any]]:
        """Get error details for response (filtered for security)."""
        if settings.ENVIRONMENT != "development":
            return None
        
        details = {}
        
        # Add exception details for development
        if hasattr(exc, 'details'):
            details.update(exc.details)
        
        # Filter out sensitive information
        filtered_details = {}
        for key, value in details.items():
            key_lower = key.lower()
            if not any(pattern in key_lower for pattern in self.sensitive_patterns):
                filtered_details[key] = value
        
        return filtered_details if filtered_details else None
    
    def _send_error_alert(self, exc: Exception, context: Dict[str, Any]):
        """Send alert for critical errors (integrate with monitoring)."""
        try:
            # This would integrate with your alerting system (PagerDuty, Slack, etc.)
            alert_data = {
                "error_type": type(exc).__name__,
                "error_message": str(exc),
                "context": context,
                "environment": settings.ENVIRONMENT,
                "service": "plant-care-api"
            }
            
            # For now, just log the alert
            logger.error("ALERT: Critical error occurred", **alert_data)
            
            # In production, this would send to monitoring systems:
            # - Sentry for error tracking
            # - PagerDuty for alerting
            # - Slack for team notifications
            
        except Exception as e:
            logger.error("Failed to send error alert", error=str(e))
    
    def _create_fallback_error_response(self) -> JSONResponse:
        """Create a fallback error response when error handling fails."""
        return JSONResponse(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            content={
                "success": False,
                "status_code": 500,
                "error": {
                    "code": "CRITICAL_ERROR",
                    "message": "A critical error occurred in the error handling system",
                    "details": {}
                },
                "timestamp": "2024-07-19T12:00:00Z",
                "api_version": "v1"
            }
        )
    
    def get_middleware_status(self) -> Dict[str, Any]:
        """Get error handling middleware status."""
        return {
            "name": "ErrorHandlingMiddleware",
            "enabled": True,
            "error_mappings_count": len(self.error_mappings),
            "plant_care_error_codes_count": len(self.plant_care_error_codes),
            "environment": settings.ENVIRONMENT,
            "include_stack_trace": settings.ENVIRONMENT == "development"
        }


# Standalone error handling functions
def create_plant_care_error_response(
    error_code: str,
    message: str,
    status_code: int = 400,
    details: Optional[Dict[str, Any]] = None
) -> JSONResponse:
    """Create a standardized Plant Care error response."""
    return JSONResponse(
        status_code=status_code,
        content=format_error_response(
            error_code=error_code,
            message=message,
            details=details,
            status_code=status_code
        )
    )


def handle_plant_not_found(plant_id: str) -> JSONResponse:
    """Handle plant not found error."""
    return create_plant_care_error_response(
        error_code="PLANT_NOT_FOUND",
        message=f"Plant with ID '{plant_id}' was not found in your collection",
        status_code=404,
        details={"plant_id": plant_id}
    )


def handle_care_task_not_found(task_id: str) -> JSONResponse:
    """Handle care task not found error."""
    return create_plant_care_error_response(
        error_code="CARE_TASK_NOT_FOUND",
        message=f"Care task with ID '{task_id}' was not found",
        status_code=404,
        details={"task_id": task_id}
    )


def handle_premium_required() -> JSONResponse:
    """Handle premium feature required error."""
    return create_plant_care_error_response(
        error_code="PREMIUM_FEATURE_REQUIRED",
        message="This feature requires a premium subscription",
        status_code=402,
        details={"upgrade_url": "https://plantcare.app/upgrade"}
    )


def handle_plant_limit_exceeded() -> JSONResponse:
    """Handle plant limit exceeded error."""
    return create_plant_care_error_response(
        error_code="PLANT_LIMIT_EXCEEDED",
        message="You've reached your plant limit. Upgrade to add more plants.",
        status_code=403,
        details={"upgrade_url": "https://plantcare.app/upgrade"}
    )