"""
Plant Care Application - Custom Exception Classes
"""
import uuid
from datetime import datetime
from typing import Any, Dict, Optional, Union

from fastapi import HTTPException, status


class PlantCareException(Exception):
    """
    Base exception class for Plant Care Application.
    """
    
    def __init__(
        self,
        message: str,
        error_code: str = "PLANT_CARE_ERROR",
        details: Optional[Dict[str, Any]] = None,
        status_code: int = status.HTTP_500_INTERNAL_SERVER_ERROR,
    ):
        """
        Initialize Plant Care exception.
        
        Args:
            message: Human-readable error message
            error_code: Machine-readable error code
            details: Additional error details
            status_code: HTTP status code
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.details = details or {}
        self.status_code = status_code
        self.timestamp = datetime.utcnow()
        self.error_id = str(uuid.uuid4())
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary."""
        return {
            "error_id": self.error_id,
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
            "timestamp": self.timestamp.isoformat(),
            "status_code": self.status_code,
        }
    
    def __str__(self) -> str:
        return f"{self.error_code}: {self.message}"


# Authentication & Authorization Exceptions
class AuthenticationError(PlantCareException):
    """Raised when authentication fails."""
    
    def __init__(self, message: str = "Authentication failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHENTICATION_ERROR",
            details=details,
            status_code=status.HTTP_401_UNAUTHORIZED,
        )


class AuthorizationError(PlantCareException):
    """Raised when authorization fails."""
    
    def __init__(self, message: str = "Authorization failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="AUTHORIZATION_ERROR",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


class TokenExpiredError(AuthenticationError):
    """Raised when JWT token is expired."""
    
    def __init__(self, message: str = "Token has expired", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "TOKEN_EXPIRED"


class InvalidTokenError(AuthenticationError):
    """Raised when JWT token is invalid."""
    
    def __init__(self, message: str = "Invalid token", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "INVALID_TOKEN"


class InsufficientPermissionsError(AuthorizationError):
    """Raised when user lacks required permissions."""
    
    def __init__(self, message: str = "Insufficient permissions", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "INSUFFICIENT_PERMISSIONS"


# Validation Exceptions
class ValidationError(PlantCareException):
    """Raised when validation fails."""
    
    def __init__(self, message: str = "Validation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="VALIDATION_ERROR",
            details=details,
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        )


class InvalidInputError(ValidationError):
    """Raised when input data is invalid."""
    
    def __init__(self, message: str = "Invalid input data", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "INVALID_INPUT"


class MissingRequiredFieldError(ValidationError):
    """Raised when required field is missing."""
    
    def __init__(self, field_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Required field '{field_name}' is missing"
        super().__init__(message=message, details=details)
        self.error_code = "MISSING_REQUIRED_FIELD"


class InvalidFieldValueError(ValidationError):
    """Raised when field value is invalid."""
    
    def __init__(self, field_name: str, value: Any, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid value for field '{field_name}': {value}"
        super().__init__(message=message, details=details)
        self.error_code = "INVALID_FIELD_VALUE"


# Resource Exceptions
class ResourceNotFoundError(PlantCareException):
    """Raised when requested resource is not found."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with ID '{resource_id}' not found"
        super().__init__(
            message=message,
            error_code="RESOURCE_NOT_FOUND",
            details=details,
            status_code=status.HTTP_404_NOT_FOUND,
        )


class ResourceAlreadyExistsError(PlantCareException):
    """Raised when resource already exists."""
    
    def __init__(self, resource_type: str, identifier: str, details: Optional[Dict[str, Any]] = None):
        message = f"{resource_type} with identifier '{identifier}' already exists"
        super().__init__(
            message=message,
            error_code="RESOURCE_ALREADY_EXISTS",
            details=details,
            status_code=status.HTTP_409_CONFLICT,
        )


class ResourceAccessDeniedError(PlantCareException):
    """Raised when access to resource is denied."""
    
    def __init__(self, resource_type: str, resource_id: str, details: Optional[Dict[str, Any]] = None):
        message = f"Access denied to {resource_type} with ID '{resource_id}'"
        super().__init__(
            message=message,
            error_code="RESOURCE_ACCESS_DENIED",
            details=details,
            status_code=status.HTTP_403_FORBIDDEN,
        )


# Database Exceptions
class DatabaseError(PlantCareException):
    """Raised when database operation fails."""
    
    def __init__(self, message: str = "Database operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="DATABASE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class DatabaseConnectionError(DatabaseError):
    """Raised when database connection fails."""
    
    def __init__(self, message: str = "Database connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "DATABASE_CONNECTION_ERROR"


class DatabaseTransactionError(DatabaseError):
    """Raised when database transaction fails."""
    
    def __init__(self, message: str = "Database transaction failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "DATABASE_TRANSACTION_ERROR"


class DatabaseConstraintError(DatabaseError):
    """Raised when database constraint is violated."""
    
    def __init__(self, constraint_name: str, details: Optional[Dict[str, Any]] = None):
        message = f"Database constraint violation: {constraint_name}"
        super().__init__(message=message, details=details)
        self.error_code = "DATABASE_CONSTRAINT_ERROR"


# External API Exceptions
class ExternalAPIError(PlantCareException):
    """Raised when external API call fails."""
    
    def __init__(self, api_name: str, message: str = "External API call failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{api_name}: {message}",
            error_code="EXTERNAL_API_ERROR",
            details=details,
            status_code=status.HTTP_502_BAD_GATEWAY,
        )


class ExternalAPIRateLimitError(ExternalAPIError):
    """Raised when external API rate limit is exceeded."""
    
    def __init__(self, api_name: str, details: Optional[Dict[str, Any]] = None):
        message = "Rate limit exceeded"
        super().__init__(api_name=api_name, message=message, details=details)
        self.error_code = "EXTERNAL_API_RATE_LIMIT"
        self.status_code = status.HTTP_429_TOO_MANY_REQUESTS


class ExternalAPITimeoutError(ExternalAPIError):
    """Raised when external API request times out."""
    
    def __init__(self, api_name: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        message = f"Request timeout after {timeout} seconds"
        super().__init__(api_name=api_name, message=message, details=details)
        self.error_code = "EXTERNAL_API_TIMEOUT"
        self.status_code = status.HTTP_504_GATEWAY_TIMEOUT


class ExternalAPIUnavailableError(ExternalAPIError):
    """Raised when external API is unavailable."""
    
    def __init__(self, api_name: str, details: Optional[Dict[str, Any]] = None):
        message = "Service unavailable"
        super().__init__(api_name=api_name, message=message, details=details)
        self.error_code = "EXTERNAL_API_UNAVAILABLE"
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


# Business Logic Exceptions
class BusinessLogicError(PlantCareException):
    """Raised when business logic validation fails."""
    
    def __init__(self, message: str = "Business logic error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="BUSINESS_LOGIC_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PlantNotFoundError(ResourceNotFoundError):
    """Raised when plant is not found."""
    
    def __init__(self, plant_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(resource_type="Plant", resource_id=plant_id, details=details)
        self.error_code = "PLANT_NOT_FOUND"


class CareScheduleNotFoundError(ResourceNotFoundError):
    """Raised when care schedule is not found."""
    
    def __init__(self, schedule_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(resource_type="Care Schedule", resource_id=schedule_id, details=details)
        self.error_code = "CARE_SCHEDULE_NOT_FOUND"


class UserNotFoundError(ResourceNotFoundError):
    """Raised when user is not found."""
    
    def __init__(self, user_id: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(resource_type="User", resource_id=user_id, details=details)
        self.error_code = "USER_NOT_FOUND"


class DuplicatePlantError(ResourceAlreadyExistsError):
    """Raised when trying to add duplicate plant."""
    
    def __init__(self, plant_name: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(resource_type="Plant", identifier=plant_name, details=details)
        self.error_code = "DUPLICATE_PLANT"


# Subscription & Payment Exceptions
class SubscriptionError(PlantCareException):
    """Raised when subscription operation fails."""
    
    def __init__(self, message: str = "Subscription error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="SUBSCRIPTION_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class PaymentError(PlantCareException):
    """Raised when payment operation fails."""
    
    def __init__(self, message: str = "Payment error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="PAYMENT_ERROR",
            details=details,
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
        )


class InactiveSubscriptionError(SubscriptionError):
    """Raised when subscription is inactive."""
    
    def __init__(self, message: str = "Subscription is inactive", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "INACTIVE_SUBSCRIPTION"


class UsageLimitExceededError(SubscriptionError):
    """Raised when usage limit is exceeded."""
    
    def __init__(self, limit_type: str, current_usage: int, limit: int, details: Optional[Dict[str, Any]] = None):
        message = f"{limit_type} usage limit exceeded: {current_usage}/{limit}"
        super().__init__(message=message, details=details)
        self.error_code = "USAGE_LIMIT_EXCEEDED"


# File & Media Exceptions
class FileError(PlantCareException):
    """Raised when file operation fails."""
    
    def __init__(self, message: str = "File operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="FILE_ERROR",
            details=details,
            status_code=status.HTTP_400_BAD_REQUEST,
        )


class InvalidFileTypeError(FileError):
    """Raised when file type is invalid."""
    
    def __init__(self, file_type: str, allowed_types: list, details: Optional[Dict[str, Any]] = None):
        message = f"Invalid file type '{file_type}'. Allowed types: {', '.join(allowed_types)}"
        super().__init__(message=message, details=details)
        self.error_code = "INVALID_FILE_TYPE"


class FileSizeExceededError(FileError):
    """Raised when file size exceeds limit."""
    
    def __init__(self, file_size: int, max_size: int, details: Optional[Dict[str, Any]] = None):
        message = f"File size {file_size} bytes exceeds maximum allowed size {max_size} bytes"
        super().__init__(message=message, details=details)
        self.error_code = "FILE_SIZE_EXCEEDED"


class FileUploadError(FileError):
    """Raised when file upload fails."""
    
    def __init__(self, message: str = "File upload failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "FILE_UPLOAD_ERROR"


# Cache Exceptions
class CacheError(PlantCareException):
    """Raised when cache operation fails."""
    
    def __init__(self, message: str = "Cache operation failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CACHE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class CacheConnectionError(CacheError):
    """Raised when cache connection fails."""
    
    def __init__(self, message: str = "Cache connection failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(message=message, details=details)
        self.error_code = "CACHE_CONNECTION_ERROR"



# Rate Limiting Exceptions
class RateLimitError(PlantCareException):
    """Raised when rate limit is exceeded."""
    
    def __init__(self, message: str = "Rate limit exceeded", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


# New RateLimitExceededError
class RateLimitExceededError(PlantCareException):
    """Raised when a user exceeds allowed request limits."""
    
    def __init__(self, message: str = "Too many requests. Please try again later.", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="RATE_LIMIT_EXCEEDED",
            details=details,
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        )


# Configuration Exceptions
class ConfigurationError(PlantCareException):
    """Raised when configuration is invalid."""
    
    def __init__(self, message: str = "Configuration error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="CONFIGURATION_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class MissingConfigurationError(ConfigurationError):
    """Raised when required configuration is missing."""
    
    def __init__(self, config_key: str, details: Optional[Dict[str, Any]] = None):
        message = f"Missing required configuration: {config_key}"
        super().__init__(message=message, details=details)
        self.error_code = "MISSING_CONFIGURATION"


# Service Exceptions
class ServiceError(PlantCareException):
    """Raised when service operation fails."""
    
    def __init__(self, service_name: str, message: str = "Service error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"{service_name}: {message}",
            error_code="SERVICE_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


class ServiceUnavailableError(ServiceError):
    """Raised when service is unavailable."""
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = "Service unavailable"
        super().__init__(service_name=service_name, message=message, details=details)
        self.error_code = "SERVICE_UNAVAILABLE"
        self.status_code = status.HTTP_503_SERVICE_UNAVAILABLE


# Exception utilities
def handle_database_error(error: Exception) -> PlantCareException:
    """Convert database errors to Plant Care exceptions."""
    error_msg = str(error)
    
    if "connection" in error_msg.lower():
        return DatabaseConnectionError(error_msg)
    elif "constraint" in error_msg.lower():
        return DatabaseConstraintError("Unknown constraint", {"original_error": error_msg})
    elif "transaction" in error_msg.lower():
        return DatabaseTransactionError(error_msg)
    else:
        return DatabaseError(error_msg)


def handle_http_error(error: HTTPException) -> PlantCareException:
    """Convert HTTP errors to Plant Care exceptions."""
    if error.status_code == 401:
        return AuthenticationError(error.detail)
    elif error.status_code == 403:
        return AuthorizationError(error.detail)
    elif error.status_code == 404:
        return ResourceNotFoundError("Resource", "unknown")
    elif error.status_code == 409:
        return ResourceAlreadyExistsError("Resource", "unknown")
    elif error.status_code == 422:
        return ValidationError(error.detail)
    elif error.status_code == 429:
        return RateLimitError(error.detail)
    else:
        return PlantCareException(
            message=error.detail or "HTTP error occurred",
            error_code="HTTP_ERROR",
            status_code=error.status_code,
        )

# Circuit Breaker Exceptions
class CircuitBreakerError(PlantCareException):
    """Base exception for circuit breaker errors."""
    
    def __init__(self, service_name: str, message: str = "Circuit breaker error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Circuit breaker error for {service_name}: {message}",
            error_code="CIRCUIT_BREAKER_ERROR",
            details=details,
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        )


class CircuitBreakerOpenError(CircuitBreakerError):
    """Raised when circuit breaker is open."""
    
    def __init__(self, service_name: str, details: Optional[Dict[str, Any]] = None):
        message = "Circuit breaker is open - service unavailable"
        super().__init__(service_name=service_name, message=message, details=details)
        self.error_code = "CIRCUIT_BREAKER_OPEN"


class CircuitBreakerTimeoutError(CircuitBreakerError):
    """Raised when circuit breaker timeout occurs."""
    
    def __init__(self, service_name: str, timeout: int, details: Optional[Dict[str, Any]] = None):
        message = f"Circuit breaker timeout after {timeout} seconds"
        super().__init__(service_name=service_name, message=message, details=details)
        self.error_code = "CIRCUIT_BREAKER_TIMEOUT"

# Event Processing Exceptions
class EventError(PlantCareException):
    """Base exception for event processing errors."""
    
    def __init__(self, message: str = "Event processing error", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=message,
            error_code="EVENT_ERROR",
            details=details,
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )

class EventProcessingError(EventError):
    """Raised when event processing fails."""
    
    def __init__(self, event_type: str, message: str = "Event processing failed", details: Optional[Dict[str, Any]] = None):
        super().__init__(
            message=f"Failed to process event {event_type}: {message}",
            details=details
        )
        self.error_code = "EVENT_PROCESSING_ERROR"



# Export all exceptions
__all__ = [
    "PlantCareException",
    "AuthenticationError",
    "AuthorizationError",
    "TokenExpiredError",
    "InvalidTokenError",
    "InsufficientPermissionsError",
    "ValidationError",
    "InvalidInputError",
    "MissingRequiredFieldError",
    "InvalidFieldValueError",
    "ResourceNotFoundError",
    "ResourceAlreadyExistsError",
    "ResourceAccessDeniedError",
    "DatabaseError",
    "DatabaseConnectionError",
    "DatabaseTransactionError",
    "DatabaseConstraintError",
    "ExternalAPIError",
    "ExternalAPIRateLimitError",
    "ExternalAPITimeoutError",
    "ExternalAPIUnavailableError",
    "BusinessLogicError",
    "PlantNotFoundError",
    "CareScheduleNotFoundError",
    "UserNotFoundError",
    "DuplicatePlantError",
    "SubscriptionError",
    "PaymentError",
    "InactiveSubscriptionError",
    "UsageLimitExceededError",
    "FileError",
    "InvalidFileTypeError",
    "FileSizeExceededError",
    "FileUploadError",
    "CacheError",
    "CacheConnectionError",
    "RateLimitError",
    "RateLimitExceededError",
    "ConfigurationError",
    "MissingConfigurationError",
    "ServiceError",
    "ServiceUnavailableError",
    "handle_database_error",
    "handle_http_error",
    "CircuitBreakerError",
    "CircuitBreakerOpenError",
    "CircuitBreakerTimeoutError",
    "EventProcessingError"
]