# app/modules/user_management/application/dto/subscription_dto.py
"""
Plant Care Application - Subscription Management DTOs

Data Transfer Objects for subscription-related operations in the Plant Care Application.
Defines data structures for subscription creation, updates, billing, and usage tracking.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field

from app.modules.user_management.domain.models.subscription import (
    Subscription, SubscriptionTier, SubscriptionStatus, BillingCycle
)


@dataclass
class SubscriptionDTO:
    """
    Complete subscription data transfer object for Plant Care Application.
    Used for detailed subscription information including billing and usage.
    """
    # Core subscription data
    subscription_id: str
    user_id: str
    tier: str
    status: str
    billing_cycle: Optional[str] = None
    
    # Pricing information
    price: float = 0.0
    currency: str = "USD"
    
    # Trial information
    trial_end_date: Optional[str] = None
    is_trial: bool = False
    days_left_in_trial: Optional[int] = None
    
    # Billing periods
    current_period_start: str = ""
    current_period_end: str = ""
    next_billing_date: Optional[str] = None
    
    # Payment information
    payment_method_id: Optional[str] = None
    last_payment_date: Optional[str] = None
    last_payment_amount: Optional[float] = None
    
    # Subscription management
    cancel_at_period_end: bool = False
    cancelled_at: Optional[str] = None
    cancellation_reason: Optional[str] = None
    
    # Feature limits and usage
    features: Dict[str, Any] = field(default_factory=dict)
    usage_current_period: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    
    # Computed fields
    is_active: bool = True
    can_upgrade: bool = False
    can_downgrade: bool = False
    upgrade_options: List[str] = field(default_factory=list)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class SubscriptionCreationDTO:
    """
    Subscription creation data transfer object.
    Contains data needed for creating a new subscription.
    """
    # Required fields
    user_id: str
    tier: str
    billing_cycle: str
    
    # Payment information
    payment_method_id: Optional[str] = None
    
    # Pricing overrides
    custom_price: Optional[Decimal] = None
    currency: str = "USD"
    
    # Trial settings
    start_trial: bool = False
    trial_days: int = 14
    
    # Promotional codes
    coupon_code: Optional[str] = None
    promo_code: Optional[str] = None
    
    # Subscription settings
    auto_renew: bool = True
    send_invoices: bool = True
    
    # Metadata
    source: str = "web"  # web, mobile, admin
    created_by: Optional[str] = None
    notes: Optional[str] = None


@dataclass
class SubscriptionUpdateDTO:
    """
    Subscription update data transfer object.
    Contains fields that can be updated in a subscription.
    """
    # Tier changes
    new_tier: Optional[str] = None
    new_billing_cycle: Optional[str] = None
    
    # Payment updates
    payment_method_id: Optional[str] = None
    
    # Subscription management
    cancel_at_period_end: Optional[bool] = None
    cancellation_reason: Optional[str] = None
    
    # Settings updates
    auto_renew: Optional[bool] = None
    send_invoices: Optional[bool] = None
    
    # Pricing updates (admin only)
    custom_price: Optional[Decimal] = None
    
    # Metadata
    update_reason: Optional[str] = None
    updated_by: Optional[str] = None
    proration_enabled: bool = True


@dataclass
class SubscriptionUsageDTO:
    """
    Subscription usage data transfer object.
    Contains current usage data for subscription features.
    """
    subscription_id: str
    user_id: str
    tier: str
    
    # Plant Care feature usage
    ai_identifications: Dict[str, Any] = field(default_factory=lambda: {
        "used": 0,
        "limit": 10,
        "remaining": 10,
        "reset_date": None,
        "overage_allowed": False
    })
    
    expert_consultations: Dict[str, Any] = field(default_factory=lambda: {
        "used": 0,
        "limit": 0,
        "remaining": 0,
        "reset_date": None,
        "overage_allowed": False
    })
    
    plant_limit: Dict[str, Any] = field(default_factory=lambda: {
        "used": 0,
        "limit": 5,
        "remaining": 5,
        "unlimited": False
    })
    
    # Premium features usage
    advanced_analytics: Dict[str, Any] = field(default_factory=lambda: {
        "available": False,
        "used_this_month": 0
    })
    
    data_export: Dict[str, Any] = field(default_factory=lambda: {
        "available": False,
        "exports_this_month": 0,
        "limit": 0
    })
    
    family_sharing: Dict[str, Any] = field(default_factory=lambda: {
        "available": False,
        "members_added": 0,
        "max_members": 0
    })
    
    # Usage period
    period_start: str = ""
    period_end: str = ""
    
    # Usage alerts
    approaching_limits: List[str] = field(default_factory=list)
    exceeded_limits: List[str] = field(default_factory=list)
    
    # Metadata
    last_updated: str = ""
    next_reset: str = ""


@dataclass
class SubscriptionAnalyticsDTO:
    """
    Subscription analytics data transfer object.
    Contains analytical data about subscription performance and usage patterns.
    """
    subscription_id: str
    user_id: str
    tier: str
    
    # Usage analytics
    feature_utilization: Dict[str, float] = field(default_factory=dict)
    usage_trends: Dict[str, List[int]] = field(default_factory=dict)
    peak_usage_hours: List[int] = field(default_factory=list)
    
    # Billing analytics
    total_revenue: float = 0.0
    average_monthly_revenue: float = 0.0
    payments_count: int = 0
    failed_payments_count: int = 0
    
    # Engagement metrics
    login_frequency: float = 0.0
    feature_adoption_rate: float = 0.0
    support_tickets_count: int = 0
    
    # Churn risk indicators
    churn_risk_score: float = 0.0
    churn_risk_factors: List[str] = field(default_factory=list)
    
    # Upgrade/downgrade history
    tier_changes: List[Dict[str, Any]] = field(default_factory=list)
    
    # Lifetime value
    customer_lifetime_value: float = 0.0
    predicted_retention_months: int = 0
    
    # Generated metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    period: str = "last_30_days"


@dataclass
class FeatureUsageDTO:
    """
    Feature usage data transfer object.
    Contains detailed usage information for a specific feature.
    """
    feature_name: str
    user_id: str
    subscription_tier: str
    
    # Usage data
    current_usage: int = 0
    usage_limit: int = 0
    remaining_usage: int = 0
    is_unlimited: bool = False
    
    # Usage history
    daily_usage: List[int] = field(default_factory=list)
    weekly_usage: List[int] = field(default_factory=list)
    monthly_usage: List[int] = field(default_factory=list)
    
    # Usage period
    period_start: str = ""
    period_end: str = ""
    reset_frequency: str = "monthly"  # daily, weekly, monthly
    next_reset: str = ""
    
    # Overage handling
    overage_allowed: bool = False
    overage_rate: Optional[float] = None
    current_overage: int = 0
    overage_charges: float = 0.0
    
    # Usage alerts
    usage_percentage: float = 0.0
    alert_threshold: float = 0.8  # 80%
    alert_triggered: bool = False
    
    # Metadata
    last_used: Optional[str] = None
    avg_daily_usage: float = 0.0
    projected_monthly_usage: int = 0


@dataclass
class BillingDTO:
    """
    Billing data transfer object.
    Contains billing information and payment history.
    """
    subscription_id: str
    user_id: str
    
    # Current billing info
    current_amount: float = 0.0
    currency: str = "USD"
    billing_cycle: str = "monthly"
    next_billing_date: Optional[str] = None
    
    # Payment method
    payment_method_id: Optional[str] = None
    payment_method_type: Optional[str] = None
    payment_method_last4: Optional[str] = None
    
    # Billing history
    payment_history: List[Dict[str, Any]] = field(default_factory=list)
    invoice_history: List[Dict[str, Any]] = field(default_factory=list)
    
    # Billing status
    payment_status: str = "current"  # current, past_due, failed
    days_overdue: int = 0
    
    # Proration and credits
    pending_charges: float = 0.0
    account_credit: float = 0.0
    proration_amount: float = 0.0
    
    # Tax information
    tax_rate: float = 0.0
    tax_amount: float = 0.0
    tax_included: bool = False
    
    # Billing preferences
    send_invoices: bool = True
    invoice_email: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    
    # Metadata
    last_payment_date: Optional[str] = None
    last_payment_amount: Optional[float] = None
    payment_failures_count: int = 0


@dataclass
class TrialDTO:
    """
    Trial subscription data transfer object.
    Contains trial-specific information and management.
    """
    subscription_id: str
    user_id: str
    
    # Trial information
    trial_tier: str
    trial_start_date: str
    trial_end_date: str
    days_remaining: int
    
    # Trial status
    is_active: bool = True
    trial_extended: bool = False
    extension_days: int = 0
    
    # Usage during trial
    features_used: List[str] = field(default_factory=list)
    usage_percentage: float = 0.0
    engagement_score: float = 0.0
    
    # Conversion tracking
    conversion_likelihood: float = 0.0
    conversion_factors: List[str] = field(default_factory=list)
    
    # Trial notifications
    reminder_sent: bool = False
    expiration_notifications: List[str] = field(default_factory=list)
    
    # Post-trial options
    available_tiers: List[str] = field(default_factory=list)
    recommended_tier: Optional[str] = None
    discount_offers: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    trial_source: str = "web"  # web, mobile, referral
    referral_code: Optional[str] = None


# Factory functions for creating DTOs from domain models

def create_subscription_dto(subscription: Subscription, 
                          usage_data: Optional[Dict[str, Any]] = None,
                          feature_limits: Optional[Dict[str, Any]] = None) -> SubscriptionDTO:
    """
    Create SubscriptionDTO from domain Subscription model.
    
    Args:
        subscription: Subscription domain model
        usage_data: Current usage data (optional)
        feature_limits: Feature limits for tier (optional)
        
    Returns:
        SubscriptionDTO: Complete subscription data transfer object
    """
    # Calculate trial days remaining
    days_left_in_trial = None
    if subscription.trial_end_date:
        remaining = (subscription.trial_end_date - datetime.utcnow()).days
        days_left_in_trial = max(0, remaining)
    
    # Determine upgrade/downgrade options
    upgrade_options = []
    can_upgrade = False
    can_downgrade = False
    
    if subscription.tier == SubscriptionTier.FREE:
        upgrade_options = ["premium", "expert", "family"]
        can_upgrade = True
    elif subscription.tier == SubscriptionTier.PREMIUM:
        upgrade_options = ["expert", "family"]
        can_upgrade = True
        can_downgrade = True
    elif subscription.tier == SubscriptionTier.EXPERT:
        upgrade_options = ["family"]
        can_upgrade = True
        can_downgrade = True
    elif subscription.tier == SubscriptionTier.FAMILY:
        can_downgrade = True
    
    # Build features dictionary
    features = feature_limits or _get_default_feature_limits(subscription.tier)
    
    return SubscriptionDTO(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        tier=subscription.tier.value,
        status=subscription.status.value,
        billing_cycle=subscription.billing_cycle.value if subscription.billing_cycle else None,
        price=float(subscription.price),
        currency=subscription.currency,
        trial_end_date=subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
        is_trial=subscription.is_trial(),
        days_left_in_trial=days_left_in_trial,
        current_period_start=subscription.current_period_start.isoformat(),
        current_period_end=subscription.current_period_end.isoformat(),
        next_billing_date=subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
        payment_method_id=subscription.payment_method_id,
        last_payment_date=subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
        last_payment_amount=float(subscription.last_payment_amount) if subscription.last_payment_amount else None,
        cancel_at_period_end=subscription.cancel_at_period_end,
        cancelled_at=subscription.cancelled_at.isoformat() if subscription.cancelled_at else None,
        cancellation_reason=subscription.cancellation_reason,
        features=features,
        usage_current_period=usage_data or {},
        created_at=subscription.created_at.isoformat(),
        updated_at=subscription.updated_at.isoformat(),
        is_active=subscription.is_active(),
        can_upgrade=can_upgrade,
        can_downgrade=can_downgrade,
        upgrade_options=upgrade_options
    )


def create_subscription_usage_dto(subscription: Subscription,
                                usage_data: Dict[str, Any]) -> SubscriptionUsageDTO:
    """
    Create SubscriptionUsageDTO from subscription and usage data.
    
    Args:
        subscription: Subscription domain model
        usage_data: Current usage data
        
    Returns:
        SubscriptionUsageDTO: Subscription usage data transfer object
    """
    # Get feature limits for tier
    feature_limits = _get_default_feature_limits(subscription.tier)
    
    # Calculate remaining usage
    ai_used = usage_data.get("ai_identifications", 0)
    ai_limit = feature_limits.get("ai_identifications_per_month", 0)
    ai_remaining = max(0, ai_limit - ai_used) if ai_limit > 0 else 0
    
    expert_used = usage_data.get("expert_consultations", 0)
    expert_limit = feature_limits.get("expert_consultations_per_month", 0)
    expert_remaining = max(0, expert_limit - expert_used) if expert_limit > 0 else 0
    
    plants_used = usage_data.get("plants_count", 0)
    plants_limit = feature_limits.get("max_plants", 5)
    plants_remaining = max(0, plants_limit - plants_used) if plants_limit > 0 else 0
    
    # Calculate next reset date
    next_reset = subscription.current_period_end.isoformat()
    
    # Determine approaching limits
    approaching_limits = []
    exceeded_limits = []
    
    if ai_limit > 0:
        usage_percentage = (ai_used / ai_limit) * 100
        if usage_percentage >= 100:
            exceeded_limits.append("ai_identifications")
        elif usage_percentage >= 80:
            approaching_limits.append("ai_identifications")
    
    if expert_limit > 0:
        usage_percentage = (expert_used / expert_limit) * 100
        if usage_percentage >= 100:
            exceeded_limits.append("expert_consultations")
        elif usage_percentage >= 80:
            approaching_limits.append("expert_consultations")
    
    if plants_limit > 0:
        usage_percentage = (plants_used / plants_limit) * 100
        if usage_percentage >= 100:
            exceeded_limits.append("plant_limit")
        elif usage_percentage >= 80:
            approaching_limits.append("plant_limit")
    
    return SubscriptionUsageDTO(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        tier=subscription.tier.value,
        ai_identifications={
            "used": ai_used,
            "limit": ai_limit,
            "remaining": ai_remaining,
            "reset_date": next_reset,
            "overage_allowed": False
        },
        expert_consultations={
            "used": expert_used,
            "limit": expert_limit,
            "remaining": expert_remaining,
            "reset_date": next_reset,
            "overage_allowed": False
        },
        plant_limit={
            "used": plants_used,
            "limit": plants_limit,
            "remaining": plants_remaining,
            "unlimited": plants_limit == -1
        },
        advanced_analytics={
            "available": feature_limits.get("advanced_analytics", False),
            "used_this_month": usage_data.get("analytics_usage", 0)
        },
        data_export={
            "available": feature_limits.get("export_data", False),
            "exports_this_month": usage_data.get("exports_count", 0),
            "limit": 10 if feature_limits.get("export_data", False) else 0
        },
        family_sharing={
            "available": feature_limits.get("family_sharing", False),
            "members_added": usage_data.get("family_members", 0),
            "max_members": feature_limits.get("max_family_members", 0)
        },
        period_start=subscription.current_period_start.isoformat(),
        period_end=subscription.current_period_end.isoformat(),
        approaching_limits=approaching_limits,
        exceeded_limits=exceeded_limits,
        last_updated=datetime.utcnow().isoformat(),
        next_reset=next_reset
    )


def create_billing_dto(subscription: Subscription,
                      payment_history: List[Dict[str, Any]] = None,
                      payment_method_info: Dict[str, Any] = None) -> BillingDTO:
    """
    Create BillingDTO from subscription and payment data.
    
    Args:
        subscription: Subscription domain model
        payment_history: Payment history data (optional)
        payment_method_info: Payment method information (optional)
        
    Returns:
        BillingDTO: Billing data transfer object
    """
    payment_method_info = payment_method_info or {}
    payment_history = payment_history or []
    
    # Calculate payment status
    payment_status = "current"
    days_overdue = 0
    
    if subscription.status == SubscriptionStatus.CANCELLED:
        payment_status = "cancelled"
    elif subscription.next_billing_date and subscription.next_billing_date < datetime.utcnow():
        payment_status = "past_due"
        days_overdue = (datetime.utcnow() - subscription.next_billing_date).days
    
    # Calculate payment failures
    payment_failures = len([p for p in payment_history if p.get("status") == "failed"])
    
    return BillingDTO(
        subscription_id=subscription.subscription_id,
        user_id=subscription.user_id,
        current_amount=float(subscription.price),
        currency=subscription.currency,
        billing_cycle=subscription.billing_cycle.value if subscription.billing_cycle else "monthly",
        next_billing_date=subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
        payment_method_id=subscription.payment_method_id,
        payment_method_type=payment_method_info.get("type"),
        payment_method_last4=payment_method_info.get("last4"),
        payment_history=payment_history,
        invoice_history=[],  # Would be populated from invoice service
        payment_status=payment_status,
        days_overdue=days_overdue,
        pending_charges=0.0,
        account_credit=0.0,
        proration_amount=0.0,
        tax_rate=0.0,
        tax_amount=0.0,
        tax_included=False,
        send_invoices=True,
        invoice_email=None,
        billing_address=payment_method_info.get("billing_address"),
        last_payment_date=subscription.last_payment_date.isoformat() if subscription.last_payment_date else None,
        last_payment_amount=float(subscription.last_payment_amount) if subscription.last_payment_amount else None,
        payment_failures_count=payment_failures
    )


def _get_default_feature_limits(tier: SubscriptionTier) -> Dict[str, Any]:
    """Get default feature limits for subscription tier."""
    limits = {
        SubscriptionTier.FREE: {
            "max_plants": 5,
            "ai_identifications_per_month": 10,
            "expert_consultations_per_month": 0,
            "advanced_analytics": False,
            "family_sharing": False,
            "export_data": False,
            "priority_support": False,
            "offline_mode": False,
            "max_family_members": 0
        },
        SubscriptionTier.PREMIUM: {
            "max_plants": -1,  # Unlimited
            "ai_identifications_per_month": 100,
            "expert_consultations_per_month": 5,
            "advanced_analytics": True,
            "family_sharing": True,
            "export_data": True,
            "priority_support": True,
            "offline_mode": True,
            "max_family_members": 4
        },
        SubscriptionTier.EXPERT: {
            "max_plants": -1,  # Unlimited
            "ai_identifications_per_month": 500,
            "expert_consultations_per_month": -1,  # Unlimited
            "advanced_analytics": True,
            "family_sharing": True,
            "export_data": True,
            "priority_support": True,
            "offline_mode": True,
            "expert_tools": True,
            "community_moderation": True,
            "max_family_members": 6
        },
        SubscriptionTier.FAMILY: {
            "max_plants": -1,  # Unlimited
            "ai_identifications_per_month": 300,
            "expert_consultations_per_month": 10,
            "advanced_analytics": True,
            "family_sharing": True,
            "export_data": True,
            "priority_support": True,
            "offline_mode": True,
            "max_family_members": 6
        }
    }
    
    return limits.get(tier, limits[SubscriptionTier.FREE])