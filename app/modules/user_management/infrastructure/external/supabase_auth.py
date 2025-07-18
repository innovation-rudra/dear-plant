# app/modules/user_management/infrastructure/external/supabase_auth.py
"""
Plant Care Application - Supabase Authentication Integration

Supabase authentication service for the Plant Care Application.
Handles JWT validation, user creation/sync, OAuth integration, and session management.
"""

import jwt
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List, Tuple
from dataclasses import dataclass

import structlog
from supabase import Client

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.shared.config.supabase import get_supabase_client, get_supabase_auth
from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    AuthenticationError, ValidationError, BusinessLogicError, ConfigurationError
)
from app.shared.utils.helpers import PlantCareHelpers

# Setup logger
logger = structlog.get_logger(__name__)


@dataclass
class SupabaseUser:
    """Supabase user data structure."""
    id: str
    email: str
    email_verified: bool
    provider: str
    user_metadata: Dict[str, Any]
    app_metadata: Dict[str, Any]
    created_at: datetime
    updated_at: datetime
    last_sign_in_at: Optional[datetime] = None


class SupabaseAuthService:
    """
    Supabase authentication service for Plant Care Application.
    Handles authentication, user management, and JWT operations.
    """
    
    def __init__(self, user_repository: UserRepository):
        """
        Initialize Supabase auth service.
        
        Args:
            user_repository: User repository for database operations
        """
        self.user_repository = user_repository
        self.settings = get_settings()
        self.supabase_client = None
        self.supabase_auth = None
        self._jwt_secret = None
        
    async def _initialize_clients(self):
        """Initialize Supabase clients if not already done."""
        if not self.supabase_client:
            self.supabase_client = await get_supabase_client()
        if not self.supabase_auth:
            self.supabase_auth = await get_supabase_auth()
        if not self._jwt_secret:
            self._jwt_secret = self.settings.supabase_jwt_secret
    
    async def validate_jwt_token(self, token: str) -> Dict[str, Any]:
        """
        Validate JWT token from Supabase.
        
        Args:
            token: JWT token to validate
            
        Returns:
            Dict[str, Any]: Decoded token payload
            
        Raises:
            AuthenticationError: If token is invalid or expired
        """
        try:
            await self._initialize_clients()
            
            logger.debug("Validating JWT token")
            
            # Decode and validate JWT token
            payload = jwt.decode(
                token,
                self._jwt_secret,
                algorithms=["HS256"],
                audience="authenticated"
            )
            
            # Check token expiration
            exp = payload.get("exp")
            if exp and datetime.utcnow().timestamp() > exp:
                raise AuthenticationError("Token has expired")
            
            # Extract user information
            user_data = {
                "user_id": payload.get("sub"),
                "email": payload.get("email"),
                "email_verified": payload.get("email_confirmed_at") is not None,
                "provider": payload.get("app_metadata", {}).get("provider", "email"),
                "role": payload.get("role", "authenticated"),
                "aud": payload.get("aud"),
                "exp": exp,
                "iat": payload.get("iat"),
                "iss": payload.get("iss")
            }
            
            logger.debug("JWT token validated successfully", user_id=user_data["user_id"])
            
            return user_data
            
        except jwt.ExpiredSignatureError:
            logger.warning("JWT token expired")
            raise AuthenticationError("Token has expired")
        except jwt.InvalidTokenError as e:
            logger.warning("Invalid JWT token", error=str(e))
            raise AuthenticationError("Invalid token")
        except Exception as e:
            logger.error("JWT validation failed", error=str(e))
            raise AuthenticationError("Token validation failed")
    
    async def get_user_from_supabase(self, supabase_user_id: str) -> Optional[SupabaseUser]:
        """
        Get user data from Supabase.
        
        Args:
            supabase_user_id: Supabase user ID
            
        Returns:
            Optional[SupabaseUser]: Supabase user data if found
            
        Raises:
            AuthenticationError: If Supabase request fails
        """
        try:
            await self._initialize_clients()
            
            logger.debug("Getting user from Supabase", user_id=supabase_user_id)
            
            # Get user from Supabase Admin API
            response = self.supabase_client.auth.admin.get_user_by_id(supabase_user_id)
            
            if not response.user:
                return None
            
            supabase_user_data = response.user
            
            # Convert to our SupabaseUser structure
            supabase_user = SupabaseUser(
                id=supabase_user_data.id,
                email=supabase_user_data.email,
                email_verified=supabase_user_data.email_confirmed_at is not None,
                provider=supabase_user_data.app_metadata.get("provider", "email"),
                user_metadata=supabase_user_data.user_metadata or {},
                app_metadata=supabase_user_data.app_metadata or {},
                created_at=datetime.fromisoformat(supabase_user_data.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(supabase_user_data.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(supabase_user_data.last_sign_in_at.replace('Z', '+00:00')) if supabase_user_data.last_sign_in_at else None
            )
            
            logger.debug("User retrieved from Supabase", user_id=supabase_user_id)
            
            return supabase_user
            
        except Exception as e:
            logger.error("Failed to get user from Supabase", user_id=supabase_user_id, error=str(e))
            raise AuthenticationError(f"Failed to get user from Supabase: {str(e)}")
    
    async def create_user_in_supabase(self, email: str, password: str, 
                                    user_metadata: Optional[Dict[str, Any]] = None) -> SupabaseUser:
        """
        Create a new user in Supabase.
        
        Args:
            email: User email
            password: User password
            user_metadata: Additional user metadata
            
        Returns:
            SupabaseUser: Created user data
            
        Raises:
            AuthenticationError: If user creation fails
            ValidationError: If email already exists
        """
        try:
            await self._initialize_clients()
            
            logger.info("Creating user in Supabase", email=email)
            
            # Create user in Supabase
            response = self.supabase_client.auth.admin.create_user({
                "email": email,
                "password": password,
                "user_metadata": user_metadata or {},
                "email_confirm": False  # We'll handle email confirmation
            })
            
            if not response.user:
                raise AuthenticationError("Failed to create user in Supabase")
            
            supabase_user_data = response.user
            
            # Convert to our SupabaseUser structure
            supabase_user = SupabaseUser(
                id=supabase_user_data.id,
                email=supabase_user_data.email,
                email_verified=False,  # New users start unverified
                provider="email",
                user_metadata=supabase_user_data.user_metadata or {},
                app_metadata=supabase_user_data.app_metadata or {},
                created_at=datetime.fromisoformat(supabase_user_data.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(supabase_user_data.updated_at.replace('Z', '+00:00'))
            )
            
            logger.info("User created in Supabase", email=email, user_id=supabase_user.id)
            
            return supabase_user
            
        except Exception as e:
            logger.error("Failed to create user in Supabase", email=email, error=str(e))
            if "already been registered" in str(e):
                raise ValidationError("Email already exists")
            raise AuthenticationError(f"Failed to create user: {str(e)}")
    
    async def update_user_in_supabase(self, supabase_user_id: str, 
                                    updates: Dict[str, Any]) -> SupabaseUser:
        """
        Update user in Supabase.
        
        Args:
            supabase_user_id: Supabase user ID
            updates: Updates to apply
            
        Returns:
            SupabaseUser: Updated user data
            
        Raises:
            AuthenticationError: If update fails
        """
        try:
            await self._initialize_clients()
            
            logger.info("Updating user in Supabase", user_id=supabase_user_id)
            
            # Update user in Supabase
            response = self.supabase_client.auth.admin.update_user_by_id(
                supabase_user_id, 
                updates
            )
            
            if not response.user:
                raise AuthenticationError("Failed to update user in Supabase")
            
            supabase_user_data = response.user
            
            # Convert to our SupabaseUser structure
            supabase_user = SupabaseUser(
                id=supabase_user_data.id,
                email=supabase_user_data.email,
                email_verified=supabase_user_data.email_confirmed_at is not None,
                provider=supabase_user_data.app_metadata.get("provider", "email"),
                user_metadata=supabase_user_data.user_metadata or {},
                app_metadata=supabase_user_data.app_metadata or {},
                created_at=datetime.fromisoformat(supabase_user_data.created_at.replace('Z', '+00:00')),
                updated_at=datetime.fromisoformat(supabase_user_data.updated_at.replace('Z', '+00:00')),
                last_sign_in_at=datetime.fromisoformat(supabase_user_data.last_sign_in_at.replace('Z', '+00:00')) if supabase_user_data.last_sign_in_at else None
            )
            
            logger.info("User updated in Supabase", user_id=supabase_user_id)
            
            return supabase_user
            
        except Exception as e:
            logger.error("Failed to update user in Supabase", user_id=supabase_user_id, error=str(e))
            raise AuthenticationError(f"Failed to update user: {str(e)}")
    
    async def delete_user_in_supabase(self, supabase_user_id: str) -> bool:
        """
        Delete user from Supabase.
        
        Args:
            supabase_user_id: Supabase user ID
            
        Returns:
            bool: True if deletion successful
            
        Raises:
            AuthenticationError: If deletion fails
        """
        try:
            await self._initialize_clients()
            
            logger.warning("Deleting user from Supabase", user_id=supabase_user_id)
            
            # Delete user from Supabase
            self.supabase_client.auth.admin.delete_user(supabase_user_id)
            
            logger.warning("User deleted from Supabase", user_id=supabase_user_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to delete user from Supabase", user_id=supabase_user_id, error=str(e))
            raise AuthenticationError(f"Failed to delete user: {str(e)}")
    
    async def send_email_verification(self, email: str) -> bool:
        """
        Send email verification to user.
        
        Args:
            email: User email
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            AuthenticationError: If sending fails
        """
        try:
            await self._initialize_clients()
            
            logger.info("Sending email verification", email=email)
            
            # Send verification email via Supabase
            response = self.supabase_client.auth.resend({
                "type": "signup",
                "email": email
            })
            
            logger.info("Email verification sent", email=email)
            
            return True
            
        except Exception as e:
            logger.error("Failed to send email verification", email=email, error=str(e))
            raise AuthenticationError(f"Failed to send email verification: {str(e)}")
    
    async def send_password_reset(self, email: str) -> bool:
        """
        Send password reset email to user.
        
        Args:
            email: User email
            
        Returns:
            bool: True if email sent successfully
            
        Raises:
            AuthenticationError: If sending fails
        """
        try:
            await self._initialize_clients()
            
            logger.info("Sending password reset email", email=email)
            
            # Send password reset email via Supabase
            response = self.supabase_client.auth.reset_password_email(email)
            
            logger.info("Password reset email sent", email=email)
            
            return True
            
        except Exception as e:
            logger.error("Failed to send password reset email", email=email, error=str(e))
            raise AuthenticationError(f"Failed to send password reset: {str(e)}")
    
    async def verify_email_token(self, token: str, email: str) -> bool:
        """
        Verify email verification token.
        
        Args:
            token: Verification token
            email: User email
            
        Returns:
            bool: True if verification successful
            
        Raises:
            AuthenticationError: If verification fails
        """
        try:
            await self._initialize_clients()
            
            logger.info("Verifying email token", email=email)
            
            # Verify email with Supabase
            response = self.supabase_client.auth.verify_otp({
                "email": email,
                "token": token,
                "type": "signup"
            })
            
            if response.user:
                logger.info("Email verified successfully", email=email)
                return True
            else:
                logger.warning("Email verification failed", email=email)
                return False
            
        except Exception as e:
            logger.error("Email verification failed", email=email, error=str(e))
            raise AuthenticationError(f"Email verification failed: {str(e)}")
    
    async def sync_user_with_supabase(self, user: User) -> User:
        """
        Sync our local user with Supabase user data.
        
        Args:
            user: Local user to sync
            
        Returns:
            User: Updated user with synced data
            
        Raises:
            AuthenticationError: If sync fails
        """
        try:
            logger.info("Syncing user with Supabase", user_id=user.user_id)
            
            if not user.supabase_user_id:
                logger.warning("User has no Supabase ID, skipping sync", user_id=user.user_id)
                return user
            
            # Get latest data from Supabase
            supabase_user = await self.get_user_from_supabase(user.supabase_user_id)
            
            if not supabase_user:
                logger.warning("User not found in Supabase", 
                             user_id=user.user_id, 
                             supabase_id=user.supabase_user_id)
                return user
            
            # Update local user with Supabase data
            sync_needed = False
            
            # Sync email if different
            if user.email != supabase_user.email:
                user.email = supabase_user.email
                sync_needed = True
            
            # Sync email verification status
            if user.is_verified != supabase_user.email_verified:
                user.is_verified = supabase_user.email_verified
                if supabase_user.email_verified and not user.email_verified_at:
                    user.email_verified_at = datetime.utcnow()
                sync_needed = True
            
            # Sync provider if different
            if user.provider != supabase_user.provider:
                user.provider = supabase_user.provider
                sync_needed = True
            
            # Update last activity from Supabase last sign in
            if supabase_user.last_sign_in_at and (
                not user.last_login_at or 
                supabase_user.last_sign_in_at > user.last_login_at
            ):
                user.last_login_at = supabase_user.last_sign_in_at
                user.last_activity_at = supabase_user.last_sign_in_at
                sync_needed = True
            
            # Save updates if needed
            if sync_needed:
                user.updated_at = datetime.utcnow()
                updated_user = await self.user_repository.update(user)
                logger.info("User synced with Supabase", user_id=user.user_id)
                return updated_user
            
            logger.debug("User already in sync with Supabase", user_id=user.user_id)
            return user
            
        except Exception as e:
            logger.error("Failed to sync user with Supabase", user_id=user.user_id, error=str(e))
            # Don't raise exception for sync failures - return original user
            return user
    
    async def handle_oauth_callback(self, provider: str, 
                                  oauth_data: Dict[str, Any]) -> Tuple[SupabaseUser, bool]:
        """
        Handle OAuth callback from providers like Google, Apple, etc.
        
        Args:
            provider: OAuth provider (google, apple, facebook)
            oauth_data: OAuth response data
            
        Returns:
            Tuple[SupabaseUser, bool]: (supabase_user, is_new_user)
            
        Raises:
            AuthenticationError: If OAuth handling fails
        """
        try:
            logger.info("Handling OAuth callback", provider=provider)
            
            # Extract user data from OAuth response
            user_id = oauth_data.get("user", {}).get("id")
            email = oauth_data.get("user", {}).get("email")
            
            if not user_id or not email:
                raise AuthenticationError("Invalid OAuth response data")
            
            # Check if user already exists in Supabase
            existing_user = await self.get_user_from_supabase(user_id)
            
            if existing_user:
                logger.info("Existing OAuth user logged in", provider=provider, email=email)
                return existing_user, False
            
            # Create new user from OAuth data
            user_metadata = {
                "provider": provider,
                "full_name": oauth_data.get("user", {}).get("user_metadata", {}).get("full_name"),
                "avatar_url": oauth_data.get("user", {}).get("user_metadata", {}).get("avatar_url"),
                "provider_id": oauth_data.get("user", {}).get("user_metadata", {}).get("provider_id")
            }
            
            # Create Supabase user structure for OAuth user
            supabase_user = SupabaseUser(
                id=user_id,
                email=email,
                email_verified=True,  # OAuth users are pre-verified
                provider=provider,
                user_metadata=user_metadata,
                app_metadata={"provider": provider},
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            logger.info("New OAuth user created", provider=provider, email=email)
            
            return supabase_user, True
            
        except Exception as e:
            logger.error("OAuth callback handling failed", provider=provider, error=str(e))
            raise AuthenticationError(f"OAuth callback failed: {str(e)}")
    
    async def revoke_user_sessions(self, supabase_user_id: str) -> bool:
        """
        Revoke all sessions for a user in Supabase.
        
        Args:
            supabase_user_id: Supabase user ID
            
        Returns:
            bool: True if sessions revoked successfully
            
        Raises:
            AuthenticationError: If revocation fails
        """
        try:
            await self._initialize_clients()
            
            logger.info("Revoking user sessions", user_id=supabase_user_id)
            
            # Update user to force re-authentication
            await self.update_user_in_supabase(supabase_user_id, {
                "user_metadata": {"session_revoked_at": datetime.utcnow().isoformat()}
            })
            
            logger.info("User sessions revoked", user_id=supabase_user_id)
            
            return True
            
        except Exception as e:
            logger.error("Failed to revoke user sessions", user_id=supabase_user_id, error=str(e))
            raise AuthenticationError(f"Failed to revoke sessions: {str(e)}")
    
    async def get_user_sessions(self, supabase_user_id: str) -> List[Dict[str, Any]]:
        """
        Get active sessions for a user.
        
        Args:
            supabase_user_id: Supabase user ID
            
        Returns:
            List[Dict[str, Any]]: List of active sessions
            
        Raises:
            AuthenticationError: If getting sessions fails
        """
        try:
            await self._initialize_clients()
            
            # Note: Supabase doesn't provide direct session listing
            # This would typically be implemented with custom session tracking
            # For now, return basic session info from user metadata
            
            supabase_user = await self.get_user_from_supabase(supabase_user_id)
            
            if not supabase_user:
                return []
            
            # Return basic session info
            sessions = [{
                "session_id": PlantCareHelpers.generate_unique_id("session"),
                "created_at": supabase_user.created_at.isoformat(),
                "last_activity": supabase_user.last_sign_in_at.isoformat() if supabase_user.last_sign_in_at else None,
                "provider": supabase_user.provider,
                "is_active": True
            }]
            
            return sessions
            
        except Exception as e:
            logger.error("Failed to get user sessions", user_id=supabase_user_id, error=str(e))
            raise AuthenticationError(f"Failed to get sessions: {str(e)}")
    
    async def check_service_health(self) -> Dict[str, Any]:
        """
        Check Supabase service health.
        
        Returns:
            Dict[str, Any]: Health status information
        """
        try:
            await self._initialize_clients()
            
            # Test basic connectivity
            start_time = datetime.utcnow()
            
            # Simple health check - try to get service info
            response = self.supabase_client.auth.get_settings()
            
            end_time = datetime.utcnow()
            response_time = (end_time - start_time).total_seconds() * 1000
            
            return {
                "service": "supabase_auth",
                "status": "healthy",
                "response_time_ms": round(response_time, 2),
                "timestamp": datetime.utcnow().isoformat(),
                "version": "1.0.0"
            }
            
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return {
                "service": "supabase_auth",
                "status": "unhealthy",
                "error": str(e),
                "timestamp": datetime.utcnow().isoformat()
            }


# Factory function for dependency injection
def create_supabase_auth_service(user_repository: UserRepository) -> SupabaseAuthService:
    """Create Supabase authentication service instance."""
    return SupabaseAuthService(user_repository)