"""
app/api/middleware/logging.py
Plant Care Application - Logging Middleware

Request/response logging middleware with Plant Care specific features:
- Structured logging with context
- Performance metrics tracking
- User activity logging
- Security event logging
- Error tracking and monitoring
"""
import time
import uuid
import json
from typing import Callable, Dict, Any, Optional
from fastapi import Request, Response
import structlog

from app.shared.config.settings import get_settings
from app.shared.utils.logging import log_api_request, log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class LoggingMiddleware:
    """
    Logging middleware for Plant Care Application.
    
    Provides comprehensive request/response logging with:
    - Request/response timing
    - User context tracking
    - Plant Care specific metrics
    - Security event logging
    - Performance monitoring
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
        # Sensitive headers that should be masked
        self.sensitive_headers = {
            "authorization",
            "x-api-key", 
            "cookie",
            "x-auth-token",
            "x-session-token"
        }
        
        # Headers to include in logs
        self.logged_headers = {
            "user-agent",
            "x-forwarded-for",
            "x-real-ip",
            "x-device-id",
            "x-app-version",
            "content-type",
            "accept"
        }
        
        # Paths to exclude from detailed logging
        self.exclude_paths = {
            "/health",
            "/metrics",
            "/favicon.ico"
        }
        
        # Paths that require minimal logging
        self.minimal_log_paths = {
            "/docs",
            "/redoc",
            "/openapi.json"
        }
        
        # Plant Care specific metrics to track
        self.tracked_metrics = {
            "api_requests_total",
            "api_request_duration_seconds", 
            "api_errors_total",
            "plant_operations_total",
            "care_tasks_total",
            "ai_requests_total",
            "file_uploads_total"
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process request logging."""
        # Generate request ID for tracking
        request_id = str(uuid.uuid4())
        request.state.request_id = request_id
        
        # Start timing
        start_time = time.time()
        
        # Skip detailed logging for excluded paths
        if self._should_skip_logging(request.url.path):
            response = await call_next(request)
            response.headers["X-Request-ID"] = request_id
            return response
        
        # Extract request context
        request_context = self._extract_request_context(request)
        
        # Log request start
        if not self._is_minimal_log_path(request.url.path):
            logger.info(
                "Request started",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                query_params=str(request.query_params),
                **request_context
            )
        
        try:
            # Process request
            response = await call_next(request)
            
            # Calculate timing
            process_time = time.time() - start_time
            
            # Extract response context
            response_context = self._extract_response_context(response, process_time)
            
            # Add headers to response
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = f"{process_time:.3f}s"
            
            # Log successful request
            self._log_request_completion(
                request, response, request_id, process_time, 
                request_context, response_context
            )
            
            # Track Plant Care specific metrics
            await self._track_plant_care_metrics(request, response, process_time)
            
            return response
            
        except Exception as e:
            # Calculate timing for failed request
            process_time = time.time() - start_time
            
            # Log error
            logger.error(
                "Request failed",
                request_id=request_id,
                method=request.method,
                path=request.url.path,
                error=str(e),
                process_time=process_time,
                **request_context
            )
            
            # Track error metrics
            await self._track_error_metrics(request, str(e))
            
            # Re-raise the exception
            raise
    
    def _should_skip_logging(self, path: str) -> bool:
        """Check if detailed logging should be skipped."""
        return any(path.startswith(excluded) for excluded in self.exclude_paths)
    
    def _is_minimal_log_path(self, path: str) -> bool:
        """Check if path requires minimal logging."""
        return any(path.startswith(minimal) for minimal in self.minimal_log_paths)
    
    def _extract_request_context(self, request: Request) -> Dict[str, Any]:
        """Extract context information from request."""
        context = {
            "client_ip": self._get_client_ip(request),
            "user_agent": request.headers.get("user-agent", "unknown"),
            "app_version": request.headers.get("x-app-version"),
            "device_id": request.headers.get("x-device-id"),
        }
        
        # Add user context if available
        user = getattr(request.state, "user", None)
        if user:
            context.update({
                "user_id": user.get("user_id"),
                "user_role": user.get("role"),
                "subscription_status": user.get("subscription_status"),
                "is_premium": user.get("is_premium", False)
            })
        
        # Add selected headers
        headers = {}
        for header in self.logged_headers:
            value = request.headers.get(header)
            if value:
                headers[header] = value
        
        if headers:
            context["headers"] = headers
        
        return context
    
    def _extract_response_context(self, response: Response, process_time: float) -> Dict[str, Any]:
        """Extract context information from response."""
        return {
            "status_code": response.status_code,
            "process_time": process_time,
            "content_length": response.headers.get("content-length"),
            "content_type": response.headers.get("content-type")
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
        
        return request.client.host
    
    def _log_request_completion(
        self,
        request: Request,
        response: Response, 
        request_id: str,
        process_time: float,
        request_context: Dict[str, Any],
        response_context: Dict[str, Any]
    ):
        """Log completed request with full context."""
        log_level = "info"
        
        # Determine log level based on status code
        if response.status_code >= 500:
            log_level = "error"
        elif response.status_code >= 400:
            log_level = "warning"
        elif process_time > 2.0:  # Slow request
            log_level = "warning"
        
        log_data = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": str(request.query_params) if request.query_params else None,
            **request_context,
            **response_context
        }
        
        # Use appropriate log level
        if log_level == "error":
            logger.error("Request completed with error", **log_data)
        elif log_level == "warning":
            logger.warning("Request completed with warning", **log_data)
        else:
            logger.info("Request completed successfully", **log_data)
        
        # Also use the shared logging utility
        log_api_request(
            method=request.method,
            url=str(request.url),
            status_code=response.status_code,
            process_time=process_time,
            user_id=request_context.get("user_id"),
            user_agent=request_context.get("user_agent"),
            ip_address=request_context.get("client_ip"),
            endpoint=request.url.path
        )
    
    async def _track_plant_care_metrics(
        self,
        request: Request,
        response: Response,
        process_time: float
    ):
        """Track Plant Care specific metrics."""
        try:
            path = request.url.path
            method = request.method
            status_code = response.status_code
            user = getattr(request.state, "user", None)
            
            # Track API request metrics
            # (In a real implementation, this would integrate with Prometheus/monitoring)
            
            # Track plant operations
            if "/plants" in path:
                metric_type = "plant_operations_total"
                if method == "POST":
                    operation = "create"
                elif method == "PUT" or method == "PATCH":
                    operation = "update"
                elif method == "DELETE":
                    operation = "delete"
                else:
                    operation = "read"
                
                logger.info(
                    "Plant operation tracked",
                    metric_type=metric_type,
                    operation=operation,
                    user_id=user.get("user_id") if user else None,
                    process_time=process_time
                )
            
            # Track care task operations
            elif "/care" in path:
                logger.info(
                    "Care operation tracked",
                    metric_type="care_tasks_total",
                    path=path,
                    method=method,
                    user_id=user.get("user_id") if user else None
                )
            
            # Track AI requests
            elif "/ai" in path:
                logger.info(
                    "AI operation tracked",
                    metric_type="ai_requests_total",
                    path=path,
                    user_id=user.get("user_id") if user else None,
                    process_time=process_time
                )
            
            # Track file uploads
            elif "upload" in path:
                logger.info(
                    "File upload tracked",
                    metric_type="file_uploads_total",
                    path=path,
                    user_id=user.get("user_id") if user else None,
                    status_code=status_code
                )
            
        except Exception as e:
            logger.error("Error tracking Plant Care metrics", error=str(e))
    
    async def _track_error_metrics(self, request: Request, error: str):
        """Track error metrics for monitoring."""
        try:
            user = getattr(request.state, "user", None)
            
            logger.error(
                "API error tracked",
                metric_type="api_errors_total",
                path=request.url.path,
                method=request.method,
                error=error,
                user_id=user.get("user_id") if user else None
            )
            
        except Exception as e:
            logger.error("Error tracking error metrics", error=str(e))
    
    def get_middleware_status(self) -> Dict[str, Any]:
        """Get logging middleware status."""
        return {
            "name": "LoggingMiddleware",
            "enabled": True,
            "sensitive_headers_count": len(self.sensitive_headers),
            "logged_headers_count": len(self.logged_headers),
            "exclude_paths_count": len(self.exclude_paths),
            "tracked_metrics_count": len(self.tracked_metrics)
        }


# Standalone logging functions
def log_plant_care_event(
    event_type: str,
    user_id: Optional[str] = None,
    plant_id: Optional[str] = None,
    **kwargs
):
    """Log Plant Care specific events."""
    logger.info(
        "Plant Care event",
        event_type=event_type,
        user_id=user_id,
        plant_id=plant_id,
        **kwargs
    )


def log_user_activity(
    user_id: str,
    activity_type: str,
    details: Optional[Dict[str, Any]] = None
):
    """Log user activity for analytics."""
    logger.info(
        "User activity",
        user_id=user_id,
        activity_type=activity_type,
        details=details or {}
    )


def log_performance_metric(
    metric_name: str,
    value: float,
    tags: Optional[Dict[str, str]] = None
):
    """Log performance metrics."""
    logger.info(
        "Performance metric",
        metric_name=metric_name,
        value=value,
        tags=tags or {}
    )