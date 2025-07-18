# app/modules/user_management/domain/events/user_events.py
"""
Plant Care Application - User Management Domain Events

Domain events for user management operations.
These events enable other modules to react to user changes without tight coupling.
"""

from datetime import datetime
from typing import Dict, Any, Optional
from dataclasses import dataclass, field

from app.shared.events.base import BaseEvent


# User Events
@dataclass
class UserRegistered(BaseEvent):
    """Event fired when a new user registers in the Plant Care Application."""
    
    user_id: str
    email: str
    supabase_user_id: Optional[str] = None
    registration_source: str = "web"  # web, mobile, api
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.registered"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass  
class UserActivated(BaseEvent):
    """Event fired when a user account is activated."""
    
    user_id: str
    email: str
    activation_method: str = "email_verification"  # email_verification, admin, auto
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.activated"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserDeactivated(BaseEvent):
    """Event fired when a user account is deactivated."""
    
    user_id: str
    email: str
    reason: Optional[str] = None
    deactivated_by: Optional[str] = None  # user_id of admin or "system"
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.deactivated"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserSuspended(BaseEvent):
    """Event fired when a user account is suspended."""
    
    user_id: str
    email: str
    reason: str
    suspended_by: str  # user_id of admin
    suspended_until: Optional[datetime] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.suspended"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserEmailVerified(BaseEvent):
    """Event fired when user verifies their email."""
    
    user_id: str
    email: str
    verification_method: str = "email_link"  # email_link, code, admin
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.email_verified"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserRoleChanged(BaseEvent):
    """Event fired when user role changes."""
    
    user_id: str
    email: str
    old_role: str
    new_role: str
    changed_by: Optional[str] = None  # user_id of admin or "system"
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.role_changed"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserLastLoginUpdated(BaseEvent):
    """Event fired when user logs in."""
    
    user_id: str
    login_timestamp: datetime
    login_source: str = "web"  # web, mobile, api
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.last_login_updated"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserUpgradedToPremium(BaseEvent):
    """Event fired when user upgrades to premium."""
    
    user_id: str
    email: str
    subscription_tier: str
    upgrade_source: str = "manual"  # manual, trial_conversion, admin
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.upgraded_to_premium"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserDowngradedFromPremium(BaseEvent):
    """Event fired when user downgrades from premium."""
    
    user_id: str
    email: str
    old_tier: str
    new_tier: str
    downgrade_reason: str = "subscription_ended"  # subscription_ended, cancellation, payment_failed
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.downgraded_from_premium"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserPromotedToExpert(BaseEvent):
    """Event fired when user is promoted to expert."""
    
    user_id: str
    email: str
    promoted_by: str  # user_id of admin
    expert_specialties: list = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.promoted_to_expert"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


@dataclass
class UserPlantCountUpdated(BaseEvent):
    """Event fired when user's plant count changes."""
    
    user_id: str
    old_count: int
    new_count: int
    change_reason: str = "plant_added"  # plant_added, plant_removed, bulk_update
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "user.plant_count_updated"
        self.aggregate_type = "user"
        self.aggregate_id = self.user_id


# Profile Events
@dataclass
class ProfileCreated(BaseEvent):
    """Event fired when user profile is created."""
    
    profile_id: str
    user_id: str
    display_name: Optional[str] = None
    experience_level: str = "beginner"
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "profile.created"
        self.aggregate_type = "profile"
        self.aggregate_id = self.profile_id


@dataclass
class ProfileUpdated(BaseEvent):
    """Event fired when user profile is updated."""
    
    profile_id: str
    user_id: str
    updated_fields: list = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "profile.updated"
        self.aggregate_type = "profile"
        self.aggregate_id = self.profile_id


@dataclass
class ProfileAvatarUpdated(BaseEvent):
    """Event fired when user avatar is updated."""
    
    profile_id: str
    user_id: str
    old_avatar_url: Optional[str] = None
    new_avatar_url: str = ""
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "profile.avatar_updated"
        self.aggregate_type = "profile"
        self.aggregate_id = self.profile_id


@dataclass
class ProfileExperienceLevelUpdated(BaseEvent):
    """Event fired when user experience level changes."""
    
    profile_id: str
    user_id: str
    old_level: str
    new_level: str
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "profile.experience_level_updated"
        self.aggregate_type = "profile"
        self.aggregate_id = self.profile_id


@dataclass
class ProfileVerifiedAsExpert(BaseEvent):
    """Event fired when profile is verified as expert."""
    
    profile_id: str
    user_id: str
    expert_rating: float
    verified_by: str  # user_id of admin
    specialties: list = field(default_factory=list)
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "profile.verified_as_expert"
        self.aggregate_type = "profile"
        self.aggregate_id = self.profile_id


# Subscription Events
@dataclass
class SubscriptionCreated(BaseEvent):
    """Event fired when subscription is created."""
    
    subscription_id: str
    user_id: str
    tier: str
    price_per_month: float = 0.0
    is_trial: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.created"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionUpgraded(BaseEvent):
    """Event fired when subscription is upgraded."""
    
    subscription_id: str
    user_id: str
    old_tier: str
    new_tier: str
    old_price: float
    new_price: float
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.upgraded"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionDowngraded(BaseEvent):
    """Event fired when subscription is downgraded."""
    
    subscription_id: str
    user_id: str
    old_tier: str
    new_tier: str
    old_price: float
    new_price: float
    reason: str = "user_request"
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.downgraded"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionCancelled(BaseEvent):
    """Event fired when subscription is cancelled."""
    
    subscription_id: str
    user_id: str
    tier: str
    cancellation_reason: Optional[str] = None
    immediate: bool = False
    cancelled_by: str = "user"  # user, admin, system
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.cancelled"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionReactivated(BaseEvent):
    """Event fired when subscription is reactivated."""
    
    subscription_id: str
    user_id: str
    tier: str
    reactivation_reason: str = "user_request"
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.reactivated"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionTrialStarted(BaseEvent):
    """Event fired when trial subscription starts."""
    
    subscription_id: str
    user_id: str
    tier: str
    trial_days: int
    trial_end_date: datetime
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.trial_started"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionTrialEnded(BaseEvent):
    """Event fired when trial subscription ends."""
    
    subscription_id: str
    user_id: str
    tier: str
    converted_to_paid: bool = False
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.trial_ended"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionPaymentRecorded(BaseEvent):
    """Event fired when subscription payment is recorded."""
    
    subscription_id: str
    user_id: str
    amount: float
    currency: str
    payment_method: str
    transaction_id: Optional[str] = None
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.payment_recorded"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionPaymentFailed(BaseEvent):
    """Event fired when subscription payment fails."""
    
    subscription_id: str
    user_id: str
    amount: float
    currency: str
    payment_method: str
    failure_reason: str
    retry_count: int = 1
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.payment_failed"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id


@dataclass
class SubscriptionExpired(BaseEvent):
    """Event fired when subscription expires."""
    
    subscription_id: str
    user_id: str
    expired_tier: str
    new_tier: str = "free"
    expiration_reason: str = "period_ended"  # period_ended, payment_failed, cancelled
    
    def __post_init__(self):
        super().__post_init__()
        self.event_type = "subscription.expired"
        self.aggregate_type = "subscription"
        self.aggregate_id = self.subscription_id