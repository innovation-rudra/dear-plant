# app/modules/user_management/domain/models/__init__.py
"""
Plant Care Application - User Management Domain Models

Core domain entities for user management in the Plant Care Application.
These models represent the business concepts and rules for users, profiles, and subscriptions.

Domain Models:
- User: Core user entity with authentication and basic information
- Profile: Extended user profile with Plant Care specific preferences
- Subscription: Premium subscription management for Plant Care features

All models follow Domain-Driven Design principles and are independent of infrastructure concerns.
"""

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.models.profile import Profile, UserPreferences, NotificationSettings
from app.modules.user_management.domain.models.subscription import (
    Subscription, 
    SubscriptionTier, 
    SubscriptionStatus,
    SubscriptionLimits
)

__all__ = [
    # User models
    "User",
    "UserRole", 
    "UserStatus",
    
    # Profile models
    "Profile",
    "UserPreferences",
    "NotificationSettings",
    
    # Subscription models
    "Subscription",
    "SubscriptionTier",
    "SubscriptionStatus", 
    "SubscriptionLimits",
]