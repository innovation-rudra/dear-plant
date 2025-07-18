# app/modules/user_management/application/queries/subscription_queries.py
"""
Plant Care Application - Subscription Data Queries

Queries for subscription data retrieval in the Plant Care Application.
Handles subscription details, usage tracking, billing history, and analytics.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, date
from decimal import Decimal


@dataclass
class GetUserSubscriptionQuery:
    """
    Query to get user subscription details in the Plant Care Application.
    Retrieves complete subscription information with Plant Care feature access.
    """
    user_id: str
    
    # Subscription data inclusion
    include_basic_details: bool = True
    include_feature_limits: bool = True
    include_usage_summary: bool = True
    include_billing_info: bool = False  # Sensitive data
    
    # Plant Care feature details
    include_plant_limits: bool = True
    include_ai_credits: bool = True
    include_expert_consultation_access: bool = True
    include_premium_features: bool = True
    
    # Usage and limits
    include_current_usage: bool = True
    include_usage_history: bool = False
    include_overage_info: bool = True
    include_remaining_credits: bool = True
    
    # Subscription status
    include_trial_info: bool = True
    include_renewal_info: bool = True
    include_cancellation_info: bool = True
    include_upgrade_eligibility: bool = True
    
    # Family plan details
    include_family_members: bool = True
    include_shared_features: bool = True
    include_family_usage: bool = True
    
    # Billing and payment
    include_next_billing_date: bool = True
    include_payment_method: bool = False  # Admin only
    include_billing_history_summary: bool = False
    include_proration_info: bool = True
    
    # Feature access details
    include_feature_flags: bool = True
    include_beta_access: bool = True
    include_api_access: bool = True
    include_integration_limits: bool = True
    
    # Promotional and discount info
    include_active_promotions: bool = True
    include_referral_credits: bool = True
    include_loyalty_benefits: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    include_sensitive_data: bool = False
    
    # Performance
    use_cache: bool = True
    cache_ttl_minutes: int = 30
    real_time_usage: bool = False  # Get real-time vs cached usage


@dataclass
class GetSubscriptionUsageQuery:
    """
    Query to get subscription usage data in the Plant Care Application.
    Retrieves detailed feature usage and limits tracking.
    """
    user_id: str
    
    # Usage time range
    time_period: str = "current_month"  # current_month, last_month, custom, all_time
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Plant Care feature usage
    include_ai_identification_usage: bool = True
    include_expert_consultation_usage: bool = True
    include_plant_management_usage: bool = True
    include_premium_feature_usage: bool = True
    
    # AI and automation usage
    include_ai_plant_health: bool = True
    include_ai_care_suggestions: bool = True
    include_automated_reminders: bool = True
    include_weather_integration_usage: bool = True
    
    # Expert and consultation usage
    include_consultation_minutes: bool = True
    include_expert_messaging: bool = True
    include_priority_support_usage: bool = True
    
    # Storage and content usage
    include_photo_storage_usage: bool = True
    include_data_export_usage: bool = True
    include_backup_usage: bool = True
    
    # Family plan usage
    include_family_member_usage: bool = True
    include_shared_feature_usage: bool = True
    include_family_limits: bool = True
    
    # API and integration usage
    include_api_calls: bool = True
    include_third_party_integrations: bool = True
    include_webhook_usage: bool = True
    
    # Usage analytics
    include_usage_trends: bool = True
    include_peak_usage_times: bool = True
    include_usage_efficiency: bool = True
    include_feature_adoption: bool = True
    
    # Limit and overage tracking
    include_limit_approaches: bool = True
    include_overage_charges: bool = True
    include_usage_alerts: bool = True
    include_optimization_suggestions: bool = True
    
    # Comparative data
    compare_to_previous_period: bool = True
    compare_to_plan_average: bool = True
    include_percentile_ranking: bool = True
    
    # Data granularity
    daily_breakdown: bool = False
    weekly_breakdown: bool = True
    feature_level_breakdown: bool = True
    
    # Privacy and context
    requesting_user_id: Optional[str] = None
    admin_detailed_view: bool = False
    include_cost_analysis: bool = False
    
    # Performance
    use_usage_cache: bool = True
    cache_ttl_minutes: int = 15
    real_time_limits: bool = True


@dataclass
class GetSubscriptionAnalyticsQuery:
    """
    Query to get subscription analytics in the Plant Care Application.
    Retrieves subscription performance and business metrics.
    """
    # Analytics scope
    user_id: Optional[str] = None  # Specific user or aggregate
    subscription_tier: Optional[str] = None  # Specific tier analysis
    
    # Time range
    time_period: str = "quarter"  # month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Subscription metrics
    include_subscription_health: bool = True
    include_churn_analysis: bool = True
    include_upgrade_patterns: bool = True
    include_retention_metrics: bool = True
    
    # Plant Care specific analytics
    include_feature_adoption_rates: bool = True
    include_plant_care_engagement: bool = True
    include_ai_feature_usage: bool = True
    include_expert_consultation_trends: bool = True
    
    # Financial analytics
    include_revenue_metrics: bool = False  # Admin only
    include_ltv_analysis: bool = False  # Admin only
    include_pricing_effectiveness: bool = False  # Admin only
    
    # User behavior analytics
    include_usage_patterns: bool = True
    include_engagement_correlation: bool = True
    include_satisfaction_metrics: bool = True
    include_support_interaction: bool = True
    
    # Conversion analytics
    include_trial_conversion: bool = True
    include_upgrade_conversion: bool = True
    include_referral_effectiveness: bool = True
    include_promotional_impact: bool = True
    
    # Cohort and segmentation
    include_cohort_analysis: bool = True
    include_segment_performance: bool = True
    include_demographic_analysis: bool = True
    include_geographic_analysis: bool = True
    
    # Predictive analytics
    include_churn_prediction: bool = True
    include_upgrade_likelihood: bool = True
    include_usage_forecasting: bool = True
    include_revenue_prediction: bool = False  # Admin only
    
    # Comparative analysis
    compare_tier_performance: bool = True
    benchmark_against_industry: bool = False  # Admin only
    include_seasonal_patterns: bool = True
    
    # Data aggregation
    aggregation_level: str = "user"  # user, tier, cohort, total
    include_statistical_analysis: bool = True
    confidence_intervals: bool = True
    
    # Authorization and privacy
    requesting_admin_id: Optional[str] = None
    analytics_clearance_level: str = "standard"  # standard, financial, executive
    anonymize_user_data: bool = True
    
    # Performance
    use_analytics_warehouse: bool = True
    max_processing_time_seconds: int = 30
    cache_results: bool = True
    cache_ttl_hours: int = 6


@dataclass
class GetExpiringTrialsQuery:
    """
    Query to get expiring trials in the Plant Care Application.
    Retrieves trial subscriptions approaching expiration for conversion campaigns.
    """
    # Expiration time frame
    expires_in_days: int = 7
    expired_in_last_days: Optional[int] = None
    include_expired: bool = False
    
    # Trial filters
    trial_tier: Optional[str] = None  # premium, expert, family
    trial_duration: Optional[int] = None  # Trial length in days
    trial_source: Optional[str] = None  # signup, upgrade_prompt, referral
    
    # User engagement filters
    min_login_count: Optional[int] = None
    min_feature_usage: Optional[int] = None
    has_plants_added: Optional[bool] = None
    used_ai_features: Optional[bool] = None
    
    # Plant Care engagement
    active_plant_care: Optional[bool] = None
    used_expert_consultation: Optional[bool] = None
    completed_onboarding: Optional[bool] = None
    set_care_reminders: Optional[bool] = None
    
    # Conversion likelihood
    high_engagement_only: bool = False
    conversion_score_min: Optional[float] = None
    showed_upgrade_interest: Optional[bool] = None
    
    # Geographic and demographic
    country: Optional[str] = None
    timezone: Optional[str] = None
    registration_source: Optional[str] = None
    
    # Communication preferences
    email_notifications_enabled: bool = True
    marketing_consent: Optional[bool] = None
    previous_trial_attempts: Optional[int] = None
    
    # Data inclusion
    include_trial_usage_summary: bool = True
    include_engagement_metrics: bool = True
    include_conversion_probability: bool = True
    include_recommended_actions: bool = True
    include_personalized_offers: bool = True
    
    # Trial analysis
    include_feature_adoption: bool = True
    include_onboarding_completion: bool = True
    include_support_interactions: bool = True
    include_plant_care_progress: bool = True
    
    # Sorting and prioritization
    sort_by: str = "expiration_date"  # expiration_date, engagement_score, conversion_likelihood
    prioritize_high_engagement: bool = True
    prioritize_recent_activity: bool = True
    
    # Privacy and authorization
    requesting_admin_id: str
    marketing_campaign_id: Optional[str] = None
    
    # Pagination
    page: int = 1
    page_size: int = 100
    max_results: int = 1000
    
    # Performance
    use_trial_cache: bool = True
    cache_ttl_hours: int = 4


@dataclass
class GetSubscriptionHistoryQuery:
    """
    Query to get subscription history in the Plant Care Application.
    Retrieves subscription changes, upgrades, downgrades, and billing history.
    """
    user_id: str
    
    # History time range
    time_period: str = "all_time"  # last_year, all_time, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # History types
    include_subscription_changes: bool = True
    include_billing_history: bool = True
    include_usage_history: bool = True
    include_support_history: bool = True
    
    # Subscription change history
    include_tier_changes: bool = True
    include_plan_modifications: bool = True
    include_feature_additions: bool = True
    include_cancellations: bool = True
    include_reactivations: bool = True
    
    # Billing and payment history
    include_payment_history: bool = True
    include_refund_history: bool = True
    include_proration_history: bool = True
    include_discount_history: bool = True
    include_failed_payments: bool = True
    
    # Plant Care feature history
    include_feature_usage_evolution: bool = True
    include_plant_limit_changes: bool = True
    include_ai_credit_history: bool = True
    include_consultation_history: bool = True
    
    # Trial and promotional history
    include_trial_history: bool = True
    include_promotional_usage: bool = True
    include_referral_credits: bool = True
    include_loyalty_rewards: bool = True
    
    # Family plan history
    include_family_member_changes: bool = True
    include_family_feature_usage: bool = True
    include_shared_benefits_history: bool = True
    
    # Support and service history
    include_support_tickets: bool = True
    include_account_issues: bool = True
    include_billing_disputes: bool = True
    include_feature_requests: bool = True
    
    # Data detail level
    summary_only: bool = False
    include_transaction_details: bool = True
    include_change_reasons: bool = True
    include_user_feedback: bool = True
    
    # Financial details
    include_amounts: bool = True
    include_tax_details: bool = False  # Admin only
    include_payment_methods: bool = False  # Admin only
    currency_conversion: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    include_sensitive_financial: bool = False
    
    # Sorting and organization
    sort_by: str = "date"  # date, type, amount
    sort_order: str = "desc"
    group_by_month: bool = False
    
    # Pagination
    page: int = 1
    page_size: int = 50
    max_history_items: int = 500
    
    # Performance
    use_history_cache: bool = True
    cache_ttl_hours: int = 24


@dataclass
class GetUsageReportsQuery:
    """
    Query to get usage reports in the Plant Care Application.
    Retrieves detailed usage reports for analysis and billing purposes.
    """
    # Report scope
    user_id: Optional[str] = None  # Specific user or aggregate
    organization_id: Optional[str] = None  # For family plans
    
    # Report time range
    report_period: str = "month"  # day, week, month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Report types
    report_types: List[str] = field(default_factory=lambda: ["usage", "limits", "billing"])
    detailed_breakdown: bool = True
    executive_summary: bool = False
    
    # Plant Care usage reports
    include_plant_management: bool = True
    include_ai_feature_usage: bool = True
    include_expert_consultations: bool = True
    include_premium_features: bool = True
    
    # Feature-specific usage
    ai_identification_details: bool = True
    plant_health_monitoring: bool = True
    care_automation_usage: bool = True
    weather_integration_usage: bool = True
    
    # Storage and data usage
    photo_storage_usage: bool = True
    data_export_usage: bool = True
    backup_and_sync_usage: bool = True
    api_usage_details: bool = True
    
    # Family plan reporting
    family_member_breakdown: bool = True
    shared_feature_usage: bool = True
    family_limit_utilization: bool = True
    
    # Usage efficiency metrics
    feature_adoption_rates: bool = True
    usage_optimization_suggestions: bool = True
    underutilized_features: bool = True
    overuse_patterns: bool = True
    
    # Billing correlation
    usage_to_billing_correlation: bool = True
    overage_analysis: bool = True
    cost_optimization_opportunities: bool = True
    upgrade_recommendations: bool = True
    
    # Comparative analysis
    compare_to_previous_period: bool = True
    compare_to_plan_averages: bool = True
    industry_benchmarking: bool = False  # Admin only
    
    # Report format options
    include_charts_data: bool = True
    include_trend_analysis: bool = True
    include_forecasting: bool = True
    export_format: str = "json"  # json, csv, pdf
    
    # Data aggregation
    aggregation_level: str = "daily"  # hourly, daily, weekly
    include_peak_usage: bool = True
    include_usage_patterns: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    admin_report: bool = False
    billing_team_access: bool = False
    
    # Performance
    use_report_cache: bool = True
    cache_ttl_hours: int = 12
    max_report_generation_time: int = 60  # seconds


@dataclass
class GetBillingHistoryQuery:
    """
    Query to get billing history in the Plant Care Application.
    Retrieves detailed billing and payment information.
    """
    user_id: str
    
    # Billing history time range
    time_period: str = "year"  # month, quarter, year, all_time, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Billing data types
    include_invoices: bool = True
    include_payments: bool = True
    include_refunds: bool = True
    include_adjustments: bool = True
    include_credits: bool = True
    
    # Invoice details
    include_invoice_line_items: bool = True
    include_tax_breakdown: bool = True
    include_discount_details: bool = True
    include_proration_details: bool = True
    
    # Payment information
    include_payment_methods: bool = False  # Sensitive
    include_payment_status: bool = True
    include_failed_payments: bool = True
    include_retry_attempts: bool = True
    
    # Plant Care billing specifics
    include_overage_charges: bool = True
    include_feature_based_billing: bool = True
    include_consultation_billing: bool = True
    include_storage_charges: bool = True
    
    # Subscription billing
    include_subscription_changes: bool = True
    include_upgrade_prorations: bool = True
    include_trial_conversions: bool = True
    include_family_plan_billing: bool = True
    
    # Credits and promotions
    include_referral_credits: bool = True
    include_promotional_discounts: bool = True
    include_loyalty_credits: bool = True
    include_refund_credits: bool = True
    
    # Billing analysis
    include_billing_trends: bool = True
    include_cost_analysis: bool = True
    include_payment_pattern_analysis: bool = True
    
    # Currency and localization
    convert_to_user_currency: bool = True
    include_exchange_rates: bool = True
    localize_tax_information: bool = True
    
    # Document access
    include_invoice_urls: bool = True
    include_receipt_urls: bool = True
    include_statement_urls: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    admin_access: bool = False
    billing_team_access: bool = False
    mask_payment_details: bool = True
    
    # Sorting and filtering
    sort_by: str = "date"  # date, amount, type, status
    sort_order: str = "desc"
    filter_by_status: Optional[str] = None  # paid, pending, failed, refunded
    
    # Pagination
    page: int = 1
    page_size: int = 25
    max_billing_records: int = 500
    
    # Performance
    use_billing_cache: bool = True
    cache_ttl_hours: int = 6