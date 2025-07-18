"""
app/api/middleware/authentication.py
Plant Care Application - Authentication Middleware

Custom authentication middleware for Plant Care API that handles:
- Supabase JWT token validation
- API key authentication
- User session management
- Role-based access control
"""
import time
from typing import Callable, Optional
from fastapi import Request, Response, HTTPException, status
from fastapi.responses import JSONResponse
import structlog

from app.shared.config.settings import get_settings
from app.shared.config.supabase import get_supabase_auth
from app.shared.core.security import security_manager
from app.shared.core.exceptions import (
    AuthenticationError,
    InvalidTokenError,
    TokenExpiredError
)
from app.shared.utils.formatters import format_error_response
from app.shared.utils.logging import log_security_event

# Setup logger
logger = structlog.get_logger(__name__)

# Get settings
settings = get_settings()

class AuthenticationMiddleware:
    """
    Authentication middleware for Plant Care Application.
    
    Handles multiple authentication methods:
    1. JWT tokens from Supabase Auth
    2. API keys for service integrations
    3. Optional authentication for public endpoints
    """
    
    def __init__(self, app: Callable):
        self.app = app
        self.supabase_auth = get_supabase_auth()
        
        # Paths that don't require authentication
        self.exclude_paths = {
            "/health",
            "/docs",
            "/redoc", 
            "/openapi.json",
            "/api/v1/",
            "/api/v1/auth/register",
            "/api/v1/auth/login",
            "/api/v1/auth/forgot-password",
            "/api/v1/auth/reset-password",
            "/api/v1/auth/verify-email"
        }
        
        # Paths where authentication is optional
        self.optional_auth_paths = {
            "/api/v1/plants/public",
            "/api/v1/community/public",
            "/api/v1/content/public"
        }
        
        # Admin-only paths
        self.admin_paths = {
            "/api/v1/admin"
        }
        
        # Premium-only paths
        self.premium_paths = {
            "/api/v1/analytics",
            "/api/v1/ai/advanced",
            "/api/v1/insights"
        }
    
    async def __call__(self, request: Request, call_next: Callable) -> Response:
        """Process authentication for incoming requests."""
        start_time = time.time()
        
        try:
            # Skip authentication for excluded paths
            if self._should_skip_auth(request.url.path):
                return await call_next(request)
            
            # Extract authentication credentials
            auth_result = await self._authenticate_request(request)
            
            if auth_result["authenticated"]:
                # Add user information to request state
                request.state.user = auth_result["user"]
                request.state.auth_method = auth_result["method"]
                
                # Check role-based access
                if not self._check_role_access(request.url.path, auth_result["user"]):
                    log_security_event(
                        event_type="authorization_denied",
                        user_id=auth_result["user"].get("user_id"),
                        path=request.url.path,
                        role=auth_result["user"].get("role")
                    )
                    return JSONResponse(
                        status_code=status.HTTP_403_FORBIDDEN,
                        content=format_error_response(
                            error_code="INSUFFICIENT_PERMISSIONS",
                            message="Insufficient permissions to access this resource",
                            status_code=403
                        )
                    )
                
                # Log successful authentication
                log_security_event(
                    event_type="authentication_success",
                    user_id=auth_result["user"].get("user_id"),
                    auth_method=auth_result["method"],
                    path=request.url.path
                )
                
            elif not self._is_optional_auth_path(request.url.path):
                # Authentication required but not provided
                return JSONResponse(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    content=format_error_response(
                        error_code="AUTHENTICATION_REQUIRED",
                        message="Authentication required to access this resource",
                        status_code=401
                    ),
                    headers={"WWW-Authenticate": "Bearer"}
                )
            
            # Continue to next middleware/endpoint
            response = await call_next(request)
            
            # Add authentication timing header
            auth_time = time.time() - start_time
            response.headers["X-Auth-Time"] = f"{auth_time:.3f}s"
            
            return response
            
        except (AuthenticationError, InvalidTokenError, TokenExpiredError) as e:
            logger.warning("Authentication failed", error=str(e), path=request.url.path)
            
            # Log authentication failure
            log_security_event(
                event_type="authentication_failed",
                error=str(e),
                path=request.url.path,
                ip_address=request.client.host
            )
            
            return JSONResponse(
                status_code=status.HTTP_401_UNAUTHORIZED,
                content=format_error_response(
                    error_code="AUTHENTICATION_FAILED",
                    message=str(e),
                    status_code=401
                ),
                headers={"WWW-Authenticate": "Bearer"}
            )
            
        except Exception as e:
            logger.error("Authentication middleware error", error=str(e), path=request.url.path)
            
            return JSONResponse(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                content=format_error_response(
                    error_code="AUTHENTICATION_ERROR",
                    message="Authentication system error",
                    status_code=500
                )
            )
    
    def _should_skip_auth(self, path: str) -> bool:
        """Check if authentication should be skipped for this path."""
        # Exact path matches
        if path in self.exclude_paths:
            return True
        
        # Prefix matches for dynamic paths
        for excluded_path in self.exclude_paths:
            if path.startswith(excluded_path.rstrip("/")):
                return True
        
        return False
    
    def _is_optional_auth_path(self, path: str) -> bool:
        """Check if authentication is optional for this path."""
        for optional_path in self.optional_auth_paths:
            if path.startswith(optional_path):
                return True
        return False
    
    async def _authenticate_request(self, request: Request) -> dict:
        """
        Authenticate request using available credentials.
        
        Returns:
            dict: Authentication result with user info
        """
        # Try JWT token authentication first
        authorization = request.headers.get("authorization")
        if authorization and authorization.startswith("Bearer "):
            token = authorization.split(" ")[1]
            user_data = await self._authenticate_jwt_token(token)
            if user_data:
                return {
                    "authenticated": True,
                    "user": user_data,
                    "method": "jwt"
                }
        
        # Try API key authentication
        api_key = request.headers.get("x-api-key")
        if api_key:
            user_data = await self._authenticate_api_key(api_key)
            if user_data:
                return {
                    "authenticated": True,
                    "user": user_data,
                    "method": "api_key"
                }
        
        return {"authenticated": False, "user": None, "method": None}
    
    async def _authenticate_jwt_token(self, token: str) -> Optional[dict]:
        """
        Authenticate JWT token from Supabase Auth.
        
        Args:
            token: JWT token string
            
        Returns:
            Optional[dict]: User data if token is valid, None otherwise
        """
        try:
            # Validate JWT token using security manager
            payload = security_manager.validate_supabase_jwt(token)
            
            # Extract user information for Plant Care
            user_data = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "role": payload.get("role", "user"),
                "subscription_status": payload.get("subscription_status", "free"),
                "email_verified": payload.get("email_verified", False),
                "phone_verified": payload.get("phone_verified", False),
                "user_metadata": payload.get("user_metadata", {}),
                "app_metadata": payload.get("app_metadata", {}),
                "is_premium": payload.get("subscription_status") in ["premium_monthly", "premium_yearly"],
                "is_expert": payload.get("role") in ["expert", "admin"],
                "is_admin": payload.get("role") == "admin"
            }
            
            return user_data
            
        except (InvalidTokenError, TokenExpiredError):
            return None
        except Exception as e:
            logger.error("JWT token validation error", error=str(e))
            return None
    
    async def _authenticate_api_key(self, api_key: str) -> Optional[dict]:
        """
        Authenticate API key for service integrations.
        
        Args:
            api_key: API key string
            
        Returns:
            Optional[dict]: Service/user data if API key is valid, None otherwise
        """
        try:
            # Validate API key format
            if not api_key.startswith("pc_"):
                return None
            
            # TODO: Validate API key against database
            # For now, we'll use the security manager's basic validation
            if security_manager.validate_api_key(api_key, "service"):
                # Return service user data
                return {
                    "user_id": f"service_{api_key[-8:]}",
                    "email": "service@plantcare.app",
                    "role": "service",
                    "subscription_status": "premium_yearly",
                    "email_verified": True,
                    "phone_verified": False,
                    "user_metadata": {"service": True},
                    "app_metadata": {"api_key": api_key[-8:]},
                    "is_premium": True,
                    "is_expert": False,
                    "is_admin": False,
                    "is_service": True
                }
            
            return None
            
        except Exception as e:
            logger.error("API key validation error", error=str(e))
            return None
    
    def _check_role_access(self, path: str, user: dict) -> bool:
        """
        Check if user's role allows access to the requested path.
        
        Args:
            path: Request path
            user: User data with role information
            
        Returns:
            bool: True if access is allowed
        """
        try:
            user_role = user.get("role", "user")
            
            # Check admin-only paths
            for admin_path in self.admin_paths:
                if path.startswith(admin_path):
                    if user_role != "admin":
                        return False
            
            # Check premium-only paths
            for premium_path in self.premium_paths:
                if path.startswith(premium_path):
                    if not user.get("is_premium", False) and user_role not in ["expert", "admin"]:
                        return False
            
            # Check expert-only features
            if "/expert/" in path:
                if not user.get("is_expert", False) and user_role != "admin":
                    return False
            
            return True
            
        except Exception as e:
            logger.error("Role access check error", error=str(e))
            return False
    
    def get_middleware_status(self) -> dict:
        """Get authentication middleware status."""
        return {
            "name": "AuthenticationMiddleware",
            "enabled": True,
            "supabase_connected": self.supabase_auth is not None,
            "exclude_paths_count": len(self.exclude_paths),
            "optional_auth_paths_count": len(self.optional_auth_paths),
            "admin_paths_count": len(self.admin_paths),
            "premium_paths_count": len(self.premium_paths)
        }


# Standalone authentication functions for dependency injection
async def authenticate_request(request: Request) -> Optional[dict]:
    """
    Standalone function to authenticate a request.
    Can be used as a FastAPI dependency.
    """
    auth_middleware = AuthenticationMiddleware(None)
    return await auth_middleware._authenticate_request(request)


async def require_authentication(request: Request) -> dict:
    """
    Require authentication and return user data.
    Raises HTTPException if not authenticated.
    """
    result = await authenticate_request(request)
    
    if not result["authenticated"]:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication required",
            headers={"WWW-Authenticate": "Bearer"}
        )
    
    return result["user"]


async def require_admin_role(request: Request) -> dict:
    """
    Require admin role and return user data.
    Raises HTTPException if not admin.
    """
    user = await require_authentication(request)
    
    if user.get("role") != "admin":
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return user


async def require_premium_subscription(request: Request) -> dict:
    """
    Require premium subscription and return user data.
    Raises HTTPException if not premium.
    """
    user = await require_authentication(request)
    
    if not user.get("is_premium", False) and user.get("role") not in ["expert", "admin"]:
        raise HTTPException(
            status_code=status.HTTP_402_PAYMENT_REQUIRED,
            detail="Premium subscription required"
        )
    
    return user


async def optional_authentication(request: Request) -> Optional[dict]:
    """
    Optional authentication - returns user data if authenticated, None otherwise.
    Does not raise exceptions.
    """
    try:
        result = await authenticate_request(request)
        return result["user"] if result["authenticated"] else None
    except Exception:
        return None