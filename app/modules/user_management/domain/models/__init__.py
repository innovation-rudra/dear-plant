# app/modules/user_management/domain/models/__init__.py
"""
Plant Care Application - User Management Domain Models

Domain models for user management in the Plant Care Application.
Contains core business entities with Plant Care specific logic and validation.
"""

from app.modules.user_management.domain.models.user import (
    # User model and enums
    User,
    UserRole,
    UserStatus,
    
    # User factory functions
    create_user,
    create_user_from_oauth
)

from app.modules.user_management.domain.models.profile import (
    # Profile model and enums
    Profile,
    ProfileStatus,
    ExperienceLevel,
    PreferredUnits,
    ProfileVisibility,
    
    # Profile factory functions
    create_profile,
    create_expert_profile
)

from app.modules.user_management.domain.models.subscription import (
    # Subscription model and enums
    Subscription,
    SubscriptionTier,
    SubscriptionStatus,
    BillingCycle,
    
    # Subscription factory functions
    create_subscription,
    create_free_subscription,
    create_premium_subscription,
    create_trial_subscription
)

__all__ = [
    # User model and enums
    "User",
    "UserRole",
    "UserStatus",
    
    # User factory functions
    "create_user",
    "create_user_from_oauth",
    
    # Profile model and enums
    "Profile",
    "ProfileStatus",
    "ExperienceLevel",
    "PreferredUnits",
    "ProfileVisibility",
    
    # Profile factory functions
    "create_profile",
    "create_expert_profile",
    
    # Subscription model and enums
    "Subscription",
    "SubscriptionTier",
    "SubscriptionStatus",
    "BillingCycle",
    
    # Subscription factory functions
    "create_subscription",
    "create_free_subscription",
    "create_premium_subscription",
    "create_trial_subscription"
]