# app/modules/user_management/domain/events/__init__.py
"""
Plant Care Application - User Management Domain Events

Domain events for user management business logic in the Plant Care Application.
Enables event-driven architecture and decoupled module communication.
"""

from app.modules.user_management.domain.events.user_events import (
    # User lifecycle events
    UserRegistered,
    UserActivated,
    UserDeactivated,
    UserDeleted,
    UserPasswordChanged,
    UserEmailVerified,
    UserLastLoginUpdated,
    UserLoggedOut,
    UserSessionRefreshed,
    UserDataExported,
    
    # Profile events
    ProfileCreated,
    ProfileUpdated,
    ProfileAvatarUpdated,
    ProfilePreferencesUpdated,
    ProfileFollowed,
    ProfileUnfollowed,
    
    # Expert verification events
    ExpertVerificationRequested,
    ExpertVerificationApproved,
    ExpertVerificationRejected,
    ExpertStatusUpdated,
    ExpertRatingUpdated,
    
    # Subscription events
    SubscriptionCreated,
    SubscriptionUpgraded,
    SubscriptionDowngraded,
    SubscriptionCancelled,
    SubscriptionRenewed,
    SubscriptionExpired,
    TrialStarted,
    TrialExpired,
    PaymentProcessed,
    PaymentFailed,
    
    # Usage and feature events
    UsageLimitReached,
    FeatureAccessGranted,
    FeatureAccessRevoked,
    
    # Security events
    SecurityAlertTriggered,
    SuspiciousActivityDetected,
    AccountLocked,
    AccountUnlocked
)

from app.modules.user_management.domain.events.handlers import (
    # Event handlers
    UserEventHandler,
    ProfileEventHandler,
    ExpertEventHandler,
    SubscriptionEventHandler,
    SecurityEventHandler,
    AnalyticsEventHandler,
    
    # Event handler registry
    EventHandlerRegistry,
    create_event_handler_registry
)

__all__ = [
    # User lifecycle events
    "UserRegistered",
    "UserActivated",
    "UserDeactivated", 
    "UserDeleted",
    "UserPasswordChanged",
    "UserEmailVerified",
    "UserLastLoginUpdated",
    "UserLoggedOut",
    "UserSessionRefreshed",
    "UserDataExported",
    
    # Profile events
    "ProfileCreated",
    "ProfileUpdated",
    "ProfileAvatarUpdated",
    "ProfilePreferencesUpdated",
    "ProfileFollowed",
    "ProfileUnfollowed",
    
    # Expert verification events
    "ExpertVerificationRequested",
    "ExpertVerificationApproved",
    "ExpertVerificationRejected",
    "ExpertStatusUpdated",
    "ExpertRatingUpdated",
    
    # Subscription events
    "SubscriptionCreated",
    "SubscriptionUpgraded",
    "SubscriptionDowngraded",
    "SubscriptionCancelled",
    "SubscriptionRenewed",
    "SubscriptionExpired",
    "TrialStarted",
    "TrialExpired",
    "PaymentProcessed",
    "PaymentFailed",
    
    # Usage and feature events
    "UsageLimitReached",
    "FeatureAccessGranted",
    "FeatureAccessRevoked",
    
    # Security events
    "SecurityAlertTriggered",
    "SuspiciousActivityDetected",
    "AccountLocked",
    "AccountUnlocked",
    
    # Event handlers
    "UserEventHandler",
    "ProfileEventHandler",
    "ExpertEventHandler",
    "SubscriptionEventHandler",
    "SecurityEventHandler",
    "AnalyticsEventHandler",
    
    # Event handler registry
    "EventHandlerRegistry",
    "create_event_handler_registry"
]