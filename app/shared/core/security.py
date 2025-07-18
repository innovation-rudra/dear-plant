"""
app/shared/core/security.py
Plant Care Application - Security Utilities

Security utilities for JWT validation, password hashing, encryption, and access control.
Integrates with Supabase Auth and provides Plant Care specific security features.
"""
import secrets
import hashlib
import hmac
import base64
from typing import Any, Dict, List, Optional, Union
from datetime import datetime, timedelta
import re

from jose import JWTError, jwt
from passlib.context import CryptContext
from passlib.hash import bcrypt
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    AuthenticationError,
    AuthorizationError,
    TokenExpiredError,
    InvalidTokenError,
    ValidationError,
)
from app.shared.utils.logging import log_security_event

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)

# Password hashing context
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


class PlantCareSecurityManager:
    """
    Security manager for Plant Care Application.
    Handles JWT validation, password security, and access control.
    """
    
    def __init__(self):
        self.jwt_secret = settings.SUPABASE_JWT_SECRET
        self.algorithm = settings.JWT_ALGORITHM
        self.access_token_expire = settings.ACCESS_TOKEN_EXPIRE_MINUTES
        self.refresh_token_expire = settings.REFRESH_TOKEN_EXPIRE_MINUTES
        
        # Plant Care specific security policies
        self.password_policy = {
            "min_length": settings.PASSWORD_MIN_LENGTH,
            "require_uppercase": settings.PASSWORD_REQUIRE_UPPERCASE,
            "require_lowercase": settings.PASSWORD_REQUIRE_LOWERCASE,
            "require_numbers": settings.PASSWORD_REQUIRE_NUMBERS,
            "require_symbols": settings.PASSWORD_REQUIRE_SYMBOLS,
            "forbidden_patterns": [
                "password", "plant", "care", "garden", "123456", "qwerty",
                "admin", "user", "root", "test"
            ]
        }
        
        # Role-based permissions for Plant Care features
        self.permissions = {
            "user": {
                "plants": ["read", "create", "update", "delete"],
                "care": ["read", "create", "update", "delete"],
                "growth": ["read", "create", "update"],
                "community": ["read", "create"],
                "notifications": ["read", "update"],
                "profile": ["read", "update"]
            },
            "premium_user": {
                "plants": ["read", "create", "update", "delete"],
                "care": ["read", "create", "update", "delete"],
                "growth": ["read", "create", "update", "delete"],
                "health": ["read", "create", "update", "delete"],
                "community": ["read", "create", "update", "delete"],
                "ai_features": ["read", "create"],
                "analytics": ["read"],
                "family_sharing": ["read", "create", "update", "delete"],
                "notifications": ["read", "update", "create"],
                "profile": ["read", "update"]
            },
            "expert": {
                "plants": ["read", "create", "update"],
                "care": ["read", "create", "update"],
                "community": ["read", "create", "update", "moderate"],
                "expert_advice": ["read", "create", "update"],
                "content": ["read", "create", "update"],
                "profile": ["read", "update"]
            },
            "admin": {
                "plants": ["read", "create", "update", "delete"],
                "users": ["read", "create", "update", "delete"],
                "community": ["read", "create", "update", "delete", "moderate"],
                "content": ["read", "create", "update", "delete"],
                "analytics": ["read", "create", "update"],
                "system": ["read", "create", "update", "delete"],
                "profile": ["read", "update"]
            }
        }
    
    def validate_supabase_jwt(self, token: str) -> Dict[str, Any]:
        """
        Validate Supabase JWT token.
        
        Args:
            token: JWT token string
            
        Returns:
            Dict: Decoded token payload
            
        Raises:
            InvalidTokenError: If token is invalid
            TokenExpiredError: If token is expired
        """
        try:
            # Decode and verify JWT
            payload = jwt.decode(
                token,
                self.jwt_secret,
                algorithms=[self.algorithm],
                options={"verify_aud": False}  # Supabase handles audience verification
            )
            
            # Check expiration
            exp = payload.get("exp")
            if exp and datetime.utcfromtimestamp(exp) < datetime.utcnow():
                raise TokenExpiredError("JWT token has expired")
            
            # Validate required fields for Plant Care
            required_fields = ["sub", "email", "role"]
            for field in required_fields:
                if field not in payload:
                    logger.warning(f"Missing required field in JWT: {field}")
            
            # Log successful token validation
            log_security_event(
                event_type="jwt_validated",
                user_id=payload.get("sub"),
                token_type="access",
                success=True
            )
            
            return payload
            
        except JWTError as e:
            log_security_event(
                event_type="jwt_validation_failed",
                error=str(e),
                token_preview=token[:20] + "..." if len(token) > 20 else token
            )
            raise InvalidTokenError(f"Invalid JWT token: {str(e)}")
        
        except Exception as e:
            logger.error("Unexpected error validating JWT", error=str(e))
            raise InvalidTokenError("Token validation failed")
    
    def validate_plant_care_permissions(
        self,
        user_role: str,
        resource: str,
        action: str,
        user_id: str,
        resource_owner_id: Optional[str] = None
    ) -> bool:
        """
        Validate user permissions for Plant Care resources.
        
        Args:
            user_role: User's role (user, premium_user, expert, admin)
            resource: Resource type (plants, care, community, etc.)
            action: Action to perform (read, create, update, delete)
            user_id: User ID performing the action
            resource_owner_id: Owner of the resource (for ownership checks)
            
        Returns:
            bool: True if action is permitted
        """
        try:
            # Get role permissions
            role_permissions = self.permissions.get(user_role, {})
            resource_permissions = role_permissions.get(resource, [])
            
            # Check if action is permitted for this role
            if action not in resource_permissions:
                log_security_event(
                    event_type="permission_denied",
                    user_id=user_id,
                    user_role=user_role,
                    resource=resource,
                    action=action,
                    reason="action_not_permitted"
                )
                return False
            
            # For personal resources, check ownership
            if resource in ["plants", "care", "growth", "notifications", "profile"]:
                if resource_owner_id and resource_owner_id != user_id:
                    # Only admins can access other users' personal resources
                    if user_role != "admin":
                        log_security_event(
                            event_type="permission_denied",
                            user_id=user_id,
                            user_role=user_role,
                            resource=resource,
                            action=action,
                            resource_owner=resource_owner_id,
                            reason="ownership_violation"
                        )
                        return False
            
            # Special checks for premium features
            if resource in ["ai_features", "analytics", "family_sharing"]:
                if user_role not in ["premium_user", "expert", "admin"]:
                    log_security_event(
                        event_type="permission_denied",
                        user_id=user_id,
                        user_role=user_role,
                        resource=resource,
                        action=action,
                        reason="premium_feature_required"
                    )
                    return False
            
            return True
            
        except Exception as e:
            logger.error(
                "Error validating permissions",
                user_id=user_id,
                resource=resource,
                action=action,
                error=str(e)
            )
            return False
    
    def validate_password_strength(self, password: str) -> bool:
        """
        Validate password strength for Plant Care users.
        
        Args:
            password: Password to validate
            
        Returns:
            bool: True if password meets requirements
            
        Raises:
            ValidationError: If password doesn't meet requirements
        """
        errors = []
        
        # Check minimum length
        if len(password) < self.password_policy["min_length"]:
            errors.append(f"Password must be at least {self.password_policy['min_length']} characters long")
        
        # Check uppercase requirement
        if self.password_policy["require_uppercase"] and not re.search(r'[A-Z]', password):
            errors.append("Password must contain at least one uppercase letter")
        
        # Check lowercase requirement
        if self.password_policy["require_lowercase"] and not re.search(r'[a-z]', password):
            errors.append("Password must contain at least one lowercase letter")
        
        # Check numbers requirement
        if self.password_policy["require_numbers"] and not re.search(r'\d', password):
            errors.append("Password must contain at least one number")
        
        # Check symbols requirement
        if self.password_policy["require_symbols"] and not re.search(r'[!@#$%^&*(),.?":{}|<>]', password):
            errors.append("Password must contain at least one special character")
        
        # Check forbidden patterns
        password_lower = password.lower()
        for pattern in self.password_policy["forbidden_patterns"]:
            if pattern in password_lower:
                errors.append(f"Password cannot contain common words like '{pattern}'")
        
        # Check for sequential characters
        if self._has_sequential_chars(password):
            errors.append("Password cannot contain sequential characters (123, abc, etc.)")
        
        if errors:
            log_security_event(
                event_type="weak_password_attempt",
                errors=errors,
                password_length=len(password)
            )
            raise ValidationError(
                message="Password does not meet security requirements",
                details={"errors": errors}
            )
        
        return True
    
    def _has_sequential_chars(self, password: str) -> bool:
        """Check for sequential characters in password."""
        for i in range(len(password) - 2):
            # Check for ascending sequence
            if (ord(password[i]) + 1 == ord(password[i + 1]) and 
                ord(password[i + 1]) + 1 == ord(password[i + 2])):
                return True
            # Check for descending sequence
            if (ord(password[i]) - 1 == ord(password[i + 1]) and 
                ord(password[i + 1]) - 1 == ord(password[i + 2])):
                return True
        return False
    
    def hash_password(self, password: str) -> str:
        """
        Hash password using bcrypt.
        
        Args:
            password: Plain text password
            
        Returns:
            str: Hashed password
        """
        # Validate password strength first
        self.validate_password_strength(password)
        
        # Hash password
        hashed = pwd_context.hash(password)
        
        log_security_event(
            event_type="password_hashed",
            password_length=len(password)
        )
        
        return hashed
    
    def verify_password(self, plain_password: str, hashed_password: str) -> bool:
        """
        Verify password against hash.
        
        Args:
            plain_password: Plain text password
            hashed_password: Hashed password
            
        Returns:
            bool: True if password matches
        """
        try:
            result = pwd_context.verify(plain_password, hashed_password)
            
            log_security_event(
                event_type="password_verification",
                success=result
            )
            
            return result
            
        except Exception as e:
            logger.error("Password verification error", error=str(e))
            return False
    
    def generate_secure_token(self, length: int = 32) -> str:
        """
        Generate secure random token.
        
        Args:
            length: Token length
            
        Returns:
            str: Secure random token
        """
        return secrets.token_urlsafe(length)
    
    def generate_api_key(self, user_id: str, purpose: str = "general") -> str:
        """
        Generate API key for Plant Care integrations.
        
        Args:
            user_id: User ID
            purpose: API key purpose
            
        Returns:
            str: API key
        """
        # Create API key with timestamp and user info
        timestamp = int(datetime.utcnow().timestamp())
        key_data = f"{user_id}:{purpose}:{timestamp}:{secrets.token_hex(16)}"
        
        # Hash the key data
        api_key = hashlib.sha256(key_data.encode()).hexdigest()
        
        log_security_event(
            event_type="api_key_generated",
            user_id=user_id,
            purpose=purpose,
            timestamp=timestamp
        )
        
        return f"pc_{api_key[:32]}"  # Plant Care prefix
    
    def validate_api_key(self, api_key: str, user_id: str) -> bool:
        """
        Validate API key for Plant Care integrations.
        
        Args:
            api_key: API key to validate
            user_id: Expected user ID
            
        Returns:
            bool: True if valid
        """
        if not api_key.startswith("pc_"):
            return False
        
        # In production, this would validate against database
        # For now, just check format
        return len(api_key) == 35  # pc_ + 32 chars
    
    def encrypt_sensitive_data(self, data: str, user_id: str) -> str:
        """
        Encrypt sensitive data for storage.
        
        Args:
            data: Data to encrypt
            user_id: User ID for key derivation
            
        Returns:
            str: Encrypted data (base64 encoded)
        """
        try:
            # Derive key from user ID and secret
            key = hashlib.pbkdf2_hmac(
                'sha256',
                user_id.encode(),
                settings.ENCRYPTION_SALT.encode(),
                100000  # iterations
            )[:32]  # 256-bit key
            
            # Simple XOR encryption (in production, use proper encryption like AES)
            encrypted = bytes(a ^ b for a, b in zip(data.encode(), (key * (len(data) // 32 + 1))[:len(data)]))
            
            return base64.b64encode(encrypted).decode()
            
        except Exception as e:
            logger.error("Encryption error", error=str(e))
            raise
    
    def decrypt_sensitive_data(self, encrypted_data: str, user_id: str) -> str:
        """
        Decrypt sensitive data.
        
        Args:
            encrypted_data: Encrypted data (base64 encoded)
            user_id: User ID for key derivation
            
        Returns:
            str: Decrypted data
        """
        try:
            # Derive same key
            key = hashlib.pbkdf2_hmac(
                'sha256',
                user_id.encode(),
                settings.ENCRYPTION_SALT.encode(),
                100000
            )[:32]
            
            # Decode and decrypt
            encrypted = base64.b64decode(encrypted_data.encode())
            decrypted = bytes(a ^ b for a, b in zip(encrypted, (key * (len(encrypted) // 32 + 1))[:len(encrypted)]))
            
            return decrypted.decode()
            
        except Exception as e:
            logger.error("Decryption error", error=str(e))
            raise
    
    def generate_csrf_token(self, user_id: str) -> str:
        """
        Generate CSRF token for forms.
        
        Args:
            user_id: User ID
            
        Returns:
            str: CSRF token
        """
        timestamp = str(int(datetime.utcnow().timestamp()))
        message = f"{user_id}:{timestamp}"
        signature = hmac.new(
            settings.SECRET_KEY.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return base64.b64encode(f"{message}:{signature}".encode()).decode()
    
    def validate_csrf_token(self, token: str, user_id: str, max_age: int = 3600) -> bool:
        """
        Validate CSRF token.
        
        Args:
            token: CSRF token
            user_id: User ID
            max_age: Maximum token age in seconds
            
        Returns:
            bool: True if valid
        """
        try:
            decoded = base64.b64decode(token.encode()).decode()
            parts = decoded.split(':')
            
            if len(parts) != 3:
                return False
            
            token_user_id, timestamp, signature = parts
            
            # Validate user ID
            if token_user_id != user_id:
                return False
            
            # Validate timestamp
            token_time = int(timestamp)
            if datetime.utcnow().timestamp() - token_time > max_age:
                return False
            
            # Validate signature
            message = f"{token_user_id}:{timestamp}"
            expected_signature = hmac.new(
                settings.SECRET_KEY.encode(),
                message.encode(),
                hashlib.sha256
            ).hexdigest()
            
            return hmac.compare_digest(signature, expected_signature)
            
        except Exception:
            return False


# Global security manager instance
security_manager = PlantCareSecurityManager()


# Convenience functions
def validate_jwt_token(token: str) -> Dict[str, Any]:
    """Validate JWT token."""
    return security_manager.validate_supabase_jwt(token)


def check_permissions(
    user_role: str,
    resource: str,
    action: str,
    user_id: str,
    resource_owner_id: Optional[str] = None
) -> bool:
    """Check user permissions."""
    return security_manager.validate_plant_care_permissions(
        user_role, resource, action, user_id, resource_owner_id
    )


def hash_password(password: str) -> str:
    """Hash password."""
    return security_manager.hash_password(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verify password."""
    return security_manager.verify_password(plain_password, hashed_password)


def generate_secure_token(length: int = 32) -> str:
    """Generate secure token."""
    return security_manager.generate_secure_token(length)


def generate_plant_care_api_key(user_id: str, purpose: str = "general") -> str:
    """Generate Plant Care API key."""
    return security_manager.generate_api_key(user_id, purpose)


def encrypt_user_data(data: str, user_id: str) -> str:
    """Encrypt sensitive user data."""
    return security_manager.encrypt_sensitive_data(data, user_id)


def decrypt_user_data(encrypted_data: str, user_id: str) -> str:
    """Decrypt sensitive user data."""
    return security_manager.decrypt_sensitive_data(encrypted_data, user_id)