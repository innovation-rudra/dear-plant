# app/modules/user_management/domain/services/auth_service.py
"""
Plant Care Application - Authentication Domain Service

Authentication business logic for the Plant Care Application.
Handles login, logout, token management, and session tracking with Supabase integration.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, Tuple, List

import structlog

from app.modules.user_management.domain.models.user import User, UserStatus, UserRole
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.domain.events.user_events import (
    UserLastLoginUpdated, UserLoggedOut, UserSessionRefreshed
)
from app.shared.events.base import EventPublisher
from app.shared.core.exceptions import (
    AuthenticationError, ValidationError, ResourceNotFoundError,
    BusinessLogicError, AuthorizationError
)

# Setup logger
logger = structlog.get_logger(__name__)


class AuthenticationService:
    """
    Domain service for authentication in Plant Care Application.
    Handles login, logout, session management, and security validation.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 event_publisher: EventPublisher):
        """
        Initialize authentication service.
        
        Args:
            user_repository: User data repository
            event_publisher: Event publisher for domain events
        """
        self.user_repository = user_repository
        self.event_publisher = event_publisher
        self.session_timeout_hours = 24  # 24 hours session timeout
        self.max_failed_attempts = 5  # Max failed login attempts
    
    async def authenticate_user(self, 
                               email: str, 
                               supabase_user_id: str,
                               login_source: str = "web",
                               ip_address: Optional[str] = None,
                               user_agent: Optional[str] = None) -> Tuple[User, Dict[str, Any]]:
        """
        Authenticate user for Plant Care Application.
        
        Args:
            email: User email address
            supabase_user_id: Supabase user ID from JWT
            login_source: Source of login (web, mobile, api)
            ip_address: User's IP address
            user_agent: User's browser/app information
            
        Returns:
            Tuple[User, Dict[str, Any]]: (authenticated_user, session_data)
            
        Raises:
            AuthenticationError: If authentication fails
            ResourceNotFoundError: If user not found
            BusinessLogicError: If user cannot login
        """
        try:
            logger.info("Authenticating user", email=email, source=login_source)
            
            # Find user by email or supabase ID
            user = await self._find_user_for_authentication(email, supabase_user_id)
            
            # Validate user can login
            await self._validate_user_login(user)
            
            # Update last login
            await self._update_last_login(user, login_source, ip_address, user_agent)
            
            # Generate session data
            session_data = await self._create_session_data(user, login_source, ip_address)
            
            logger.info("User authenticated successfully", 
                       user_id=user.user_id, 
                       email=email)
            
            return user, session_data
            
        except Exception as e:
            logger.error("Authentication failed", email=email, error=str(e))
            raise
    
    async def validate_session(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Validate user session for Plant Care Application.
        
        Args:
            user_id: User ID from session
            session_data: Session data to validate
            
        Returns:
            bool: True if session is valid
            
        Raises:
            AuthenticationError: If session is invalid
        """
        try:
            logger.debug("Validating session", user_id=user_id)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise AuthenticationError("Invalid session: user not found")
            
            # Validate user is still active
            if not user.is_active():
                raise AuthenticationError("Invalid session: user is not active")
            
            # Validate session expiry
            if not self._is_session_valid(session_data):
                raise AuthenticationError("Session expired")
            
            # Validate session integrity
            if not self._validate_session_integrity(user, session_data):
                raise AuthenticationError("Invalid session data")
            
            return True
            
        except Exception as e:
            logger.warning("Session validation failed", user_id=user_id, error=str(e))
            raise
    
    async def refresh_session(self, user_id: str, current_session: Dict[str, Any]) -> Dict[str, Any]:
        """
        Refresh user session.
        
        Args:
            user_id: User ID
            current_session: Current session data
            
        Returns:
            Dict[str, Any]: New session data
            
        Raises:
            AuthenticationError: If session cannot be refreshed
        """
        try:
            logger.info("Refreshing session", user_id=user_id)
            
            # Validate current session
            await self.validate_session(user_id, current_session)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found for session refresh")
            
            # Create new session data
            new_session = await self._create_session_data(
                user, 
                current_session.get("login_source", "web"),
                current_session.get("ip_address")
            )
            
            # Publish session refreshed event
            await self.event_publisher.publish(
                UserSessionRefreshed(
                    user_id=user.user_id,
                    email=user.email,
                    session_id=new_session["session_id"],
                    refreshed_at=datetime.utcnow(),
                    login_source=current_session.get("login_source", "web")
                )
            )
            
            logger.info("Session refreshed successfully", user_id=user_id)
            
            return new_session
            
        except Exception as e:
            logger.error("Session refresh failed", user_id=user_id, error=str(e))
            raise
    
    async def logout_user(self, user_id: str, session_data: Dict[str, Any]) -> bool:
        """
        Logout user and invalidate session.
        
        Args:
            user_id: User ID
            session_data: Session data to invalidate
            
        Returns:
            bool: True if logout successful
        """
        try:
            logger.info("Logging out user", user_id=user_id)
            
            # Get user
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                logger.warning("User not found during logout", user_id=user_id)
                return True  # Return true even if user not found
            
            # Update user's last activity and logout time
            user.last_activity_at = datetime.utcnow()
            await self.user_repository.update(user)
            
            # Publish logout event
            await self.event_publisher.publish(
                UserLoggedOut(
                    user_id=user.user_id,
                    email=user.email,
                    session_id=session_data.get("session_id"),
                    logged_out_at=datetime.utcnow(),
                    login_source=session_data.get("login_source", "web")
                )
            )
            
            logger.info("User logged out successfully", user_id=user_id)
            
            return True
            
        except Exception as e:
            logger.error("Logout failed", user_id=user_id, error=str(e))
            # Don't raise exception for logout - return false instead
            return False
    
    async def validate_user_permissions(self, user_id: str, required_permission: str) -> bool:
        """
        Validate user has required permissions for Plant Care features.
        
        Args:
            user_id: User ID
            required_permission: Required permission (e.g., 'premium_features', 'expert_access')
            
        Returns:
            bool: True if user has permission
            
        Raises:
            AuthenticationError: If user not found
            AuthorizationError: If user lacks permission
        """
        try:
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found for permission check")
            
            # Check basic permissions based on user role and subscription
            has_permission = await self._check_user_permission(user, required_permission)
            
            if not has_permission:
                raise AuthorizationError(f"User lacks required permission: {required_permission}")
            
            return True
            
        except (AuthenticationError, AuthorizationError):
            raise
        except Exception as e:
            logger.error("Permission validation failed", 
                        user_id=user_id, 
                        permission=required_permission, 
                        error=str(e))
            raise AuthorizationError("Permission validation failed")
    
    async def get_user_context(self, user_id: str) -> Dict[str, Any]:
        """
        Get user context for Plant Care Application features.
        
        Args:
            user_id: User ID
            
        Returns:
            Dict[str, Any]: User context data
            
        Raises:
            AuthenticationError: If user not found
        """
        try:
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise AuthenticationError("User not found")
            
            # Build user context
            context = {
                "user_id": user.user_id,
                "email": user.email,
                "role": user.role.value,
                "status": user.status.value,
                "is_active": user.is_active(),
                "is_verified": user.is_verified,
                "plant_limit": user.plant_limit,
                "created_at": user.created_at.isoformat(),
                "last_login_at": user.last_login_at.isoformat() if user.last_login_at else None,
                "subscription": {
                    "has_premium": user.has_premium_features(),
                    "is_expert": user.role == UserRole.EXPERT,
                    "is_admin": user.role == UserRole.ADMIN
                },
                "permissions": await self._get_user_permissions(user)
            }
            
            return context
            
        except AuthenticationError:
            raise
        except Exception as e:
            logger.error("Failed to get user context", user_id=user_id, error=str(e))
            raise AuthenticationError("Failed to get user context")
    
    # Private helper methods
    
    async def _find_user_for_authentication(self, email: str, supabase_user_id: str) -> User:
        """Find user for authentication by email or Supabase ID."""
        # Try to find by Supabase ID first
        user = await self.user_repository.find_by_supabase_id(supabase_user_id)
        
        if not user:
            # Try to find by email
            user = await self.user_repository.find_by_email(email)
            
            if user and not user.supabase_user_id:
                # Link Supabase ID to existing user
                user.supabase_user_id = supabase_user_id
                await self.user_repository.update(user)
        
        if not user:
            raise ResourceNotFoundError(f"User not found: {email}")
        
        return user
    
    async def _validate_user_login(self, user: User) -> None:
        """Validate user can login."""
        if not user.is_active():
            if user.status == UserStatus.SUSPENDED:
                raise BusinessLogicError("Account is suspended")
            elif user.status == UserStatus.DELETED:
                raise BusinessLogicError("Account has been deleted")
            else:
                raise BusinessLogicError("Account is not active")
        
        if not user.is_verified:
            raise BusinessLogicError("Email not verified")
        
        # Check for failed login attempts (if tracking)
        failed_attempts = getattr(user, 'failed_login_attempts', 0)
        if failed_attempts >= self.max_failed_attempts:
            raise BusinessLogicError("Account locked due to too many failed attempts")
    
    async def _update_last_login(self, user: User, login_source: str, 
                               ip_address: Optional[str], user_agent: Optional[str]) -> None:
        """Update user's last login information."""
        now = datetime.utcnow()
        user.last_login_at = now
        user.last_activity_at = now
        
        # Reset failed login attempts on successful login
        if hasattr(user, 'failed_login_attempts'):
            user.failed_login_attempts = 0
        
        await self.user_repository.update(user)
        
        # Publish login event
        await self.event_publisher.publish(
            UserLastLoginUpdated(
                user_id=user.user_id,
                email=user.email,
                last_login_at=now,
                login_source=login_source,
                ip_address=ip_address,
                user_agent=user_agent
            )
        )
    
    async def _create_session_data(self, user: User, login_source: str, 
                                 ip_address: Optional[str]) -> Dict[str, Any]:
        """Create session data for authenticated user."""
        session_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(hours=self.session_timeout_hours)
        
        return {
            "session_id": session_id,
            "user_id": user.user_id,
            "email": user.email,
            "role": user.role.value,
            "login_source": login_source,
            "ip_address": ip_address,
            "created_at": datetime.utcnow().isoformat(),
            "expires_at": expires_at.isoformat(),
            "is_premium": user.has_premium_features(),
            "plant_limit": user.plant_limit
        }
    
    def _is_session_valid(self, session_data: Dict[str, Any]) -> bool:
        """Check if session is still valid (not expired)."""
        try:
            expires_at_str = session_data.get("expires_at")
            if not expires_at_str:
                return False
            
            expires_at = datetime.fromisoformat(expires_at_str.replace('Z', '+00:00'))
            return datetime.utcnow() < expires_at.replace(tzinfo=None)
            
        except (ValueError, AttributeError):
            return False
    
    def _validate_session_integrity(self, user: User, session_data: Dict[str, Any]) -> bool:
        """Validate session data integrity."""
        try:
            # Check user ID matches
            if session_data.get("user_id") != user.user_id:
                return False
            
            # Check email matches
            if session_data.get("email") != user.email:
                return False
            
            # Check role matches
            if session_data.get("role") != user.role.value:
                return False
            
            return True
            
        except (KeyError, AttributeError):
            return False
    
    async def _check_user_permission(self, user: User, permission: str) -> bool:
        """Check if user has specific permission."""
        # Basic Plant Care permissions based on role and subscription
        permission_map = {
            "basic_features": True,  # All users have basic features
            "premium_features": user.has_premium_features(),
            "expert_access": user.role in [UserRole.EXPERT, UserRole.ADMIN],
            "admin_access": user.role == UserRole.ADMIN,
            "community_post": user.is_active(),
            "ai_features": user.has_premium_features(),
            "unlimited_plants": user.has_premium_features(),
            "advanced_analytics": user.has_premium_features(),
            "export_data": user.has_premium_features(),
            "family_sharing": user.has_premium_features()
        }
        
        return permission_map.get(permission, False)
    
    async def _get_user_permissions(self, user: User) -> List[str]:
        """Get list of user permissions."""
        permissions = ["basic_features"]
        
        if user.has_premium_features():
            permissions.extend([
                "premium_features", "ai_features", "unlimited_plants",
                "advanced_analytics", "export_data", "family_sharing"
            ])
        
        if user.role == UserRole.EXPERT:
            permissions.extend(["expert_access", "community_moderation"])
        
        if user.role == UserRole.ADMIN:
            permissions.extend(["admin_access", "user_management", "system_settings"])
        
        if user.is_active():
            permissions.append("community_post")
        
        return permissions


# Convenience functions for dependency injection
def create_authentication_service(user_repository: UserRepository, 
                                event_publisher: EventPublisher) -> AuthenticationService:
    """Create authentication service instance."""
    return AuthenticationService(user_repository, event_publisher)