# app/modules/user_management/domain/models/subscription.py
"""
Plant Care Application - Subscription Domain Model

Subscription management for Plant Care Application premium features.
Handles subscription tiers, limits, billing, and premium feature access.
"""

import uuid
from datetime import datetime, timedelta
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import structlog

# Setup logger
logger = structlog.get_logger(__name__)


class SubscriptionTier(str, Enum):
    """
    Subscription tiers in Plant Care Application.
    Defines feature access and usage limits.
    """
    FREE = "free"           # Basic features, limited plants
    PREMIUM = "premium"     # Advanced features, unlimited plants
    EXPERT = "expert"       # Expert features, consultation tools
    FAMILY = "family"       # Family sharing, multiple users


class SubscriptionStatus(str, Enum):
    """
    Subscription status values.
    """
    ACTIVE = "active"           # Active subscription
    CANCELLED = "cancelled"     # Cancelled but still valid until period end
    EXPIRED = "expired"         # Expired subscription
    PAST_DUE = "past_due"      # Payment failed, grace period
    PAUSED = "paused"          # Temporarily paused
    TRIALING = "trialing"      # Free trial period


class PaymentMethod(str, Enum):
    """Payment methods for subscriptions."""
    CREDIT_CARD = "credit_card"
    DEBIT_CARD = "debit_card"
    PAYPAL = "paypal"
    BANK_TRANSFER = "bank_transfer"
    UPI = "upi"                # For Indian market
    WALLET = "wallet"


@dataclass
class SubscriptionLimits:
    """
    Feature limits for different subscription tiers.
    Defines what users can access based on their subscription.
    """
    
    # Plant management limits
    max_plants: Optional[int] = 5  # None = unlimited
    max_plant_photos_per_plant: int = 10
    
    # Plant identification limits
    plant_identifications_per_month: Optional[int] = 3  # None = unlimited
    
    # AI and expert features
    ai_chat_messages_per_month: Optional[int] = None
    expert_consultations_per_month: Optional[int] = None
    
    # Storage limits
    max_storage_gb: Optional[float] = 1.0  # None = unlimited
    
    # Community features
    can_post_in_community: bool = True
    can_ask_experts: bool = True
    priority_expert_response: bool = False
    
    # Advanced features
    weather_integration: bool = True
    care_analytics: bool = False
    growth_tracking: bool = True
    automated_care_schedules: bool = False
    family_sharing: bool = False
    
    # Export and backup
    can_export_data: bool = False
    automated_backups: bool = False
    
    @classmethod
    def get_limits_for_tier(cls, tier: SubscriptionTier) -> "SubscriptionLimits":
        """
        Get feature limits for subscription tier.
        
        Args:
            tier: Subscription tier
            
        Returns:
            SubscriptionLimits: Limits for the tier
        """
        if tier == SubscriptionTier.FREE:
            return cls(
                max_plants=5,
                max_plant_photos_per_plant=5,
                plant_identifications_per_month=3,
                ai_chat_messages_per_month=10,
                expert_consultations_per_month=1,
                max_storage_gb=0.5,
                can_post_in_community=True,
                can_ask_experts=True,
                priority_expert_response=False,
                weather_integration=True,
                care_analytics=False,
                growth_tracking=True,
                automated_care_schedules=False,
                family_sharing=False,
                can_export_data=False,
                automated_backups=False,
            )
        
        elif tier == SubscriptionTier.PREMIUM:
            return cls(
                max_plants=None,  # Unlimited
                max_plant_photos_per_plant=50,
                plant_identifications_per_month=None,  # Unlimited
                ai_chat_messages_per_month=500,
                expert_consultations_per_month=5,
                max_storage_gb=10.0,
                can_post_in_community=True,
                can_ask_experts=True,
                priority_expert_response=True,
                weather_integration=True,
                care_analytics=True,
                growth_tracking=True,
                automated_care_schedules=True,
                family_sharing=False,
                can_export_data=True,
                automated_backups=True,
            )
        
        elif tier == SubscriptionTier.EXPERT:
            return cls(
                max_plants=None,  # Unlimited
                max_plant_photos_per_plant=100,
                plant_identifications_per_month=None,  # Unlimited
                ai_chat_messages_per_month=None,  # Unlimited
                expert_consultations_per_month=None,  # Can provide consultations
                max_storage_gb=50.0,
                can_post_in_community=True,
                can_ask_experts=True,
                priority_expert_response=True,
                weather_integration=True,
                care_analytics=True,
                growth_tracking=True,
                automated_care_schedules=True,
                family_sharing=True,
                can_export_data=True,
                automated_backups=True,
            )
        
        elif tier == SubscriptionTier.FAMILY:
            return cls(
                max_plants=None,  # Unlimited
                max_plant_photos_per_plant=50,
                plant_identifications_per_month=None,  # Unlimited
                ai_chat_messages_per_month=1000,
                expert_consultations_per_month=10,
                max_storage_gb=25.0,
                can_post_in_community=True,
                can_ask_experts=True,
                priority_expert_response=True,
                weather_integration=True,
                care_analytics=True,
                growth_tracking=True,
                automated_care_schedules=True,
                family_sharing=True,
                can_export_data=True,
                automated_backups=True,
            )
        
        else:
            # Default to free tier
            return cls.get_limits_for_tier(SubscriptionTier.FREE)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "max_plants": self.max_plants,
            "max_plant_photos_per_plant": self.max_plant_photos_per_plant,
            "plant_identifications_per_month": self.plant_identifications_per_month,
            "ai_chat_messages_per_month": self.ai_chat_messages_per_month,
            "expert_consultations_per_month": self.expert_consultations_per_month,
            "max_storage_gb": self.max_storage_gb,
            "can_post_in_community": self.can_post_in_community,
            "can_ask_experts": self.can_ask_experts,
            "priority_expert_response": self.priority_expert_response,
            "weather_integration": self.weather_integration,
            "care_analytics": self.care_analytics,
            "growth_tracking": self.growth_tracking,
            "automated_care_schedules": self.automated_care_schedules,
            "family_sharing": self.family_sharing,
            "can_export_data": self.can_export_data,
            "automated_backups": self.automated_backups,
        }


@dataclass
class Subscription:
    """
    User subscription for Plant Care Application premium features.
    Manages billing, feature access, and subscription lifecycle.
    """
    
    # Identity
    subscription_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Subscription details
    tier: SubscriptionTier = SubscriptionTier.FREE
    status: SubscriptionStatus = SubscriptionStatus.ACTIVE
    
    # Billing information
    price_per_month: float = 0.0
    currency: str = "USD"
    payment_method: Optional[PaymentMethod] = None
    
    # Subscription period
    started_at: datetime = field(default_factory=datetime.utcnow)
    current_period_start: datetime = field(default_factory=datetime.utcnow)
    current_period_end: datetime = field(default_factory=lambda: datetime.utcnow() + timedelta(days=30))
    
    # Trial information
    trial_start: Optional[datetime] = None
    trial_end: Optional[datetime] = None
    is_trial: bool = False
    
    # Cancellation
    cancelled_at: Optional[datetime] = None
    cancel_at_period_end: bool = False
    cancellation_reason: Optional[str] = None
    
    # Usage tracking
    usage_this_period: Dict[str, int] = field(default_factory=dict)
    
    # Feature limits
    limits: SubscriptionLimits = field(default_factory=SubscriptionLimits)
    
    # Payment tracking
    last_payment_at: Optional[datetime] = None
    next_payment_due: Optional[datetime] = None
    failed_payment_count: int = 0
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization setup."""
        self._validate_subscription_id()
        self._validate_user_id()
        
        # Set limits based on tier
        if not self.limits or self.limits == SubscriptionLimits():
            self.limits = SubscriptionLimits.get_limits_for_tier(self.tier)
        
        # Initialize usage tracking
        if not self.usage_this_period:
            self.usage_this_period = {
                "plant_identifications": 0,
                "ai_chat_messages": 0,
                "expert_consultations": 0,
                "storage_used_gb": 0.0,
            }
    
    def _validate_subscription_id(self) -> None:
        """Validate subscription ID format."""
        if not self.subscription_id:
            raise ValueError("Subscription ID is required")
        
        try:
            uuid.UUID(self.subscription_id)
        except ValueError:
            raise ValueError("Invalid subscription ID format")
    
    def _validate_user_id(self) -> None:
        """Validate user ID format."""
        if not self.user_id:
            raise ValueError("User ID is required")
        
        try:
            uuid.UUID(self.user_id)
        except ValueError:
            raise ValueError("Invalid user ID format")
    
    def start_trial(self, trial_days: int = 14) -> None:
        """
        Start free trial period.
        
        Args:
            trial_days: Length of trial in days
        """
        if self.is_trial:
            raise ValueError("Trial already started")
        
        if self.tier == SubscriptionTier.FREE:
            raise ValueError("Cannot start trial for free tier")
        
        now = datetime.utcnow()
        self.trial_start = now
        self.trial_end = now + timedelta(days=trial_days)
        self.is_trial = True
        self.status = SubscriptionStatus.TRIALING
        self.updated_at = now
        
        logger.info("Trial started", 
                   subscription_id=self.subscription_id, 
                   user_id=self.user_id,
                   trial_days=trial_days)
    
    def end_trial(self, convert_to_paid: bool = False) -> None:
        """
        End trial period.
        
        Args:
            convert_to_paid: Whether to convert to paid subscription
        """
        if not self.is_trial:
            raise ValueError("No active trial to end")
        
        self.is_trial = False
        
        if convert_to_paid:
            self.status = SubscriptionStatus.ACTIVE
            self._setup_billing_period()
        else:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.limits = SubscriptionLimits.get_limits_for_tier(SubscriptionTier.FREE)
        
        self.updated_at = datetime.utcnow()
        
        logger.info("Trial ended", 
                   subscription_id=self.subscription_id,
                   converted=convert_to_paid)
    
    def upgrade_tier(self, new_tier: SubscriptionTier, price_per_month: float) -> None:
        """
        Upgrade subscription tier.
        
        Args:
            new_tier: New subscription tier
            price_per_month: Monthly price for new tier
        """
        if new_tier == self.tier:
            raise ValueError("Already on this tier")
        
        old_tier = self.tier
        self.tier = new_tier
        self.price_per_month = price_per_month
        self.limits = SubscriptionLimits.get_limits_for_tier(new_tier)
        self.status = SubscriptionStatus.ACTIVE
        self.updated_at = datetime.utcnow()
        
        # Reset usage for new period
        self._reset_usage_tracking()
        
        logger.info("Subscription upgraded", 
                   subscription_id=self.subscription_id,
                   old_tier=old_tier.value,
                   new_tier=new_tier.value)
    
    def downgrade_tier(self, new_tier: SubscriptionTier, price_per_month: float) -> None:
        """
        Downgrade subscription tier.
        
        Args:
            new_tier: New subscription tier
            price_per_month: Monthly price for new tier
        """
        if new_tier == self.tier:
            raise ValueError("Already on this tier")
        
        old_tier = self.tier
        self.tier = new_tier
        self.price_per_month = price_per_month
        self.limits = SubscriptionLimits.get_limits_for_tier(new_tier)
        self.updated_at = datetime.utcnow()
        
        logger.info("Subscription downgraded", 
                   subscription_id=self.subscription_id,
                   old_tier=old_tier.value,
                   new_tier=new_tier.value)
    
    def cancel(self, reason: Optional[str] = None, immediate: bool = False) -> None:
        """
        Cancel subscription.
        
        Args:
            reason: Cancellation reason
            immediate: Whether to cancel immediately or at period end
        """
        if self.status == SubscriptionStatus.CANCELLED:
            raise ValueError("Subscription already cancelled")
        
        self.cancelled_at = datetime.utcnow()
        self.cancellation_reason = reason
        
        if immediate:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.limits = SubscriptionLimits.get_limits_for_tier(SubscriptionTier.FREE)
        else:
            self.status = SubscriptionStatus.CANCELLED
            self.cancel_at_period_end = True
        
        self.updated_at = datetime.utcnow()
        
        logger.info("Subscription cancelled", 
                   subscription_id=self.subscription_id,
                   reason=reason,
                   immediate=immediate)
    
    def reactivate(self) -> None:
        """Reactivate cancelled subscription."""
        if self.status not in [SubscriptionStatus.CANCELLED, SubscriptionStatus.EXPIRED]:
            raise ValueError("Can only reactivate cancelled or expired subscriptions")
        
        self.status = SubscriptionStatus.ACTIVE
        self.cancelled_at = None
        self.cancel_at_period_end = False
        self.cancellation_reason = None
        self.failed_payment_count = 0
        self.updated_at = datetime.utcnow()
        
        # Extend period if needed
        if self.current_period_end <= datetime.utcnow():
            self._setup_billing_period()
        
        logger.info("Subscription reactivated", subscription_id=self.subscription_id)
    
    def record_payment(self, amount: float, payment_method: PaymentMethod) -> None:
        """
        Record successful payment.
        
        Args:
            amount: Payment amount
            payment_method: Payment method used
        """
        self.last_payment_at = datetime.utcnow()
        self.payment_method = payment_method
        self.failed_payment_count = 0
        
        # Extend billing period
        self._setup_billing_period()
        
        # Activate if past due
        if self.status == SubscriptionStatus.PAST_DUE:
            self.status = SubscriptionStatus.ACTIVE
        
        self.updated_at = datetime.utcnow()
        
        logger.info("Payment recorded", 
                   subscription_id=self.subscription_id,
                   amount=amount,
                   method=payment_method.value)
    
    def record_payment_failure(self) -> None:
        """Record failed payment attempt."""
        self.failed_payment_count += 1
        
        # Set to past due after first failure
        if self.failed_payment_count == 1:
            self.status = SubscriptionStatus.PAST_DUE
        
        # Cancel after 3 failures
        elif self.failed_payment_count >= 3:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.limits = SubscriptionLimits.get_limits_for_tier(SubscriptionTier.FREE)
        
        self.updated_at = datetime.utcnow()
        
        logger.warning("Payment failed", 
                      subscription_id=self.subscription_id,
                      failure_count=self.failed_payment_count)
    
    def check_and_update_status(self) -> None:
        """Check subscription status and update if needed."""
        now = datetime.utcnow()
        
        # Check if trial ended
        if self.is_trial and self.trial_end and now > self.trial_end:
            self.end_trial(convert_to_paid=False)
        
        # Check if subscription expired
        elif self.status == SubscriptionStatus.ACTIVE and now > self.current_period_end:
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.limits = SubscriptionLimits.get_limits_for_tier(SubscriptionTier.FREE)
            self.updated_at = now
        
        # Check if cancelled subscription should expire
        elif (self.status == SubscriptionStatus.CANCELLED and 
              self.cancel_at_period_end and 
              now > self.current_period_end):
            self.status = SubscriptionStatus.EXPIRED
            self.tier = SubscriptionTier.FREE
            self.limits = SubscriptionLimits.get_limits_for_tier(SubscriptionTier.FREE)
            self.updated_at = now
    
    def track_usage(self, usage_type: str, amount: int = 1) -> None:
        """
        Track usage for the current period.
        
        Args:
            usage_type: Type of usage to track
            amount: Amount to add to usage
        """
        if usage_type in self.usage_this_period:
            self.usage_this_period[usage_type] += amount
        else:
            self.usage_this_period[usage_type] = amount
        
        self.updated_at = datetime.utcnow()
    
    def check_usage_limit(self, usage_type: str) -> bool:
        """
        Check if usage limit has been reached.
        
        Args:
            usage_type: Type of usage to check
            
        Returns:
            bool: True if within limit, False if limit exceeded
        """
        current_usage = self.usage_this_period.get(usage_type, 0)
        
        if usage_type == "plant_identifications":
            limit = self.limits.plant_identifications_per_month
        elif usage_type == "ai_chat_messages":
            limit = self.limits.ai_chat_messages_per_month
        elif usage_type == "expert_consultations":
            limit = self.limits.expert_consultations_per_month
        else:
            return True  # No limit for unknown usage types
        
        if limit is None:  # Unlimited
            return True
        
        return current_usage < limit
    
    def get_usage_remaining(self, usage_type: str) -> Optional[int]:
        """
        Get remaining usage for the period.
        
        Args:
            usage_type: Type of usage to check
            
        Returns:
            Optional[int]: Remaining usage, None if unlimited
        """
        current_usage = self.usage_this_period.get(usage_type, 0)
        
        if usage_type == "plant_identifications":
            limit = self.limits.plant_identifications_per_month
        elif usage_type == "ai_chat_messages":
            limit = self.limits.ai_chat_messages_per_month
        elif usage_type == "expert_consultations":
            limit = self.limits.expert_consultations_per_month
        else:
            return None
        
        if limit is None:  # Unlimited
            return None
        
        return max(0, limit - current_usage)
    
    def _setup_billing_period(self) -> None:
        """Setup next billing period."""
        now = datetime.utcnow()
        self.current_period_start = now
        self.current_period_end = now + timedelta(days=30)  # Monthly billing
        self.next_payment_due = self.current_period_end
        
        # Reset usage tracking for new period
        self._reset_usage_tracking()
    
    def _reset_usage_tracking(self) -> None:
        """Reset usage tracking for new period."""
        self.usage_this_period = {
            "plant_identifications": 0,
            "ai_chat_messages": 0,
            "expert_consultations": 0,
            "storage_used_gb": 0.0,
        }
    
    def is_active(self) -> bool:
        """Check if subscription is currently active."""
        return self.status in [SubscriptionStatus.ACTIVE, SubscriptionStatus.TRIALING]
    
    def is_premium(self) -> bool:
        """Check if subscription provides premium features."""
        return self.tier in [SubscriptionTier.PREMIUM, SubscriptionTier.EXPERT, SubscriptionTier.FAMILY]
    
    def has_feature(self, feature: str) -> bool:
        """
        Check if subscription includes specific feature.
        
        Args:
            feature: Feature name to check
            
        Returns:
            bool: True if feature is included
        """
        feature_mapping = {
            "unlimited_plants": self.limits.max_plants is None,
            "ai_chat": self.limits.ai_chat_messages_per_month is not None,
            "expert_consultations": self.limits.expert_consultations_per_month is not None,
            "priority_support": self.limits.priority_expert_response,
            "care_analytics": self.limits.care_analytics,
            "automated_schedules": self.limits.automated_care_schedules,
            "family_sharing": self.limits.family_sharing,
            "data_export": self.limits.can_export_data,
            "automated_backups": self.limits.automated_backups,
            "weather_integration": self.limits.weather_integration,
        }
        
        return feature_mapping.get(feature, False)
    
    def days_until_renewal(self) -> Optional[int]:
        """
        Get days until subscription renewal.
        
        Returns:
            Optional[int]: Days until renewal, None if not applicable
        """
        if not self.is_active():
            return None
        
        now = datetime.utcnow()
        if self.current_period_end > now:
            return (self.current_period_end - now).days
        
        return 0
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert subscription to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Subscription data as dictionary
        """
        return {
            "subscription_id": self.subscription_id,
            "user_id": self.user_id,
            "tier": self.tier.value,
            "status": self.status.value,
            "price_per_month": self.price_per_month,
            "currency": self.currency,
            "payment_method": self.payment_method.value if self.payment_method else None,
            "started_at": self.started_at.isoformat(),
            "current_period_start": self.current_period_start.isoformat(),
            "current_period_end": self.current_period_end.isoformat(),
            "trial_start": self.trial_start.isoformat() if self.trial_start else None,
            "trial_end": self.trial_end.isoformat() if self.trial_end else None,
            "is_trial": self.is_trial,
            "cancelled_at": self.cancelled_at.isoformat() if self.cancelled_at else None,
            "cancel_at_period_end": self.cancel_at_period_end,
            "cancellation_reason": self.cancellation_reason,
            "usage_this_period": self.usage_this_period,
            "limits": self.limits.to_dict(),
            "last_payment_at": self.last_payment_at.isoformat() if self.last_payment_at else None,
            "next_payment_due": self.next_payment_due.isoformat() if self.next_payment_due else None,
            "failed_payment_count": self.failed_payment_count,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Subscription":
        """
        Create subscription from dictionary.
        
        Args:
            data: Subscription data dictionary
            
        Returns:
            Subscription: Subscription instance
        """
        # Parse datetime fields
        started_at = datetime.fromisoformat(data["started_at"]) if data.get("started_at") else datetime.utcnow()
        current_period_start = datetime.fromisoformat(data["current_period_start"]) if data.get("current_period_start") else datetime.utcnow()
        current_period_end = datetime.fromisoformat(data["current_period_end"]) if data.get("current_period_end") else datetime.utcnow() + timedelta(days=30)
        trial_start = datetime.fromisoformat(data["trial_start"]) if data.get("trial_start") else None
        trial_end = datetime.fromisoformat(data["trial_end"]) if data.get("trial_end") else None
        cancelled_at = datetime.fromisoformat(data["cancelled_at"]) if data.get("cancelled_at") else None
        last_payment_at = datetime.fromisoformat(data["last_payment_at"]) if data.get("last_payment_at") else None
        next_payment_due = datetime.fromisoformat(data["next_payment_due"]) if data.get("next_payment_due") else None
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        
        # Parse limits
        limits_data = data.get("limits", {})
        limits = SubscriptionLimits(
            max_plants=limits_data.get("max_plants"),
            max_plant_photos_per_plant=limits_data.get("max_plant_photos_per_plant", 10),
            plant_identifications_per_month=limits_data.get("plant_identifications_per_month"),
            ai_chat_messages_per_month=limits_data.get("ai_chat_messages_per_month"),
            expert_consultations_per_month=limits_data.get("expert_consultations_per_month"),
            max_storage_gb=limits_data.get("max_storage_gb"),
            can_post_in_community=limits_data.get("can_post_in_community", True),
            can_ask_experts=limits_data.get("can_ask_experts", True),
            priority_expert_response=limits_data.get("priority_expert_response", False),
            weather_integration=limits_data.get("weather_integration", True),
            care_analytics=limits_data.get("care_analytics", False),
            growth_tracking=limits_data.get("growth_tracking", True),
            automated_care_schedules=limits_data.get("automated_care_schedules", False),
            family_sharing=limits_data.get("family_sharing", False),
            can_export_data=limits_data.get("can_export_data", False),
            automated_backups=limits_data.get("automated_backups", False),
        )
        
        return cls(
            subscription_id=data["subscription_id"],
            user_id=data["user_id"],
            tier=SubscriptionTier(data.get("tier", SubscriptionTier.FREE.value)),
            status=SubscriptionStatus(data.get("status", SubscriptionStatus.ACTIVE.value)),
            price_per_month=data.get("price_per_month", 0.0),
            currency=data.get("currency", "USD"),
            payment_method=PaymentMethod(data["payment_method"]) if data.get("payment_method") else None,
            started_at=started_at,
            current_period_start=current_period_start,
            current_period_end=current_period_end,
            trial_start=trial_start,
            trial_end=trial_end,
            is_trial=data.get("is_trial", False),
            cancelled_at=cancelled_at,
            cancel_at_period_end=data.get("cancel_at_period_end", False),
            cancellation_reason=data.get("cancellation_reason"),
            usage_this_period=data.get("usage_this_period", {}),
            limits=limits,
            last_payment_at=last_payment_at,
            next_payment_due=next_payment_due,
            failed_payment_count=data.get("failed_payment_count", 0),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        return f"Subscription(id={self.subscription_id}, user={self.user_id}, tier={self.tier.value}, status={self.status.value})"
    
    def __repr__(self) -> str:
        return self.__str__()