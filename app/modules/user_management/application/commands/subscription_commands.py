# app/modules/user_management/application/commands/subscription_commands.py
"""
Plant Care Application - Subscription Management Commands

Commands for subscription operations in the Plant Care Application.
Handles subscription creation, upgrades, downgrades, cancellations, and billing.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime
from decimal import Decimal


@dataclass
class CreateSubscriptionCommand:
    """
    Command to create a new subscription in the Plant Care Application.
    Creates initial subscription with Plant Care feature limits.
    """
    user_id: str
    tier: str = "free"  # free, premium, expert, family
    
    # Billing information
    billing_cycle: str = "monthly"  # monthly, annual, lifetime
    payment_method_id: Optional[str] = None
    billing_address: Optional[Dict[str, str]] = None
    
    # Pricing
    base_price: Decimal = Decimal("0.00")
    discount_amount: Decimal = Decimal("0.00")
    tax_amount: Decimal = Decimal("0.00")
    total_amount: Decimal = Decimal("0.00")
    currency: str = "USD"
    
    # Plant Care feature limits
    plant_limit: int = 5  # Number of plants allowed
    ai_identification_limit: int = 10  # AI identifications per month
    expert_consultation_limit: int = 0  # Expert consultations per month
    photo_storage_limit: int = 100  # Photos per plant
    
    # Premium features
    advanced_analytics: bool = False
    weather_integration: bool = False
    care_automation: bool = False
    data_export: bool = False
    priority_support: bool = False
    
    # Family plan specific
    family_member_limit: int = 1  # Number of family members
    shared_plant_library: bool = False
    family_dashboard: bool = False
    
    # Trial and promotions
    trial_period_days: int = 0
    promotion_code: Optional[str] = None
    referral_credit: Decimal = Decimal("0.00")
    
    # Subscription context
    subscription_source: str = "direct"  # direct, app_store, google_play, referral
    created_by: Optional[str] = None  # admin_user_id if created by admin
    
    # Auto-renewal settings
    auto_renew: bool = True
    renewal_notification_days: int = 7
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpgradeSubscriptionCommand:
    """
    Command to upgrade subscription in the Plant Care Application.
    Handles tier upgrades with prorated billing and feature unlocks.
    """
    user_id: str
    subscription_id: str
    new_tier: str  # premium, expert, family
    
    # Billing changes
    new_billing_cycle: Optional[str] = None  # Change billing cycle during upgrade
    payment_method_id: Optional[str] = None  # New payment method
    
    # Pricing calculation
    proration_method: str = "immediate"  # immediate, next_cycle, custom
    upgrade_amount: Optional[Decimal] = None  # Additional amount to charge
    credit_existing_payment: bool = True
    
    # Feature unlocks
    immediate_feature_access: bool = True
    unlock_plant_limit: bool = True
    unlock_ai_features: bool = True
    unlock_expert_features: bool = True
    
    # Plant Care specific upgrades
    new_plant_limit: Optional[int] = None
    new_ai_identification_limit: Optional[int] = None
    new_expert_consultation_limit: Optional[int] = None
    new_photo_storage_limit: Optional[int] = None
    
    # Premium feature activation
    enable_advanced_analytics: bool = False
    enable_weather_integration: bool = False
    enable_care_automation: bool = False
    enable_data_export: bool = False
    enable_priority_support: bool = False
    
    # Family plan upgrades
    enable_family_features: bool = False
    family_member_limit: Optional[int] = None
    migrate_existing_plants: bool = True
    
    # Upgrade incentives
    bonus_ai_credits: int = 0
    free_expert_consultation: bool = False
    extended_trial: int = 0  # Additional trial days
    
    # Communication
    send_upgrade_confirmation: bool = True
    announce_premium_features: bool = True
    offer_feature_tutorial: bool = True
    
    # Context
    upgrade_reason: Optional[str] = None
    upgrade_source: str = "user"  # user, admin, automatic, promotion
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DowngradeSubscriptionCommand:
    """
    Command to downgrade subscription in the Plant Care Application.
    Handles tier downgrades with data preservation and feature restrictions.
    """
    user_id: str
    subscription_id: str
    new_tier: str  # free, premium (from expert/family)
    
    # Downgrade timing
    downgrade_timing: str = "end_of_cycle"  # immediate, end_of_cycle, custom_date
    effective_date: Optional[datetime] = None
    
    # Data preservation
    preserve_plant_data: bool = True
    preserve_photos: bool = True
    preserve_analytics_history: bool = True
    archive_excess_data: bool = True  # Archive data beyond new limits
    
    # Plant Care data handling
    handle_excess_plants: str = "archive"  # archive, delete, choose
    selected_plants_to_keep: Optional[List[str]] = None
    preserve_care_history: bool = True
    maintain_basic_reminders: bool = True
    
    # Feature restrictions
    disable_advanced_analytics: bool = True
    disable_weather_integration: bool = True
    disable_care_automation: bool = True
    disable_data_export: bool = True
    revoke_priority_support: bool = True
    
    # Expert downgrades
    maintain_expert_badge: bool = True  # Keep verification but lose features
    disable_consultations: bool = False
    reduce_consultation_visibility: bool = True
    
    # Family plan downgrades
    migrate_family_plants: str = "to_primary"  # to_primary, distribute, archive
    notify_family_members: bool = True
    preserve_shared_data: bool = True
    
    # Billing adjustments
    calculate_refund: bool = True
    refund_method: str = "original_payment"  # original_payment, credit, none
    prorate_remaining_period: bool = True
    
    # Retention efforts
    offer_discount: bool = True
    suggest_pause_instead: bool = True
    provide_downgrade_feedback: bool = True
    
    # Communication
    send_downgrade_confirmation: bool = True
    explain_feature_changes: bool = True
    offer_upgrade_path: bool = True
    
    # Context
    downgrade_reason: str
    downgrade_source: str = "user"  # user, admin, payment_failure, violation
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class CancelSubscriptionCommand:
    """
    Command to cancel subscription in the Plant Care Application.
    Handles subscription cancellation with data retention options.
    """
    user_id: str
    subscription_id: str
    
    # Cancellation timing
    cancellation_type: str = "end_of_cycle"  # immediate, end_of_cycle, scheduled
    effective_date: Optional[datetime] = None
    
    # Cancellation reason
    cancellation_reason: str
    cancellation_feedback: Optional[str] = None
    satisfaction_rating: Optional[int] = None  # 1-5 scale
    
    # Data preservation options
    preserve_account: bool = True
    preserve_plant_data: bool = True
    preserve_photos: bool = True
    preserve_care_history: bool = True
    data_retention_period: int = 365  # Days to retain data
    
    # Feature access during notice period
    maintain_premium_features: bool = True  # Until effective date
    allow_data_export: bool = True
    continue_care_reminders: bool = True
    
    # Plant Care specific handling
    convert_to_free_limits: bool = True
    archive_excess_plants: bool = True
    maintain_basic_features: bool = True
    preserve_plant_relationships: bool = True  # Following, sharing
    
    # Expert cancellations
    maintain_expert_status: bool = True
    disable_paid_consultations: bool = True
    reduce_expert_visibility: bool = True
    transfer_ongoing_consultations: bool = False
    
    # Family plan cancellations
    handle_family_members: str = "downgrade_all"  # downgrade_all, transfer_ownership, individual_choice
    notify_family_members: bool = True
    migrate_shared_plants: bool = True
    
    # Billing and refunds
    calculate_refund: bool = True
    refund_unused_portion: bool = True
    cancel_future_payments: bool = True
    final_invoice: bool = True
    
    # Retention efforts
    offer_pause_option: bool = True
    suggest_downgrade: bool = True
    provide_win_back_offer: bool = True
    schedule_follow_up: bool = True
    
    # Communication
    send_cancellation_confirmation: bool = True
    explain_data_retention: bool = True
    provide_reactivation_instructions: bool = True
    request_exit_interview: bool = True
    
    # Context
    cancelled_by: Optional[str] = None  # admin_user_id if cancelled by admin
    cancellation_source: str = "user"  # user, admin, system, payment_failure
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RenewSubscriptionCommand:
    """
    Command to renew subscription in the Plant Care Application.
    Handles subscription renewals with pricing updates and feature refreshes.
    """
    user_id: str
    subscription_id: str
    
    # Renewal details
    renewal_type: str = "auto"  # auto, manual, admin
    new_billing_cycle: Optional[str] = None
    
    # Pricing updates
    new_price: Optional[Decimal] = None
    apply_price_changes: bool = True
    honor_grandfathered_pricing: bool = True
    apply_loyalty_discount: bool = True
    
    # Payment processing
    payment_method_id: Optional[str] = None
    retry_failed_payment: bool = True
    payment_retry_attempts: int = 3
    
    # Feature limit refreshes
    reset_usage_counters: bool = True
    refresh_ai_identification_limit: bool = True
    refresh_expert_consultation_limit: bool = True
    grant_renewal_bonuses: bool = True
    
    # Plant Care renewals
    maintain_plant_limits: bool = True
    refresh_premium_features: bool = True
    update_care_automation: bool = True
    sync_weather_integration: bool = True
    
    # Renewal incentives
    bonus_ai_credits: int = 0
    free_consultation_credits: int = 0
    extended_trial_features: int = 0  # Days of trial features
    loyalty_rewards: Optional[Dict[str, Any]] = None
    
    # Family plan renewals
    renew_family_members: bool = True
    update_family_limits: bool = True
    refresh_shared_features: bool = True
    
    # Communication
    send_renewal_confirmation: bool = True
    highlight_new_features: bool = True
    provide_usage_summary: bool = True
    thank_for_loyalty: bool = True
    
    # Context
    renewal_source: str = "auto"  # auto, user, admin, recovery
    previous_renewal_date: Optional[datetime] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class StartTrialCommand:
    """
    Command to start premium trial in the Plant Care Application.
    Handles trial activation with feature unlocks and usage tracking.
    """
    user_id: str
    trial_tier: str = "premium"  # premium, expert, family
    trial_duration_days: int = 14
    
    # Trial activation
    require_payment_method: bool = False
    auto_convert_at_end: bool = True
    trial_source: str = "signup"  # signup, upgrade_prompt, referral, promotion
    
    # Feature unlocks during trial
    unlock_plant_limit: bool = True
    unlock_ai_features: bool = True
    unlock_expert_features: bool = True
    unlock_advanced_analytics: bool = True
    unlock_weather_integration: bool = True
    
    # Trial limits (reduced from full tier)
    trial_plant_limit: int = 20  # Less than full premium
    trial_ai_identification_limit: int = 50
    trial_expert_consultation_limit: int = 2
    trial_photo_storage_limit: int = 500
    
    # Plant Care trial features
    enable_care_automation: bool = True
    enable_advanced_reminders: bool = True
    enable_plant_health_insights: bool = True
    enable_growth_tracking: bool = True
    
    # Family trial features
    trial_family_member_limit: int = 3  # Less than full family plan
    enable_family_dashboard: bool = True
    enable_shared_plant_library: bool = True
    
    # Trial engagement
    send_trial_welcome: bool = True
    provide_feature_tutorials: bool = True
    track_feature_usage: bool = True
    send_trial_reminders: bool = True
    
    # Trial conversion optimization
    highlight_popular_features: bool = True
    show_usage_statistics: bool = True
    provide_personalized_recommendations: bool = True
    offer_conversion_incentives: bool = True
    
    # Trial restrictions
    watermark_exports: bool = True
    limit_api_access: bool = True
    reduce_support_priority: bool = True
    
    # Communication schedule
    send_welcome_email: bool = True
    trial_day_3_check_in: bool = True
    trial_day_7_feature_highlight: bool = True
    trial_day_12_conversion_offer: bool = True
    
    # Context
    trial_code: Optional[str] = None
    referred_by: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class PauseSubscriptionCommand:
    """
    Command to pause subscription in the Plant Care Application.
    Handles temporary subscription suspension with data preservation.
    """
    user_id: str
    subscription_id: str
    
    # Pause details
    pause_reason: str
    pause_duration_days: Optional[int] = None
    auto_resume_date: Optional[datetime] = None
    
    # Pause scope
    pause_billing: bool = True
    pause_feature_access: bool = False  # Keep basic features
    pause_notifications: bool = False
    maintain_data_access: bool = True
    
    # Plant Care during pause
    maintain_care_reminders: bool = True
    preserve_plant_data: bool = True
    reduce_ai_limits: bool = True
    pause_premium_features: bool = True
    
    # Feature restrictions during pause
    basic_plant_management: bool = True
    basic_care_reminders: bool = True
    limited_photo_storage: bool = True
    no_advanced_analytics: bool = True
    no_expert_consultations: bool = True
    
    # Communication
    send_pause_confirmation: bool = True
    explain_pause_limitations: bool = True
    provide_resume_instructions: bool = True
    
    # Context
    pause_source: str = "user"  # user, admin, system
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ResumeSubscriptionCommand:
    """
    Command to resume paused subscription in the Plant Care Application.
    Handles subscription reactivation with feature restoration.
    """
    user_id: str
    subscription_id: str
    
    # Resume details
    resume_immediately: bool = True
    update_payment_method: Optional[str] = None
    catch_up_billing: bool = True
    
    # Feature restoration
    restore_full_features: bool = True
    restore_usage_limits: bool = True
    sync_data_changes: bool = True
    restore_premium_features: bool = True
    
    # Plant Care restoration
    restore_care_automation: bool = True
    restore_advanced_analytics: bool = True
    restore_expert_consultations: bool = True
    refresh_weather_integration: bool = True
    
    # Welcome back incentives
    bonus_ai_credits: int = 0
    free_consultation_credit: bool = False
    feature_catch_up_tutorial: bool = True
    
    # Communication
    send_welcome_back_email: bool = True
    highlight_missed_features: bool = True
    provide_usage_summary: bool = True
    
    # Context
    resume_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpdatePaymentMethodCommand:
    """
    Command to update payment method for subscription.
    Handles payment method changes with validation and security.
    """
    user_id: str
    subscription_id: str
    new_payment_method_id: str
    
    # Payment method details
    payment_type: str  # credit_card, debit_card, paypal, bank_transfer
    billing_address: Optional[Dict[str, str]] = None
    set_as_default: bool = True
    
    # Security validation
    verify_payment_method: bool = True
    require_3d_secure: bool = True
    fraud_check: bool = True
    
    # Update timing
    effective_immediately: bool = True
    apply_to_next_billing: bool = False
    
    # Previous payment method
    remove_old_method: bool = False
    keep_as_backup: bool = True
    
    # Communication
    send_update_confirmation: bool = True
    confirm_next_billing_date: bool = True
    
    # Context
    update_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None