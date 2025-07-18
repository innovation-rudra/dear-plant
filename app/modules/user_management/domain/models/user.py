# app/modules/user_management/domain/models/user.py
"""
Plant Care Application - User Domain Model

Core user entity for the Plant Care Application.
Represents the fundamental user concept with authentication and basic information.
Integrates with Supabase Auth while maintaining domain logic independence.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any
from dataclasses import dataclass, field

import structlog

# Setup logger
logger = structlog.get_logger(__name__)


class UserRole(str, Enum):
    """
    User roles in the Plant Care Application.
    Defines permission levels and feature access.
    """
    USER = "user"              # Basic plant care features
    PREMIUM = "premium"        # Advanced features, unlimited plants
    EXPERT = "expert"          # Community expert, can provide advice
    ADMIN = "admin"            # Administrative access


class UserStatus(str, Enum):
    """
    User account status in the Plant Care Application.
    """
    ACTIVE = "active"          # Normal active user
    INACTIVE = "inactive"      # Temporarily deactivated
    SUSPENDED = "suspended"    # Suspended for violations
    PENDING = "pending"        # Pending email verification
    DELETED = "deleted"        # Soft deleted account


@dataclass
class User:
    """
    Core User domain entity for Plant Care Application.
    
    Represents a user in the system with authentication information,
    basic profile data, and Plant Care specific attributes.
    """
    
    # Identity
    user_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    email: str = ""
    
    # Authentication (Supabase Integration)
    supabase_user_id: Optional[str] = None
    email_verified: bool = False
    phone: Optional[str] = None
    phone_verified: bool = False
    
    # User Status
    role: UserRole = UserRole.USER
    status: UserStatus = UserStatus.PENDING
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    last_login_at: Optional[datetime] = None
    email_confirmed_at: Optional[datetime] = None
    
    # Plant Care Specific
    plant_count: int = 0
    subscription_tier: str = "free"
    is_premium: bool = False
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation and setup."""
        self._validate_email()
        self._validate_user_id()
        
    def _validate_email(self) -> None:
        """Validate email format."""
        if not self.email:
            raise ValueError("Email is required")
        
        # Basic email validation
        if "@" not in self.email or "." not in self.email.split("@")[1]:
            raise ValueError("Invalid email format")
    
    def _validate_user_id(self) -> None:
        """Validate user ID format."""
        if not self.user_id:
            raise ValueError("User ID is required")
        
        try:
            uuid.UUID(self.user_id)
        except ValueError:
            raise ValueError("Invalid user ID format")
    
    def activate(self) -> None:
        """
        Activate user account.
        Business rule: User must be verified before activation.
        """
        if not self.email_verified:
            raise ValueError("Cannot activate user without email verification")
        
        self.status = UserStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        
        logger.info("User activated", user_id=self.user_id, email=self.email)
    
    def deactivate(self, reason: Optional[str] = None) -> None:
        """
        Deactivate user account.
        
        Args:
            reason: Optional reason for deactivation
        """
        self.status = UserStatus.INACTIVE
        self.updated_at = datetime.utcnow()
        
        if reason:
            self.metadata["deactivation_reason"] = reason
            self.metadata["deactivated_at"] = datetime.utcnow().isoformat()
        
        logger.info("User deactivated", user_id=self.user_id, reason=reason)
    
    def suspend(self, reason: str, suspended_until: Optional[datetime] = None) -> None:
        """
        Suspend user account for violations.
        
        Args:
            reason: Reason for suspension
            suspended_until: Optional end date for suspension
        """
        if not reason:
            raise ValueError("Suspension reason is required")
        
        self.status = UserStatus.SUSPENDED
        self.updated_at = datetime.utcnow()
        
        self.metadata["suspension_reason"] = reason
        self.metadata["suspended_at"] = datetime.utcnow().isoformat()
        if suspended_until:
            self.metadata["suspended_until"] = suspended_until.isoformat()
        
        logger.warning("User suspended", user_id=self.user_id, reason=reason)
    
    def verify_email(self) -> None:
        """
        Mark email as verified.
        Business rule: Sets email_confirmed_at timestamp.
        """
        self.email_verified = True
        self.email_confirmed_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
        
        # Auto-activate if pending
        if self.status == UserStatus.PENDING:
            self.status = UserStatus.ACTIVE
        
        logger.info("Email verified", user_id=self.user_id, email=self.email)
    
    def update_last_login(self) -> None:
        """Update last login timestamp."""
        self.last_login_at = datetime.utcnow()
        self.updated_at = datetime.utcnow()
    
    def upgrade_to_premium(self) -> None:
        """
        Upgrade user to premium tier.
        Business rule: Premium users get enhanced Plant Care features.
        """
        if self.status != UserStatus.ACTIVE:
            raise ValueError("Cannot upgrade inactive user to premium")
        
        self.role = UserRole.PREMIUM
        self.subscription_tier = "premium"
        self.is_premium = True
        self.updated_at = datetime.utcnow()
        
        logger.info("User upgraded to premium", user_id=self.user_id)
    
    def downgrade_from_premium(self) -> None:
        """
        Downgrade user from premium tier.
        Business rule: Must handle plant count limits for free tier.
        """
        self.role = UserRole.USER
        self.subscription_tier = "free"
        self.is_premium = False
        self.updated_at = datetime.utcnow()
        
        # Note: Plant count enforcement handled by plant management module
        logger.info("User downgraded from premium", user_id=self.user_id)
    
    def promote_to_expert(self) -> None:
        """
        Promote user to expert role.
        Business rule: Experts can provide plant care advice in community.
        """
        if self.status != UserStatus.ACTIVE:
            raise ValueError("Cannot promote inactive user to expert")
        
        self.role = UserRole.EXPERT
        self.updated_at = datetime.utcnow()
        
        logger.info("User promoted to expert", user_id=self.user_id)
    
    def update_plant_count(self, count: int) -> None:
        """
        Update user's plant count.
        Business rule: Free users limited to 5 plants.
        
        Args:
            count: New plant count
        """
        if count < 0:
            raise ValueError("Plant count cannot be negative")
        
        # Enforce free tier limits
        if not self.is_premium and count > 5:
            raise ValueError("Free tier limited to 5 plants. Upgrade to premium for unlimited plants.")
        
        self.plant_count = count
        self.updated_at = datetime.utcnow()
    
    def can_add_plant(self) -> bool:
        """
        Check if user can add another plant.
        Business rule: Free users limited to 5 plants, premium unlimited.
        
        Returns:
            bool: True if user can add another plant
        """
        if self.is_premium:
            return True
        
        return self.plant_count < 5
    
    def get_remaining_plant_slots(self) -> Optional[int]:
        """
        Get remaining plant slots for free users.
        
        Returns:
            Optional[int]: Remaining slots, None if premium (unlimited)
        """
        if self.is_premium:
            return None
        
        return max(0, 5 - self.plant_count)
    
    def is_active(self) -> bool:
        """Check if user is active and can use the application."""
        return self.status == UserStatus.ACTIVE
    
    def is_verified(self) -> bool:
        """Check if user email is verified."""
        return self.email_verified
    
    def has_role(self, role: UserRole) -> bool:
        """
        Check if user has specific role or higher.
        
        Args:
            role: Role to check
            
        Returns:
            bool: True if user has role or higher
        """
        role_hierarchy = {
            UserRole.USER: 1,
            UserRole.PREMIUM: 2,
            UserRole.EXPERT: 3,
            UserRole.ADMIN: 4
        }
        
        return role_hierarchy.get(self.role, 0) >= role_hierarchy.get(role, 0)
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert user to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: User data as dictionary
        """
        return {
            "user_id": self.user_id,
            "email": self.email,
            "supabase_user_id": self.supabase_user_id,
            "email_verified": self.email_verified,
            "phone": self.phone,
            "phone_verified": self.phone_verified,
            "role": self.role.value,
            "status": self.status.value,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "last_login_at": self.last_login_at.isoformat() if self.last_login_at else None,
            "email_confirmed_at": self.email_confirmed_at.isoformat() if self.email_confirmed_at else None,
            "plant_count": self.plant_count,
            "subscription_tier": self.subscription_tier,
            "is_premium": self.is_premium,
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "User":
        """
        Create user from dictionary.
        
        Args:
            data: User data dictionary
            
        Returns:
            User: User instance
        """
        # Parse datetime fields
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        last_login_at = datetime.fromisoformat(data["last_login_at"]) if data.get("last_login_at") else None
        email_confirmed_at = datetime.fromisoformat(data["email_confirmed_at"]) if data.get("email_confirmed_at") else None
        
        return cls(
            user_id=data["user_id"],
            email=data["email"],
            supabase_user_id=data.get("supabase_user_id"),
            email_verified=data.get("email_verified", False),
            phone=data.get("phone"),
            phone_verified=data.get("phone_verified", False),
            role=UserRole(data.get("role", UserRole.USER.value)),
            status=UserStatus(data.get("status", UserStatus.PENDING.value)),
            created_at=created_at,
            updated_at=updated_at,
            last_login_at=last_login_at,
            email_confirmed_at=email_confirmed_at,
            plant_count=data.get("plant_count", 0),
            subscription_tier=data.get("subscription_tier", "free"),
            is_premium=data.get("is_premium", False),
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        return f"User(id={self.user_id}, email={self.email}, role={self.role.value})"
    
    def __repr__(self) -> str:
        return self.__str__()