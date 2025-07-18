"""
app/api/middleware/cors.py
Plant Care Application - CORS Middleware

Custom CORS middleware for Plant Care API with:
- Mobile app support
- Web app integration
- Admin panel access
- Development environment support
- Security-focused configuration
"""
import re
from typing import Callable, List, Optional, Union
from fastapi import Request, Response
from fastapi.responses import JSONResponse
import structlog

from app.shared.config.settings import get_settings

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class CORSMiddleware:
    """
    CORS middleware for Plant Care Application.
    
    Handles cross-origin requests for:
    - Plant Care mobile app
    - Web application
    - Admin dashboard
    - Development environments
    """
    
    def __init__(self, app: Callable):
        self.app = app
        
        # Allowed origins for Plant Care Application
        self.allowed_origins = self._get_allowed_origins()
        
        # Allowed origin patterns (regex)
        self.allowed_origin_patterns = [
            r"https://.*\.plantcare\.app",  # Subdomains
            r"http://localhost:\d+",        # Local development
            r"http://127\.0\.0\.1:\d+",     # Local development
            r"capacitor://localhost",       # Capacitor mobile app
            r"ionic://localhost",           # Ionic mobile app
        ]
        
        # Allowed methods for Plant Care API
        self.allowed_methods = [
            "GET",
            "POST", 
            "PUT",
            "PATCH",
            "DELETE",
            "OPTIONS",
            "HEAD"
        ]
        
        # Allowed headers
        self.allowed_headers = [
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
            "x-app-version",
            "x-platform",
            "x-build-number",
            "cache-control",
            "pragma"
        ]
        
        # Headers to expose to clients
        self.exposed_headers = [
            "x-total-count",
            "x-rate-limit-remaining",
            "x-rate-limit-reset",
            "x-request-id",
            "x-process-time",
            "x-auth-time"
        ]
        
        # CORS settings
        self.allow_credentials = True
        self.max_age = 86400  # 24 hours
        self.preflight_cache_time = 3600  # 1 hour
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process CORS for incoming requests."""
        origin = request.headers.get("origin")
        
        # Handle preflight requests
        if request.method == "OPTIONS":
            return self._handle_preflight_request(request, origin)
        
        # Process actual request
        response = await call_next(request)
        
        # Add CORS headers to response
        self._add_cors_headers(response, origin)
        
        return response
    
    def _get_allowed_origins(self) -> List[str]:
        """Get allowed origins based on environment."""
        origins = []
        
        # Production origins
        if settings.ENVIRONMENT == "production":
            origins.extend([
                "https://plantcare.app",
                "https://app.plantcare.app",
                "https://admin.plantcare.app"
            ])
        
        # Staging origins
        elif settings.ENVIRONMENT == "staging":
            origins.extend([
                "https://staging.plantcare.app",
                "https://staging-app.plantcare.app",
                "https://staging-admin.plantcare.app"
            ])
        
        # Development origins
        else:
            origins.extend([
                "http://localhost:3000",   # React dev server
                "http://localhost:3001",   # Alternative React port
                "http://localhost:4200",   # Angular dev server
                "http://localhost:8080",   # Vue.js dev server
                "http://localhost:8100",   # Ionic dev server
                "http://127.0.0.1:3000",
                "http://127.0.0.1:8080",
                "http://127.0.0.1:8100"
            ])
        
        # Always allow mobile app schemes
        origins.extend([
            "capacitor://localhost",
            "ionic://localhost",
            "file://"  # For mobile file access
        ])
        
        return origins
    
    def _is_origin_allowed(self, origin: Optional[str]) -> bool:
        """Check if origin is allowed."""
        if not origin:
            return False
        
        # Check exact matches
        if origin in self.allowed_origins:
            return True
        
        # Check pattern matches
        for pattern in self.allowed_origin_patterns:
            if re.match(pattern, origin):
                return True
        
        # For development, be more permissive
        if settings.ENVIRONMENT == "development":
            # Allow any localhost or local IP
            if "localhost" in origin or "127.0.0.1" in origin:
                return True
            
            # Allow local network IPs (192.168.x.x, 10.x.x.x)
            local_patterns = [
                r"http://192\.168\.\d+\.\d+:\d+",
                r"http://10\.\d+\.\d+\.\d+:\d+",
                r"http://172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+:\d+"
            ]
            
            for pattern in local_patterns:
                if re.match(pattern, origin):
                    return True
        
        return False
    
    def _handle_preflight_request(self, request: Request, origin: Optional[str]) -> Response:
        """Handle CORS preflight OPTIONS request."""
        # Check if origin is allowed
        if not self._is_origin_allowed(origin):
            logger.warning("CORS preflight rejected", origin=origin)
            return JSONResponse(
                status_code=403,
                content={"error": "Origin not allowed"},
                headers={"Access-Control-Allow-Origin": "null"}
            )
        
        # Get requested method and headers
        requested_method = request.headers.get("access-control-request-method")
        requested_headers = request.headers.get("access-control-request-headers", "")
        
        # Validate requested method
        if requested_method and requested_method not in self.allowed_methods:
            logger.warning(
                "CORS preflight rejected - method not allowed",
                origin=origin,
                method=requested_method
            )
            return JSONResponse(
                status_code=405,
                content={"error": "Method not allowed"}
            )
        
        # Validate requested headers
        if requested_headers:
            headers_list = [h.strip().lower() for h in requested_headers.split(",")]
            allowed_headers_lower = [h.lower() for h in self.allowed_headers]
            
            for header in headers_list:
                if header not in allowed_headers_lower:
                    logger.warning(
                        "CORS preflight rejected - header not allowed",
                        origin=origin,
                        header=header
                    )
                    return JSONResponse(
                        status_code=400,
                        content={"error": f"Header not allowed: {header}"}
                    )
        
        # Create preflight response
        response_headers = {
            "Access-Control-Allow-Origin": origin,
            "Access-Control-Allow-Methods": ", ".join(self.allowed_methods),
            "Access-Control-Allow-Headers": ", ".join(self.allowed_headers),
            "Access-Control-Max-Age": str(self.preflight_cache_time),
            "Access-Control-Allow-Credentials": "true" if self.allow_credentials else "false",
            "Vary": "Origin"
        }
        
        logger.info("CORS preflight approved", origin=origin, method=requested_method)
        
        return JSONResponse(
            status_code=200,
            content={"message": "Preflight approved"},
            headers=response_headers
        )
    
    def _add_cors_headers(self, response: Response, origin: Optional[str]):
        """Add CORS headers to response."""
        # Check if origin is allowed
        if self._is_origin_allowed(origin):
            response.headers["Access-Control-Allow-Origin"] = origin
            
            if self.allow_credentials:
                response.headers["Access-Control-Allow-Credentials"] = "true"
            
            # Add exposed headers
            if self.exposed_headers:
                response.headers["Access-Control-Expose-Headers"] = ", ".join(self.exposed_headers)
            
            # Add Vary header for caching
            response.headers["Vary"] = "Origin"
            
            logger.debug("CORS headers added", origin=origin)
        else:
            # Origin not allowed - don't add CORS headers
            if origin:
                logger.warning("CORS blocked - origin not allowed", origin=origin)
    
    def get_middleware_status(self) -> dict:
        """Get CORS middleware status."""
        return {
            "name": "CORSMiddleware",
            "enabled": True,
            "allowed_origins_count": len(self.allowed_origins),
            "allowed_methods_count": len(self.allowed_methods),
            "allowed_headers_count": len(self.allowed_headers),
            "exposed_headers_count": len(self.exposed_headers),
            "allow_credentials": self.allow_credentials,
            "max_age": self.max_age,
            "environment": settings.ENVIRONMENT
        }


# Standalone CORS functions
def check_origin_allowed(origin: str) -> bool:
    """Check if an origin is allowed."""
    middleware = CORSMiddleware(None)
    return middleware._is_origin_allowed(origin)


def get_allowed_origins() -> List[str]:
    """Get list of allowed origins."""
    middleware = CORSMiddleware(None)
    return middleware.allowed_origins


def add_cors_headers_to_response(response: Response, origin: str):
    """Add CORS headers to an existing response."""
    middleware = CORSMiddleware(None)
    middleware._add_cors_headers(response, origin)