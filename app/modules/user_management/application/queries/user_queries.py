# app/modules/user_management/application/queries/user_queries.py
"""
Plant Care Application - User Data Queries

Queries for user data retrieval in the Plant Care Application.
Handles user lookup, dashboard data, statistics, and search operations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, date


@dataclass
class GetUserByIdQuery:
    """
    Query to get user by ID in the Plant Care Application.
    Retrieves complete user information with Plant Care context.
    """
    user_id: str
    
    # Data inclusion options
    include_profile: bool = True
    include_subscription: bool = True
    include_preferences: bool = False
    include_security_info: bool = False
    
    # Plant Care specific includes
    include_plant_count: bool = True
    include_care_stats: bool = False
    include_expert_info: bool = True
    include_social_stats: bool = True
    
    # Performance options
    use_cache: bool = True
    cache_ttl_minutes: int = 15
    minimal_data: bool = False  # Return only essential fields
    
    # Privacy context
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    admin_override: bool = False
    
    # Data freshness
    max_age_minutes: Optional[int] = None
    force_refresh: bool = False


@dataclass
class GetUserByEmailQuery:
    """
    Query to get user by email address in the Plant Care Application.
    Handles email-based user lookup with security considerations.
    """
    email: str
    
    # Security options
    case_sensitive: bool = False
    exact_match_only: bool = True
    include_inactive_users: bool = False
    
    # Data inclusion
    include_profile: bool = True
    include_subscription: bool = False
    include_verification_status: bool = True
    
    # Plant Care context
    include_expert_status: bool = True
    include_registration_source: bool = False
    
    # Privacy and security
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    audit_lookup: bool = True  # Log email lookups for security
    
    # Performance
    use_cache: bool = False  # Don't cache email lookups for security
    timeout_seconds: int = 5


@dataclass
class GetUserDashboardQuery:
    """
    Query to get user dashboard data in the Plant Care Application.
    Retrieves comprehensive dashboard information with Plant Care metrics.
    """
    user_id: str
    
    # Dashboard sections
    include_plant_summary: bool = True
    include_care_reminders: bool = True
    include_recent_activity: bool = True
    include_social_updates: bool = True
    include_expert_recommendations: bool = True
    
    # Plant Care dashboard data
    include_care_calendar: bool = True
    include_plant_health_alerts: bool = True
    include_weather_integration: bool = True
    include_ai_suggestions: bool = True
    
    # Time range for activity data
    activity_days: int = 7
    reminder_days: int = 3
    
    # Feature usage dashboard
    include_ai_usage: bool = True
    include_consultation_history: bool = True
    include_subscription_status: bool = True
    include_feature_highlights: bool = True
    
    # Social dashboard
    include_follower_updates: bool = True
    include_expert_content: bool = True
    include_community_highlights: bool = True
    
    # Personalization
    personalize_content: bool = True
    user_timezone: Optional[str] = None
    preferred_units: Optional[str] = None
    
    # Performance options
    use_cache: bool = True
    cache_ttl_minutes: int = 30
    preload_images: bool = False
    
    # Data pagination
    max_activity_items: int = 10
    max_reminders: int = 20
    max_social_updates: int = 15


@dataclass
class GetUserStatsQuery:
    """
    Query to get user statistics in the Plant Care Application.
    Retrieves user metrics and Plant Care performance data.
    """
    user_id: str
    
    # Stats time range
    time_period: str = "all_time"  # all_time, year, month, week
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Plant Care stats
    include_plant_stats: bool = True
    include_care_stats: bool = True
    include_growth_tracking: bool = True
    include_health_metrics: bool = True
    
    # User activity stats
    include_login_stats: bool = True
    include_feature_usage: bool = True
    include_engagement_metrics: bool = True
    include_streak_data: bool = True
    
    # Social stats
    include_social_metrics: bool = True
    include_expert_interactions: bool = True
    include_community_participation: bool = True
    
    # Expert-specific stats
    include_expert_metrics: bool = False
    include_consultation_stats: bool = False
    include_content_creation: bool = False
    
    # Subscription stats
    include_subscription_usage: bool = True
    include_feature_adoption: bool = True
    include_upgrade_history: bool = False
    
    # Comparison data
    include_percentiles: bool = True
    compare_to_cohort: bool = True
    anonymize_comparisons: bool = True
    
    # Data granularity
    detailed_breakdown: bool = False
    include_daily_data: bool = False
    include_trends: bool = True


@dataclass
class SearchUsersQuery:
    """
    Query to search users in the Plant Care Application.
    Handles user search with Plant Care context and filters.
    """
    # Search parameters
    search_term: Optional[str] = None
    search_fields: List[str] = field(default_factory=lambda: ["display_name", "bio"])
    
    # User filters
    user_status: Optional[str] = None  # active, inactive, suspended
    user_role: Optional[str] = None  # user, expert, moderator, admin
    verified_email: Optional[bool] = None
    
    # Plant Care filters
    experience_level: Optional[str] = None  # beginner, intermediate, advanced, expert
    expert_verified: Optional[bool] = None
    has_plants: Optional[bool] = None
    plant_count_min: Optional[int] = None
    plant_count_max: Optional[int] = None
    
    # Geographic filters
    location: Optional[str] = None
    country: Optional[str] = None
    radius_km: Optional[float] = None
    center_coordinates: Optional[Dict[str, float]] = None  # lat, lng
    
    # Activity filters
    last_active_days: Optional[int] = None
    registration_date_from: Optional[date] = None
    registration_date_to: Optional[date] = None
    
    # Social filters
    has_followers: Optional[bool] = None
    follower_count_min: Optional[int] = None
    following_count_min: Optional[int] = None
    
    # Expert filters
    expert_specialties: Optional[List[str]] = None
    consultation_available: Optional[bool] = None
    expert_rating_min: Optional[float] = None
    
    # Subscription filters
    subscription_tier: Optional[str] = None  # free, premium, expert, family
    trial_status: Optional[str] = None  # active, expired, converted, none
    
    # Search options
    exact_match: bool = False
    case_sensitive: bool = False
    include_inactive: bool = False
    
    # Sorting and pagination
    sort_by: str = "relevance"  # relevance, name, date_joined, last_active, plant_count
    sort_order: str = "desc"  # asc, desc
    page: int = 1
    page_size: int = 20
    max_results: int = 1000
    
    # Data inclusion
    include_profile_preview: bool = True
    include_plant_preview: bool = True
    include_expert_preview: bool = True
    
    # Privacy and security
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    admin_search: bool = False
    
    # Performance
    use_search_index: bool = True
    timeout_seconds: int = 10


@dataclass
class GetUserActivityQuery:
    """
    Query to get user activity history in the Plant Care Application.
    Retrieves user actions and Plant Care interactions.
    """
    user_id: str
    
    # Activity time range
    days_back: int = 30
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    
    # Activity types
    include_login_activity: bool = True
    include_plant_care_actions: bool = True
    include_social_interactions: bool = True
    include_content_creation: bool = True
    include_feature_usage: bool = True
    
    # Plant Care specific activities
    include_watering_logs: bool = True
    include_fertilizing_logs: bool = True
    include_photo_uploads: bool = True
    include_plant_additions: bool = True
    include_care_reminders: bool = True
    
    # Social activities
    include_follows: bool = True
    include_likes: bool = True
    include_comments: bool = True
    include_shares: bool = True
    
    # Expert activities
    include_consultations: bool = True
    include_expert_content: bool = True
    include_community_help: bool = True
    
    # Subscription activities
    include_subscription_changes: bool = True
    include_feature_adoptions: bool = True
    include_billing_events: bool = False
    
    # Activity details
    include_device_info: bool = False
    include_ip_address: bool = False  # Admin only
    include_user_agent: bool = False
    
    # Aggregation options
    group_by_day: bool = False
    group_by_activity_type: bool = False
    include_activity_counts: bool = True
    
    # Privacy
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    anonymize_sensitive_data: bool = True
    
    # Pagination
    page: int = 1
    page_size: int = 50
    max_activities: int = 1000


@dataclass
class GetUserPreferencesQuery:
    """
    Query to get user preferences in the Plant Care Application.
    Retrieves user settings and Plant Care preferences.
    """
    user_id: str
    
    # Preference categories
    include_plant_care_preferences: bool = True
    include_notification_preferences: bool = True
    include_privacy_preferences: bool = True
    include_display_preferences: bool = True
    
    # Plant Care preferences
    include_care_schedules: bool = True
    include_reminder_settings: bool = True
    include_weather_preferences: bool = True
    include_ai_preferences: bool = True
    
    # Communication preferences
    include_email_preferences: bool = True
    include_push_preferences: bool = True
    include_marketing_preferences: bool = True
    
    # Social preferences
    include_privacy_settings: bool = True
    include_follow_preferences: bool = True
    include_sharing_preferences: bool = True
    
    # Expert preferences (if applicable)
    include_consultation_preferences: bool = True
    include_expert_visibility: bool = True
    include_content_preferences: bool = True
    
    # App preferences
    include_ui_preferences: bool = True
    include_unit_preferences: bool = True
    include_language_preferences: bool = True
    
    # Data format
    flatten_preferences: bool = False
    include_defaults: bool = True
    include_preference_history: bool = False
    
    # Privacy context
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    mask_sensitive_preferences: bool = True


@dataclass
class GetUserSecurityInfoQuery:
    """
    Query to get user security information in the Plant Care Application.
    Retrieves security-related data for admin and security purposes.
    """
    user_id: str
    
    # Security info categories
    include_login_history: bool = True
    include_device_info: bool = True
    include_security_events: bool = True
    include_2fa_status: bool = True
    
    # Login and session data
    include_active_sessions: bool = True
    include_failed_attempts: bool = True
    include_password_history: bool = False  # Admin only
    include_oauth_connections: bool = True
    
    # Device and location data
    include_trusted_devices: bool = True
    include_login_locations: bool = True
    include_suspicious_activity: bool = True
    
    # Security settings
    include_privacy_settings: bool = True
    include_account_locks: bool = True
    include_verification_status: bool = True
    
    # Plant Care security
    include_data_access_logs: bool = True
    include_sharing_permissions: bool = True
    include_expert_verification: bool = True
    
    # Time range for security data
    days_back: int = 90
    include_all_time_summary: bool = True
    
    # Security analysis
    include_risk_assessment: bool = True
    include_security_score: bool = True
    include_recommendations: bool = True
    
    # Data sensitivity
    mask_ip_addresses: bool = True
    anonymize_locations: bool = False
    include_raw_logs: bool = False
    
    # Authorization
    requesting_admin_id: str
    security_clearance_level: str = "standard"  # standard, elevated, admin
    audit_request: bool = True
    
    # Performance
    max_login_records: int = 100
    max_security_events: int = 50
    use_security_cache: bool = True