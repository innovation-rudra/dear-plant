"""
app/shared/core/dependencies.py
Plant Care Application - FastAPI Dependencies

FastAPI dependency injection for authentication, authorization, database sessions,
and Plant Care specific dependencies.
"""
from typing import Any, Dict, Optional, Annotated
from fastapi import Depends, HTTPException, status, Request, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
import structlog

from app.shared.config.settings import get_settings
from app.shared.infrastructure.database.connection import get_db_manager
from app.shared.infrastructure.cache.redis_client import get_redis_manager
from app.shared.core.security import security_manager
from app.shared.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    RateLimitError,
    ValidationError
)
from app.shared.utils.logging import log_api_call

# Setup logger
logger = structlog.get_logger(__name__)

# Security scheme
security_scheme = HTTPBearer()

# Get settings
settings = get_settings()


async def get_database_session() -> AsyncSession:
    """
    Get database session for Plant Care operations.
    
    Returns:
        AsyncSession: Database session
    """
    db_manager = get_database_manager()
    async with db_manager.get_session() as session:
        try:
            yield session
        except Exception as e:
            await session.rollback()
            logger.error("Database session error", error=str(e))
            raise
        finally:
            await session.close()


async def get_redis_session():
    """
    Get Redis session for caching Plant Care data.
    
    Returns:
        Redis client session
    """
    redis_manager = get_redis_manager()
    return await redis_manager.get_client()


async def get_current_user_from_token(
    credentials: HTTPAuthorizationCredentials = Depends(security_scheme)
) -> Dict[str, Any]:
    """
    Extract current user from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        
    Returns:
        Dict: User information from token
        
    Raises:
        HTTPException: If token is invalid or expired
    """
    try:
        # Validate JWT token
        payload = security_manager.validate_supabase_jwt(credentials.credentials)
        
        # Extract user information
        user_info = {
            "user_id": payload.get("sub"),
            "email": payload.get("email"),
            "role": payload.get("role", "user"),
            "subscription_status": payload.get("subscription_status", "free"),
            "email_verified": payload.get("email_verified", False),
            "phone_verified": payload.get("phone_verified", False),
            "user_metadata": payload.get("user_metadata", {}),
            "app_metadata": payload.get("app_metadata", {})
        }
        
        # Validate required fields
        if not user_info["user_id"]:
            raise AuthenticationError("Invalid token: missing user ID")
        
        if not user_info["email"]:
            raise AuthenticationError("Invalid token: missing email")
        
        logger.info(
            "User authenticated successfully",
            user_id=user_info["user_id"],
            email=user_info["email"],
            role=user_info["role"]
        )
        
        return user_info
        
    except Exception as e:
        logger.warning("Authentication failed", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Could not validate credentials",
            headers={"WWW-Authenticate": "Bearer"},
        )


async def get_current_active_user(
    current_user: Dict[str, Any] = Depends(get_current_user_from_token),
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    Get current active user with additional database checks.
    
    Args:
        current_user: User from token
        db: Database session
        
    Returns:
        Dict: Enhanced user information
        
    Raises:
        HTTPException: If user is inactive or not found
    """
    try:
        # Check if user is active in database
        # This would typically query the users table
        user_id = current_user["user_id"]
        
        # Add plant care specific user data
        current_user.update({
            "is_premium": current_user["subscription_status"] in ["premium_monthly", "premium_yearly"],
            "is_expert": current_user["role"] in ["expert", "admin"],
            "is_admin": current_user["role"] == "admin",
            "can_access_ai_features": current_user["subscription_status"] in ["premium_monthly", "premium_yearly"],
            "can_access_analytics": current_user["subscription_status"] in ["premium_monthly", "premium_yearly"],
            "plant_limit": 5 if current_user["subscription_status"] == "free" else 999,
            "photo_limit": 1 if current_user["subscription_status"] == "free" else 999
        })
        
        logger.info(
            "Active user validated",
            user_id=user_id,
            is_premium=current_user["is_premium"],
            role=current_user["role"]
        )
        
        return current_user
        
    except Exception as e:
        logger.error("Error validating active user", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User account is inactive or not found"
        )


async def get_premium_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Ensure current user has premium subscription.
    
    Args:
        current_user: Current active user
        
    Returns:
        Dict: Premium user information
        
    Raises:
        HTTPException: If user doesn't have premium subscription
    """
    if not current_user["is_premium"]:
        logger.warning(
            "Premium access denied",
            user_id=current_user["user_id"],
            subscription_status=current_user["subscription_status"]
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Premium subscription required for this feature"
        )
    
    return current_user


async def get_expert_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Ensure current user is an expert or admin.
    
    Args:
        current_user: Current active user
        
    Returns:
        Dict: Expert user information
        
    Raises:
        HTTPException: If user is not an expert
    """
    if not current_user["is_expert"]:
        logger.warning(
            "Expert access denied",
            user_id=current_user["user_id"],
            role=current_user["role"]
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Expert or admin privileges required"
        )
    
    return current_user


async def get_admin_user(
    current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> Dict[str, Any]:
    """
    Ensure current user is an admin.
    
    Args:
        current_user: Current active user
        
    Returns:
        Dict: Admin user information
        
    Raises:
        HTTPException: If user is not an admin
    """
    if not current_user["is_admin"]:
        logger.warning(
            "Admin access denied",
            user_id=current_user["user_id"],
            role=current_user["role"]
        )
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Admin privileges required"
        )
    
    return current_user


async def check_plant_ownership(
    plant_id: str,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session)
) -> bool:
    """
    Check if current user owns the specified plant.
    
    Args:
        plant_id: Plant ID to check
        current_user: Current user
        db: Database session
        
    Returns:
        bool: True if user owns the plant
        
    Raises:
        HTTPException: If user doesn't own the plant
    """
    try:
        # In a real implementation, this would query the plants table
        # For now, we'll assume the check passes for non-admin users
        user_id = current_user["user_id"]
        
        # Admins can access any plant
        if current_user["is_admin"]:
            return True
        
        # TODO: Query database to check plant ownership
        # query = "SELECT user_id FROM plants WHERE plant_id = :plant_id"
        # result = await db.execute(text(query), {"plant_id": plant_id})
        # plant_owner = result.scalar_one_or_none()
        
        # For now, assume ownership check passes
        plant_owner = user_id  # This would come from database
        
        if plant_owner != user_id:
            logger.warning(
                "Plant ownership violation",
                user_id=user_id,
                plant_id=plant_id,
                actual_owner=plant_owner
            )
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You don't have permission to access this plant"
            )
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking plant ownership", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error validating plant ownership"
        )


async def check_rate_limit(
    request: Request,
    current_user: Optional[Dict[str, Any]] = None,
    redis_client = Depends(get_redis_session)
) -> bool:
    """
    Check rate limiting for Plant Care API endpoints.
    
    Args:
        request: FastAPI request object
        current_user: Current user (if authenticated)
        redis_client: Redis client for storing rate limit data
        
    Returns:
        bool: True if request is within rate limits
        
    Raises:
        HTTPException: If rate limit exceeded
    """
    try:
        # Determine rate limit key
        if current_user:
            # User-based rate limiting
            key = f"rate_limit:user:{current_user['user_id']}"
            # Premium users get higher limits
            if current_user.get("is_premium"):
                limit = settings.PREMIUM_RATE_LIMIT_PER_HOUR
            else:
                limit = settings.RATE_LIMIT_PER_HOUR
        else:
            # IP-based rate limiting for anonymous users
            client_ip = request.client.host
            key = f"rate_limit:ip:{client_ip}"
            limit = settings.ANONYMOUS_RATE_LIMIT_PER_HOUR
        
        # Check current count
        current_count = await redis_client.get(key)
        if current_count is None:
            current_count = 0
        else:
            current_count = int(current_count)
        
        # Check if limit exceeded
        if current_count >= limit:
            logger.warning(
                "Rate limit exceeded",
                key=key,
                current_count=current_count,
                limit=limit,
                endpoint=str(request.url)
            )
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Maximum {limit} requests per hour.",
                headers={"Retry-After": "3600"}
            )
        
        # Increment counter
        await redis_client.incr(key)
        await redis_client.expire(key, 3600)  # 1 hour TTL
        
        return True
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error checking rate limit", error=str(e))
        # Don't block requests if rate limiting fails
        return True


async def validate_plant_care_api_key(
    x_api_key: Annotated[str, Header(alias="X-API-Key")],
    db: AsyncSession = Depends(get_database_session)
) -> Dict[str, Any]:
    """
    Validate Plant Care API key for external integrations.
    
    Args:
        x_api_key: API key from header
        db: Database session
        
    Returns:
        Dict: API key information and associated user
        
    Raises:
        HTTPException: If API key is invalid
    """
    try:
        if not x_api_key.startswith("pc_"):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid API key format"
            )
        
        # TODO: Query database to validate API key
        # In a real implementation, this would check the api_keys table
        # query = "SELECT user_id, permissions, active FROM api_keys WHERE key_hash = :key_hash"
        # key_hash = hashlib.sha256(x_api_key.encode()).hexdigest()
        # result = await db.execute(text(query), {"key_hash": key_hash})
        # api_key_data = result.first()
        
        # For now, assume valid API key
        api_key_data = {
            "user_id": "api_user_123",
            "permissions": ["plants:read", "care:read", "weather:read"],
            "active": True
        }
        
        if not api_key_data or not api_key_data["active"]:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or inactive API key"
            )
        
        logger.info(
            "API key validated",
            user_id=api_key_data["user_id"],
            permissions=api_key_data["permissions"]
        )
        
        return api_key_data
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error("Error validating API key", error=str(e))
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="API key validation failed"
        )


async def get_plant_care_context(
    current_user: Dict[str, Any] = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_database_session),
    redis_client = Depends(get_redis_session)
) -> Dict[str, Any]:
    """
    Get Plant Care specific context for the current user.
    
    Args:
        current_user: Current authenticated user
        db: Database session
        redis_client: Redis client
        
    Returns:
        Dict: Plant Care context including user stats and preferences
    """
    try:
        user_id = current_user["user_id"]
        
        # Try to get cached context first
        cache_key = f"user_context:{user_id}"
        cached_context = await redis_client.get(cache_key)
        
        if cached_context:
            import json
            return json.loads(cached_context)
        
        # TODO: Query database for user context
        # In a real implementation, this would query multiple tables
        context = {
            "user_stats": {
                "total_plants": 0,  # Query plants table
                "care_streak_days": 0,  # Query care_history table
                "plants_watered_today": 0,  # Query care_history table
                "health_score_average": 0,  # Query health_records table
                "milestones_achieved": 0,  # Query milestones table
                "community_posts": 0,  # Query community_posts table
            },
            "preferences": {
                "notification_preferences": {
                    "care_reminders": True,
                    "health_alerts": True,
                    "community_updates": False,
                    "marketing_emails": False
                },
                "privacy_settings": {
                    "profile_visibility": "friends",
                    "plant_collection_visibility": "private",
                    "share_growth_photos": False
                },
                "app_settings": {
                    "theme": "auto",
                    "language": "en",
                    "units": "metric",
                    "timezone": "UTC"
                }
            },
            "subscription_info": {
                "plan": current_user["subscription_status"],
                "is_premium": current_user["is_premium"],
                "features_available": {
                    "unlimited_plants": current_user["is_premium"],
                    "ai_chat": current_user["is_premium"],
                    "advanced_analytics": current_user["is_premium"],
                    "family_sharing": current_user["is_premium"],
                    "expert_consultation": current_user["is_premium"]
                }
            },
            "limits": {
                "plants": current_user["plant_limit"],
                "photos_per_plant": current_user["photo_limit"],
                "api_requests_per_hour": settings.PREMIUM_RATE_LIMIT_PER_HOUR if current_user["is_premium"] else settings.RATE_LIMIT_PER_HOUR
            }
        }
        
        # Cache context for 5 minutes
        import json
        await redis_client.setex(cache_key, 300, json.dumps(context))
        
        logger.info(
            "Plant Care context loaded",
            user_id=user_id,
            total_plants=context["user_stats"]["total_plants"],
            is_premium=context["subscription_info"]["is_premium"]
        )
        
        return context
        
    except Exception as e:
        logger.error("Error loading Plant Care context", error=str(e))
        # Return minimal context on error
        return {
            "user_stats": {},
            "preferences": {},
            "subscription_info": {"plan": "free", "is_premium": False},
            "limits": {"plants": 5, "photos_per_plant": 1}
        }


async def log_api_access(
    request: Request,
    current_user: Optional[Dict[str, Any]] = None
):
    """
    Log API access for Plant Care endpoints.
    
    Args:
        request: FastAPI request object
        current_user: Current user (if authenticated)
    """
    try:
        log_api_call(
            method=request.method,
            url=str(request.url),
            user_id=current_user["user_id"] if current_user else None,
            user_agent=request.headers.get("user-agent"),
            ip_address=request.client.host,
            endpoint=request.url.path
        )
    except Exception as e:
        logger.error("Error logging API access", error=str(e))


# Type aliases for common dependency combinations
CurrentUser = Annotated[Dict[str, Any], Depends(get_current_active_user)]
PremiumUser = Annotated[Dict[str, Any], Depends(get_premium_user)]
ExpertUser = Annotated[Dict[str, Any], Depends(get_expert_user)]
AdminUser = Annotated[Dict[str, Any], Depends(get_admin_user)]
DatabaseSession = Annotated[AsyncSession, Depends(get_database_session)]
RedisSession = Annotated[Any, Depends(get_redis_session)]
PlantCareContext = Annotated[Dict[str, Any], Depends(get_plant_care_context)]


# Dependency combinations for Plant Care endpoints
async def get_authenticated_plant_care_user(
    current_user: CurrentUser,
    context: PlantCareContext,
    db: DatabaseSession,
    request: Request
):
    """
    Complete dependency for authenticated Plant Care endpoints.
    
    Returns tuple of (user, context, db_session)
    """
    await log_api_access(request, current_user)
    return current_user, context, db


async def get_premium_plant_care_user(
    premium_user: PremiumUser,
    context: PlantCareContext,
    db: DatabaseSession,
    request: Request
):
    """
    Complete dependency for premium Plant Care endpoints.
    
    Returns tuple of (premium_user, context, db_session)
    """
    await log_api_access(request, premium_user)
    return premium_user, context, db


# Plant-specific dependencies
class PlantAccessDependency:
    """Dependency class for plant-specific endpoints."""
    
    def __init__(self, require_ownership: bool = True):
        self.require_ownership = require_ownership
    
    async def __call__(
        self,
        plant_id: str,
        current_user: CurrentUser,
        db: DatabaseSession
    ) -> Dict[str, Any]:
        """
        Validate plant access and return plant data.
        
        Args:
            plant_id: Plant ID from path parameter
            current_user: Current authenticated user
            db: Database session
            
        Returns:
            Dict: Plant data with access validation
        """
        if self.require_ownership:
            await check_plant_ownership(plant_id, current_user, db)
        
        # TODO: Query plant data from database
        # In a real implementation, this would fetch the plant
        plant_data = {
            "plant_id": plant_id,
            "user_id": current_user["user_id"],
            "name": "Sample Plant",
            "species": "Sample Species",
            "access_granted": True
        }
        
        return plant_data


# Create instances for different access levels
require_plant_ownership = PlantAccessDependency(require_ownership=True)
allow_plant_viewing = PlantAccessDependency(require_ownership=False)