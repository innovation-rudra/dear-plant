# app/modules/user_management/domain/__init__.py
"""
Plant Care Application - User Management Domain Layer

Domain layer for user management in the Plant Care Application.
Contains the core business logic, entities, and domain services.

This layer is the heart of the user management module and contains:
- Domain Models: Core entities (User, Profile, Subscription)
- Domain Events: Events fired when business operations occur
- Repository Interfaces: Contracts for data access
- Domain Services: Business logic services (will be added in next phase)

The domain layer is independent of infrastructure concerns and external dependencies.
It represents the Plant Care Application's business rules and concepts for user management.

Architecture:
- models/: Core domain entities and value objects
- events/: Domain events and event handlers
- repositories/: Repository interfaces (not implementations)
- services/: Domain services with business logic (coming in Phase 2)

Usage:
    from app.modules.user_management.domain.models import User, Profile, Subscription
    from app.modules.user_management.domain.events import UserRegistered, ProfileCreated
    from app.modules.user_management.domain.repositories import UserRepository, ProfileRepository
"""

# Import domain models
from app.modules.user_management.domain.models import (
    User, UserRole, UserStatus,
    Profile, UserPreferences, NotificationSettings, 
    Subscription, SubscriptionTier, SubscriptionStatus, SubscriptionLimits
)

# Import domain events
from app.modules.user_management.domain.events import (
    UserRegistered, UserActivated, UserDeactivated, UserSuspended,
    UserEmailVerified, UserRoleChanged, UserUpgradedToPremium,
    ProfileCreated, ProfileUpdated, ProfileVerifiedAsExpert,
    SubscriptionCreated, SubscriptionUpgraded, SubscriptionCancelled
)

# Import repository interfaces
from app.modules.user_management.domain.repositories import (
    UserRepository, ProfileRepository
)

# Import event handlers
from app.modules.user_management.domain.events.handlers import (
    event_handler_registry
)

__all__ = [
    # Domain Models
    "User", "UserRole", "UserStatus",
    "Profile", "UserPreferences", "NotificationSettings",
    "Subscription", "SubscriptionTier", "SubscriptionStatus", "SubscriptionLimits",
    
    # Domain Events  
    "UserRegistered", "UserActivated", "UserDeactivated", "UserSuspended",
    "UserEmailVerified", "UserRoleChanged", "UserUpgradedToPremium",
    "ProfileCreated", "ProfileUpdated", "ProfileVerifiedAsExpert", 
    "SubscriptionCreated", "SubscriptionUpgraded", "SubscriptionCancelled",
    
    # Repository Interfaces
    "UserRepository", "ProfileRepository",
    
    # Event Handlers
    "event_handler_registry",
]