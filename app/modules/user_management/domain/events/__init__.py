# app/modules/user_management/domain/events/__init__.py
"""
Plant Care Application - User Management Domain Events

Domain events for user management operations in the Plant Care Application.
These events enable loose coupling between modules and audit trails.

Events:
- User Events: Registration, activation, deactivation, role changes
- Profile Events: Profile updates, preferences changes
- Subscription Events: Upgrades, downgrades, cancellations, payments

All events follow the domain event pattern for decoupled module communication.
"""

from app.modules.user_management.domain.events.user_events import (
    UserRegistered,
    UserActivated,
    UserDeactivated,
    UserSuspended,
    UserEmailVerified,
    UserRoleChanged,
    UserLastLoginUpdated,
    UserUpgradedToPremium,
    UserDowngradedFromPremium,
    UserPromotedToExpert,
    UserPlantCountUpdated,
    ProfileCreated,
    ProfileUpdated,
    ProfileAvatarUpdated,
    ProfileExperienceLevelUpdated,
    ProfileVerifiedAsExpert,
    SubscriptionCreated,
    SubscriptionUpgraded,
    SubscriptionDowngraded,
    SubscriptionCancelled,
    SubscriptionReactivated,
    SubscriptionTrialStarted,
    SubscriptionTrialEnded,
    SubscriptionPaymentRecorded,
    SubscriptionPaymentFailed,
    SubscriptionExpired,
)

__all__ = [
    # User events
    "UserRegistered",
    "UserActivated", 
    "UserDeactivated",
    "UserSuspended",
    "UserEmailVerified",
    "UserRoleChanged",
    "UserLastLoginUpdated",
    "UserUpgradedToPremium",
    "UserDowngradedFromPremium",
    "UserPromotedToExpert",
    "UserPlantCountUpdated",
    
    # Profile events
    "ProfileCreated",
    "ProfileUpdated",
    "ProfileAvatarUpdated", 
    "ProfileExperienceLevelUpdated",
    "ProfileVerifiedAsExpert",
    
    # Subscription events
    "SubscriptionCreated",
    "SubscriptionUpgraded",
    "SubscriptionDowngraded", 
    "SubscriptionCancelled",
    "SubscriptionReactivated",
    "SubscriptionTrialStarted",
    "SubscriptionTrialEnded",
    "SubscriptionPaymentRecorded",
    "SubscriptionPaymentFailed",
    "SubscriptionExpired",
]