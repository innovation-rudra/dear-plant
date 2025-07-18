# app/modules/user_management/application/queries/analytics_queries.py
"""
Plant Care Application - Analytics Queries

Queries for analytics and business intelligence in the Plant Care Application.
Handles user analytics, expert performance, subscription metrics, and engagement data.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, date


@dataclass
class GetUserAnalyticsQuery:
    """
    Query to get user behavior analytics in the Plant Care Application.
    Retrieves comprehensive user engagement and activity metrics.
    """
    # Analytics scope
    user_id: Optional[str] = None  # Specific user or aggregate
    user_segment: Optional[str] = None  # beginners, experts, premium_users, etc.
    
    # Time range
    time_period: str = "month"  # week, month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # User engagement analytics
    include_login_patterns: bool = True
    include_session_analytics: bool = True
    include_feature_usage: bool = True
    include_content_interaction: bool = True
    
    # Plant Care behavior analytics
    include_plant_management_behavior: bool = True
    include_care_routine_analytics: bool = True
    include_plant_health_tracking: bool = True
    include_growth_documentation: bool = True
    
    # AI feature analytics
    include_ai_identification_usage: bool = True
    include_ai_care_suggestions: bool = True
    include_ai_health_monitoring: bool = True
    include_automated_reminder_engagement: bool = True
    
    # Social and community analytics
    include_social_interaction: bool = True
    include_expert_consultations: bool = True
    include_community_participation: bool = True
    include_content_sharing: bool = True
    
    # Learning and progression analytics
    include_skill_development: bool = True
    include_knowledge_acquisition: bool = True
    include_care_success_rates: bool = True
    include_plant_survival_rates: bool = True
    
    # Subscription and monetization
    include_subscription_engagement: bool = True
    include_premium_feature_adoption: bool = True
    include_upgrade_behavior: bool = True
    include_churn_indicators: bool = True
    
    # Device and platform analytics
    include_device_usage: bool = True
    include_platform_preferences: bool = True
    include_notification_engagement: bool = True
    include_offline_usage: bool = True
    
    # Geographic and demographic
    include_geographic_patterns: bool = True
    include_seasonal_behavior: bool = True
    include_climate_correlation: bool = True
    
    # Performance metrics
    include_task_completion_rates: bool = True
    include_feature_adoption_speed: bool = True
    include_user_satisfaction_scores: bool = True
    include_support_interaction: bool = True
    
    # Predictive analytics
    include_churn_prediction: bool = True
    include_upgrade_likelihood: bool = True
    include_engagement_forecasting: bool = True
    
    # Comparative analysis
    compare_to_cohort: bool = True
    compare_to_previous_period: bool = True
    include_percentile_rankings: bool = True
    
    # Data granularity
    daily_breakdown: bool = False
    weekly_breakdown: bool = True
    include_hourly_patterns: bool = False
    
    # Privacy and authorization
    requesting_admin_id: Optional[str] = None
    analytics_purpose: str = "product_improvement"
    anonymize_personal_data: bool = True
    
    # Performance
    use_analytics_warehouse: bool = True
    max_processing_time_seconds: int = 30
    cache_results: bool = True
    cache_ttl_hours: int = 6


@dataclass
class GetExpertAnalyticsQuery:
    """
    Query to get expert performance analytics in the Plant Care Application.
    Retrieves expert-specific metrics and consultation performance data.
    """
    expert_user_id: Optional[str] = None  # Specific expert or aggregate
    
    # Time range
    time_period: str = "month"  # week, month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Expert performance metrics
    include_consultation_metrics: bool = True
    include_response_time_analytics: bool = True
    include_client_satisfaction: bool = True
    include_expertise_effectiveness: bool = True
    
    # Consultation analytics
    include_consultation_volume: bool = True
    include_consultation_duration: bool = True
    include_consultation_outcomes: bool = True
    include_repeat_client_rate: bool = True
    
    # Client interaction analytics
    include_client_acquisition: bool = True
    include_client_retention: bool = True
    include_referral_generation: bool = True
    include_client_success_stories: bool = True
    
    # Content and knowledge sharing
    include_content_creation_metrics: bool = True
    include_tutorial_effectiveness: bool = True
    include_community_contribution: bool = True
    include_plant_identification_help: bool = True
    
    # Expert platform engagement
    include_profile_views: bool = True
    include_expert_search_visibility: bool = True
    include_booking_conversion_rate: bool = True
    include_availability_optimization: bool = True
    
    # Specialization analytics
    include_specialty_performance: bool = True
    include_plant_type_expertise: bool = True
    include_problem_solving_success: bool = True
    include_seasonal_expertise_demand: bool = True
    
    # Revenue and business metrics
    include_revenue_analytics: bool = False  # Expert or admin only
    include_pricing_effectiveness: bool = False
    include_upselling_success: bool = False
    include_consultation_profit_margin: bool = False
    
    # Geographic and market analytics
    include_geographic_reach: bool = True
    include_market_penetration: bool = True
    include_local_vs_remote_performance: bool = True
    include_timezone_optimization: bool = True
    
    # Quality and reputation metrics
    include_expert_rating_trends: bool = True
    include_review_sentiment_analysis: bool = True
    include_complaint_resolution: bool = True
    include_expert_badge_progress: bool = True
    
    # Competitive analysis
    include_market_position: bool = True
    include_specialty_ranking: bool = True
    include_pricing_competitiveness: bool = False
    
    # Growth and development
    include_skill_development: bool = True
    include_knowledge_expansion: bool = True
    include_certification_progress: bool = True
    include_mentorship_activities: bool = True
    
    # Platform contribution
    include_community_impact: bool = True
    include_knowledge_base_contributions: bool = True
    include_new_expert_mentoring: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    expert_self_analytics: bool = False
    admin_detailed_view: bool = False
    
    # Performance
    use_expert_analytics_cache: bool = True
    cache_ttl_hours: int = 4
    include_real_time_metrics: bool = False


@dataclass
class GetSubscriptionMetricsQuery:
    """
    Query to get subscription business metrics in the Plant Care Application.
    Retrieves subscription performance, conversion, and revenue analytics.
    """
    # Metrics scope
    subscription_tier: Optional[str] = None  # Specific tier or all
    user_segment: Optional[str] = None  # Geographic, demographic, behavior
    
    # Time range
    time_period: str = "quarter"  # month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Core subscription metrics
    include_subscription_growth: bool = True
    include_churn_analysis: bool = True
    include_retention_metrics: bool = True
    include_conversion_funnels: bool = True
    
    # Revenue metrics
    include_revenue_analytics: bool = False  # Admin only
    include_mrr_analysis: bool = False  # Admin only
    include_ltv_metrics: bool = False  # Admin only
    include_arpu_analysis: bool = False  # Admin only
    
    # Plant Care specific metrics
    include_feature_adoption_impact: bool = True
    include_plant_limit_utilization: bool = True
    include_ai_feature_correlation: bool = True
    include_expert_consultation_impact: bool = True
    
    # Trial and conversion metrics
    include_trial_performance: bool = True
    include_trial_to_paid_conversion: bool = True
    include_free_to_premium_conversion: bool = True
    include_upgrade_path_analysis: bool = True
    
    # Churn and retention analysis
    include_churn_prediction: bool = True
    include_churn_reasons: bool = True
    include_win_back_effectiveness: bool = True
    include_pause_vs_cancel_analysis: bool = True
    
    # Pricing and packaging analysis
    include_pricing_elasticity: bool = False  # Admin only
    include_package_preference: bool = True
    include_discount_effectiveness: bool = True
    include_promotional_impact: bool = True
    
    # Customer lifecycle metrics
    include_onboarding_effectiveness: bool = True
    include_engagement_correlation: bool = True
    include_support_impact: bool = True
    include_satisfaction_correlation: bool = True
    
    # Geographic and demographic metrics
    include_geographic_performance: bool = True
    include_demographic_analysis: bool = True
    include_seasonal_patterns: bool = True
    include_market_penetration: bool = True
    
    # Cohort analysis
    include_cohort_retention: bool = True
    include_cohort_revenue: bool = False  # Admin only
    include_cohort_behavior: bool = True
    
    # Competitive and market analysis
    include_market_share_trends: bool = False  # Admin only
    include_competitive_positioning: bool = False  # Admin only
    
    # Family plan metrics
    include_family_plan_performance: bool = True
    include_family_member_engagement: bool = True
    include_shared_feature_usage: bool = True
    
    # Privacy and authorization
    requesting_admin_id: str
    financial_access_level: str = "standard"  # standard, financial, executive
    
    # Performance
    use_metrics_warehouse: bool = True
    cache_results: bool = True
    cache_ttl_hours: int = 12
    max_processing_time_seconds: int = 45


@dataclass
class GetUserEngagementQuery:
    """
    Query to get user engagement analytics in the Plant Care Application.
    Retrieves detailed engagement patterns and user journey analytics.
    """
    # Engagement scope
    user_id: Optional[str] = None  # Specific user or aggregate
    user_cohort: Optional[str] = None  # Registration period, source, etc.
    
    # Time range
    time_period: str = "month"  # week, month, quarter, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Core engagement metrics
    include_session_analytics: bool = True
    include_daily_active_users: bool = True
    include_weekly_active_users: bool = True
    include_monthly_active_users: bool = True
    
    # Plant Care engagement
    include_plant_care_activities: bool = True
    include_care_reminder_engagement: bool = True
    include_plant_health_monitoring: bool = True
    include_growth_tracking_engagement: bool = True
    
    # Feature engagement
    include_feature_usage_depth: bool = True
    include_feature_adoption_timeline: bool = True
    include_feature_abandonment: bool = True
    include_feature_stickiness: bool = True
    
    # AI feature engagement
    include_ai_feature_interaction: bool = True
    include_ai_suggestion_acceptance: bool = True
    include_automated_feature_engagement: bool = True
    
    # Social engagement
    include_social_feature_usage: bool = True
    include_expert_interaction: bool = True
    include_community_participation: bool = True
    include_content_sharing: bool = True
    
    # Content engagement
    include_content_consumption: bool = True
    include_tutorial_completion: bool = True
    include_guide_usage: bool = True
    include_educational_content_engagement: bool = True
    
    # Notification engagement
    include_push_notification_response: bool = True
    include_email_engagement: bool = True
    include_reminder_effectiveness: bool = True
    
    # User journey analytics
    include_onboarding_engagement: bool = True
    include_feature_discovery_path: bool = True
    include_engagement_progression: bool = True
    include_drop_off_analysis: bool = True
    
    # Engagement quality metrics
    include_meaningful_interaction: bool = True
    include_task_completion_rates: bool = True
    include_goal_achievement: bool = True
    include_user_satisfaction_correlation: bool = True
    
    # Seasonal and temporal patterns
    include_seasonal_engagement: bool = True
    include_time_of_day_patterns: bool = True
    include_day_of_week_patterns: bool = True
    
    # Engagement segmentation
    include_engagement_segments: bool = True
    include_power_user_identification: bool = True
    include_at_risk_user_identification: bool = True
    
    # Predictive engagement
    include_engagement_forecasting: bool = True
    include_churn_risk_scoring: bool = True
    include_re_engagement_opportunities: bool = True
    
    # Privacy and context
    requesting_user_id: Optional[str] = None
    admin_detailed_view: bool = False
    anonymize_individual_data: bool = True
    
    # Performance
    use_engagement_cache: bool = True
    cache_ttl_hours: int = 6
    real_time_metrics: bool = False


@dataclass
class GetFeatureUsageQuery:
    """
    Query to get feature usage analytics in the Plant Care Application.
    Retrieves detailed feature adoption, usage patterns, and effectiveness metrics.
    """
    # Feature scope
    feature_category: Optional[str] = None  # plant_care, ai, social, expert, etc.
    specific_features: Optional[List[str]] = None
    
    # Time range
    time_period: str = "month"  # week, month, quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Core feature metrics
    include_adoption_rates: bool = True
    include_usage_frequency: bool = True
    include_feature_retention: bool = True
    include_feature_abandonment: bool = True
    
    # Plant Care feature usage
    include_plant_management_features: bool = True
    include_care_reminder_usage: bool = True
    include_plant_health_monitoring: bool = True
    include_growth_tracking_features: bool = True
    
    # AI feature analytics
    include_ai_identification_usage: bool = True
    include_ai_care_suggestions: bool = True
    include_automated_care_features: bool = True
    include_ai_health_diagnostics: bool = True
    
    # Premium feature usage
    include_premium_feature_adoption: bool = True
    include_advanced_analytics_usage: bool = True
    include_weather_integration_usage: bool = True
    include_data_export_usage: bool = True
    
    # Expert feature usage
    include_consultation_features: bool = True
    include_expert_search_usage: bool = True
    include_expert_booking_features: bool = True
    include_expert_communication: bool = True
    
    # Social feature usage
    include_following_features: bool = True
    include_sharing_features: bool = True
    include_community_features: bool = True
    include_discovery_features: bool = True
    
    # Mobile vs web usage
    include_platform_comparison: bool = True
    include_device_specific_usage: bool = True
    include_cross_platform_behavior: bool = True
    
    # Feature effectiveness
    include_user_satisfaction_by_feature: bool = True
    include_feature_success_metrics: bool = True
    include_feature_conversion_impact: bool = True
    include_feature_churn_correlation: bool = True
    
    # Feature discovery and adoption
    include_discovery_paths: bool = True
    include_adoption_timeline: bool = True
    include_onboarding_feature_usage: bool = True
    include_feature_recommendation_effectiveness: bool = True
    
    # Usage depth analysis
    include_power_user_features: bool = True
    include_casual_user_features: bool = True
    include_feature_combinations: bool = True
    include_workflow_analysis: bool = True
    
    # Geographic and demographic usage
    include_geographic_feature_preferences: bool = True
    include_demographic_usage_patterns: bool = True
    include_cultural_feature_adoption: bool = True
    
    # Seasonal and temporal patterns
    include_seasonal_feature_usage: bool = True
    include_time_based_usage_patterns: bool = True
    include_weather_correlated_usage: bool = True
    
    # Feature performance metrics
    include_feature_load_times: bool = True
    include_feature_error_rates: bool = True
    include_feature_completion_rates: bool = True
    
    # Privacy and authorization
    requesting_admin_id: Optional[str] = None
    product_team_access: bool = False
    
    # Performance
    use_feature_analytics_cache: bool = True
    cache_ttl_hours: int = 8
    include_real_time_usage: bool = False


@dataclass
class GetRetentionAnalyticsQuery:
    """
    Query to get user retention analytics in the Plant Care Application.
    Retrieves retention cohorts, churn analysis, and lifecycle metrics.
    """
    # Retention analysis scope
    cohort_type: str = "registration"  # registration, first_plant, subscription, etc.
    cohort_period: str = "month"  # week, month, quarter
    
    # Time range
    analysis_period: str = "year"  # quarter, year, custom
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Cohort analysis
    include_cohort_retention: bool = True
    include_cohort_size_analysis: bool = True
    include_cohort_behavior_comparison: bool = True
    include_cohort_value_analysis: bool = False  # Admin only
    
    # Retention metrics
    include_day_1_retention: bool = True
    include_day_7_retention: bool = True
    include_day_30_retention: bool = True
    include_long_term_retention: bool = True
    
    # Plant Care retention factors
    include_plant_care_correlation: bool = True
    include_first_plant_impact: bool = True
    include_care_success_correlation: bool = True
    include_expert_interaction_impact: bool = True
    
    # Feature adoption impact
    include_feature_adoption_correlation: bool = True
    include_onboarding_completion_impact: bool = True
    include_premium_feature_retention: bool = True
    include_ai_feature_retention: bool = True
    
    # Churn analysis
    include_churn_prediction: bool = True
    include_churn_reasons: bool = True
    include_churn_prevention_opportunities: bool = True
    include_win_back_analysis: bool = True
    
    # Engagement correlation
    include_engagement_retention_correlation: bool = True
    include_social_feature_retention: bool = True
    include_community_participation_impact: bool = True
    
    # Subscription retention
    include_subscription_retention: bool = True
    include_trial_retention: bool = True
    include_upgrade_retention: bool = True
    include_payment_failure_impact: bool = True
    
    # Geographic and demographic factors
    include_geographic_retention_patterns: bool = True
    include_demographic_retention_analysis: bool = True
    include_seasonal_retention_patterns: bool = True
    
    # Retention improvement analysis
    include_retention_intervention_effectiveness: bool = True
    include_re_engagement_campaign_impact: bool = True
    include_product_change_impact: bool = True
    
    # Comparative analysis
    compare_cohorts: bool = True
    benchmark_against_industry: bool = False  # Admin only
    include_competitive_retention: bool = False  # Admin only
    
    # Privacy and authorization
    requesting_admin_id: str
    analytics_access_level: str = "standard"
    
    # Performance
    use_retention_warehouse: bool = True
    cache_results: bool = True
    cache_ttl_hours: int = 24
    max_processing_time_seconds: int = 60


@dataclass
class GetCohortAnalysisQuery:
    """
    Query to get cohort analysis in the Plant Care Application.
    Retrieves user behavior analysis based on cohort segmentation.
    """
    # Cohort definition
    cohort_definition: str = "registration_month"  # registration_month, first_subscription, etc.
    cohort_size_min: int = 50  # Minimum cohort size for statistical significance
    
    # Time range
    cohort_start_date: date
    cohort_end_date: date
    analysis_periods: int = 12  # Number of periods to analyze
    
    # Cohort metrics
    include_retention_cohorts: bool = True
    include_revenue_cohorts: bool = False  # Admin only
    include_engagement_cohorts: bool = True
    include_feature_adoption_cohorts: bool = True
    
    # Plant Care cohort analysis
    include_plant_care_behavior_cohorts: bool = True
    include_care_success_cohorts: bool = True
    include_plant_survival_cohorts: bool = True
    include_expertise_development_cohorts: bool = True
    
    # Subscription cohort analysis
    include_subscription_upgrade_cohorts: bool = True
    include_trial_conversion_cohorts: bool = True
    include_churn_cohorts: bool = True
    
    # Engagement cohort analysis
    include_session_frequency_cohorts: bool = True
    include_feature_usage_cohorts: bool = True
    include_social_engagement_cohorts: bool = True
    include_content_consumption_cohorts: bool = True
    
    # Cohort comparison
    compare_acquisition_channels: bool = True
    compare_geographic_cohorts: bool = True
    compare_demographic_cohorts: bool = True
    compare_seasonal_cohorts: bool = True
    
    # Advanced cohort analysis
    include_cohort_overlap_analysis: bool = True
    include_cross_cohort_migration: bool = True
    include_cohort_lifecycle_analysis: bool = True
    
    # Statistical analysis
    include_statistical_significance: bool = True
    include_confidence_intervals: bool = True
    include_trend_analysis: bool = True
    
    # Privacy and authorization
    requesting_admin_id: str
    research_purpose: str = "product_optimization"
    
    # Performance
    use_cohort_warehouse: bool = True
    cache_results: bool = True
    cache_ttl_hours: int = 48