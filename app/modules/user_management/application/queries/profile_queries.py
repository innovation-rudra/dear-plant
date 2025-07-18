# app/modules/user_management/application/queries/profile_queries.py
"""
Plant Care Application - Profile Data Queries

Queries for profile data retrieval in the Plant Care Application.
Handles profile lookup, expert searches, social connections, and location-based queries.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime, date


@dataclass
class GetProfileByUserIdQuery:
    """
    Query to get profile by user ID in the Plant Care Application.
    Retrieves complete profile information with Plant Care context.
    """
    user_id: str
    
    # Profile data inclusion
    include_basic_info: bool = True
    include_plant_care_preferences: bool = True
    include_notification_preferences: bool = True
    include_expert_info: bool = True
    
    # Plant Care specific data
    include_plant_count: bool = True
    include_care_statistics: bool = True
    include_growth_tracking: bool = True
    include_specialties: bool = True
    
    # Social data
    include_follower_info: bool = True
    include_following_info: bool = True
    include_social_stats: bool = True
    include_recent_activity: bool = False
    
    # Expert profile data
    include_expert_credentials: bool = True
    include_consultation_info: bool = True
    include_expert_ratings: bool = True
    include_verification_details: bool = False
    
    # Profile completion and analytics
    include_completion_score: bool = True
    include_profile_analytics: bool = False
    include_engagement_metrics: bool = False
    
    # Privacy and visibility
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    check_blocking_status: bool = True
    admin_override: bool = False
    
    # Performance options
    use_cache: bool = True
    cache_ttl_minutes: int = 15
    preload_images: bool = False
    minimal_data: bool = False


@dataclass
class GetExpertProfilesQuery:
    """
    Query to get verified expert profiles in the Plant Care Application.
    Retrieves expert profiles with consultation and expertise information.
    """
    # Expert filters
    verification_status: str = "verified"  # verified, pending, all
    specialties: Optional[List[str]] = None
    experience_level: Optional[str] = None
    
    # Consultation filters
    consultation_available: Optional[bool] = None
    consultation_price_min: Optional[float] = None
    consultation_price_max: Optional[float] = None
    response_time_max_hours: Optional[int] = None
    
    # Rating and performance filters
    min_rating: Optional[float] = None
    min_consultation_count: Optional[int] = None
    min_review_count: Optional[int] = None
    
    # Geographic filters
    location: Optional[str] = None
    country: Optional[str] = None
    radius_km: Optional[float] = None
    center_coordinates: Optional[Dict[str, float]] = None
    timezone: Optional[str] = None
    
    # Availability filters
    available_now: Optional[bool] = None
    available_this_week: Optional[bool] = None
    consultation_types: Optional[List[str]] = None
    
    # Plant Care expertise
    plant_types: Optional[List[str]] = None  # indoor, outdoor, succulents, etc.
    care_specialties: Optional[List[str]] = None  # pest_control, propagation, etc.
    difficulty_levels: Optional[List[str]] = None  # beginner_friendly, advanced, etc.
    
    # Social and content filters
    min_followers: Optional[int] = None
    content_creator: Optional[bool] = None  # Has created guides/articles
    community_active: Optional[bool] = None
    
    # Sorting options
    sort_by: str = "rating"  # rating, price, response_time, experience, popularity
    sort_order: str = "desc"
    featured_first: bool = True
    
    # Data inclusion
    include_consultation_details: bool = True
    include_availability_calendar: bool = False
    include_portfolio_samples: bool = True
    include_client_reviews: bool = True
    include_credentials_summary: bool = True
    
    # Pagination
    page: int = 1
    page_size: int = 20
    max_results: int = 200
    
    # Privacy context
    requesting_user_id: Optional[str] = None
    show_contact_info: bool = False
    
    # Performance
    use_search_index: bool = True
    cache_results: bool = True
    timeout_seconds: int = 10


@dataclass
class GetProfileFollowersQuery:
    """
    Query to get profile followers in the Plant Care Application.
    Retrieves users following a specific profile with relationship context.
    """
    profile_user_id: str
    
    # Follower filters
    follower_type: str = "all"  # all, experts, regular_users, mutual
    verified_only: bool = False
    active_followers_only: bool = True
    
    # Plant Care context filters
    experience_level: Optional[str] = None
    has_plants: Optional[bool] = None
    expert_followers: Optional[bool] = None
    
    # Activity filters
    followed_since_days: Optional[int] = None
    last_active_days: Optional[int] = None
    engagement_level: Optional[str] = None  # high, medium, low
    
    # Geographic filters
    same_location: Optional[bool] = None
    country: Optional[str] = None
    
    # Social filters
    mutual_followers: Optional[bool] = None
    mutual_following: Optional[bool] = None
    
    # Data inclusion
    include_follower_profiles: bool = True
    include_follow_date: bool = True
    include_interaction_history: bool = False
    include_plant_interests: bool = True
    include_mutual_connections: bool = True
    
    # Privacy and permissions
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    show_private_profiles: bool = False
    check_blocking_status: bool = True
    
    # Sorting
    sort_by: str = "follow_date"  # follow_date, last_active, interaction_level, alphabetical
    sort_order: str = "desc"
    prioritize_experts: bool = False
    
    # Pagination
    page: int = 1
    page_size: int = 50
    max_followers: int = 1000
    
    # Performance
    use_cache: bool = True
    cache_ttl_minutes: int = 30
    load_profile_images: bool = True


@dataclass
class GetProfileFollowingQuery:
    """
    Query to get profiles being followed by a user in the Plant Care Application.
    Retrieves users that a specific profile follows with relationship context.
    """
    profile_user_id: str
    
    # Following filters
    following_type: str = "all"  # all, experts, regular_users, mutual
    verified_experts_only: bool = False
    active_following_only: bool = True
    
    # Plant Care context filters
    expert_following: Optional[bool] = None
    specialties_of_interest: Optional[List[str]] = None
    similar_experience_level: Optional[bool] = None
    
    # Activity and engagement filters
    recently_followed: Optional[int] = None  # Days
    high_interaction: Optional[bool] = None
    consultation_history: Optional[bool] = None
    
    # Content preferences
    content_creators: Optional[bool] = None
    tutorial_creators: Optional[bool] = None
    active_community_members: Optional[bool] = None
    
    # Geographic preferences
    local_following: Optional[bool] = None
    same_timezone: Optional[bool] = None
    
    # Data inclusion
    include_following_profiles: bool = True
    include_follow_date: bool = True
    include_interaction_summary: bool = True
    include_shared_interests: bool = True
    include_recent_activity: bool = False
    
    # Plant Care insights
    include_plant_inspiration: bool = True
    include_care_tips_received: bool = False
    include_consultation_opportunities: bool = True
    
    # Privacy and permissions
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    show_private_profiles: bool = False
    
    # Sorting
    sort_by: str = "interaction_level"  # follow_date, interaction_level, last_active, alphabetical
    sort_order: str = "desc"
    prioritize_experts: bool = True
    
    # Pagination
    page: int = 1
    page_size: int = 50
    max_following: int = 1000
    
    # Performance
    use_cache: bool = True
    cache_ttl_minutes: int = 30
    include_preview_images: bool = True


@dataclass
class SearchProfilesQuery:
    """
    Query to search profiles in the Plant Care Application.
    Handles profile search with Plant Care expertise and location filters.
    """
    # Search parameters
    search_term: Optional[str] = None
    search_fields: List[str] = field(default_factory=lambda: ["display_name", "bio", "specialties"])
    
    # Profile type filters
    profile_type: str = "all"  # all, experts, regular_users, content_creators
    verified_experts_only: bool = False
    consultation_available: Optional[bool] = None
    
    # Plant Care expertise filters
    specialties: Optional[List[str]] = None
    experience_levels: Optional[List[str]] = None
    plant_types_expertise: Optional[List[str]] = None
    care_difficulties: Optional[List[str]] = None
    
    # Geographic search
    location: Optional[str] = None
    country: Optional[str] = None
    radius_km: Optional[float] = None
    center_coordinates: Optional[Dict[str, float]] = None
    timezone_preference: Optional[str] = None
    
    # Profile quality filters
    min_completion_score: Optional[int] = None
    has_avatar: Optional[bool] = None
    has_bio: Optional[bool] = None
    verified_email: Optional[bool] = None
    
    # Activity filters
    last_active_days: Optional[int] = None
    recently_joined: Optional[int] = None  # Days since registration
    active_community_member: Optional[bool] = None
    
    # Social filters
    min_followers: Optional[int] = None
    min_following: Optional[int] = None
    mutual_connections: Optional[bool] = None
    
    # Plant Care activity filters
    has_plants: Optional[bool] = None
    min_plant_count: Optional[int] = None
    recently_active_care: Optional[int] = None  # Days since last plant activity
    shares_plant_content: Optional[bool] = None
    
    # Expert-specific filters
    consultation_price_range: Optional[Dict[str, float]] = None  # min, max
    expert_rating_min: Optional[float] = None
    consultation_count_min: Optional[int] = None
    response_time_max: Optional[int] = None  # Hours
    
    # Content and contribution filters
    content_creator: Optional[bool] = None
    tutorial_creator: Optional[bool] = None
    community_helper: Optional[bool] = None
    plant_identifier: Optional[bool] = None  # Helps with plant ID
    
    # Search behavior
    exact_match: bool = False
    fuzzy_search: bool = True
    search_boost_verified: bool = True
    search_boost_local: bool = True
    
    # Sorting and ranking
    sort_by: str = "relevance"  # relevance, distance, rating, activity, followers
    sort_order: str = "desc"
    boost_experts: bool = True
    boost_nearby: bool = True
    boost_recently_active: bool = True
    
    # Data inclusion
    include_profile_preview: bool = True
    include_expertise_summary: bool = True
    include_availability_info: bool = True
    include_location_info: bool = True
    include_social_proof: bool = True
    
    # Privacy and context
    requesting_user_id: Optional[str] = None
    respect_privacy_settings: bool = True
    show_contact_info: bool = False
    check_blocking_status: bool = True
    
    # Pagination
    page: int = 1
    page_size: int = 20
    max_results: int = 500
    
    # Performance
    use_search_index: bool = True
    enable_autocomplete: bool = False
    search_timeout_seconds: int = 10
    cache_results: bool = True


@dataclass
class GetProfileAnalyticsQuery:
    """
    Query to get profile analytics in the Plant Care Application.
    Retrieves profile performance metrics and engagement data.
    """
    profile_user_id: str
    
    # Analytics time range
    time_period: str = "month"  # week, month, quarter, year, all_time
    start_date: Optional[date] = None
    end_date: Optional[date] = None
    
    # Profile engagement metrics
    include_view_analytics: bool = True
    include_interaction_analytics: bool = True
    include_follower_analytics: bool = True
    include_content_analytics: bool = True
    
    # Plant Care specific analytics
    include_plant_inspiration_metrics: bool = True
    include_care_advice_impact: bool = True
    include_identification_help: bool = True
    include_expertise_recognition: bool = True
    
    # Social analytics
    include_follow_trends: bool = True
    include_engagement_rate: bool = True
    include_reach_metrics: bool = True
    include_influence_score: bool = True
    
    # Expert analytics (if applicable)
    include_consultation_metrics: bool = True
    include_expert_performance: bool = True
    include_client_satisfaction: bool = True
    include_revenue_analytics: bool = False  # Admin only
    
    # Content performance
    include_content_reach: bool = True
    include_tutorial_effectiveness: bool = True
    include_plant_guide_usage: bool = True
    include_community_impact: bool = True
    
    # Growth metrics
    include_growth_trends: bool = True
    include_milestone_tracking: bool = True
    include_seasonal_patterns: bool = True
    include_comparative_analysis: bool = True
    
    # Geographic analytics
    include_geographic_reach: bool = True
    include_location_based_engagement: bool = True
    include_timezone_activity: bool = True
    
    # Audience analytics
    include_audience_demographics: bool = True
    include_follower_expertise_levels: bool = True
    include_audience_plant_interests: bool = True
    include_audience_geographic: bool = True
    
    # Engagement quality
    include_meaningful_interactions: bool = True
    include_repeat_engagement: bool = True
    include_conversion_metrics: bool = True  # Followers to consultation clients
    
    # Data granularity
    daily_breakdown: bool = False
    weekly_breakdown: bool = True
    include_hourly_patterns: bool = False
    include_trend_analysis: bool = True
    
    # Privacy and authorization
    requesting_user_id: Optional[str] = None
    admin_request: bool = False
    detailed_analytics: bool = False  # Owner or admin only
    
    # Performance
    use_analytics_cache: bool = True
    cache_ttl_hours: int = 6
    max_data_points: int = 1000


@dataclass
class GetProfileCompletionQuery:
    """
    Query to get profile completion analysis in the Plant Care Application.
    Retrieves completion score and improvement recommendations.
    """
    profile_user_id: str
    
    # Completion analysis options
    include_completion_score: bool = True
    include_missing_fields: bool = True
    include_improvement_suggestions: bool = True
    include_priority_recommendations: bool = True
    
    # Plant Care completion factors
    include_plant_care_setup: bool = True
    include_expertise_completion: bool = True
    include_social_setup: bool = True
    include_preference_completion: bool = True
    
    # Expert profile completion (if applicable)
    include_expert_verification_status: bool = True
    include_consultation_setup: bool = True
    include_credential_completion: bool = True
    include_portfolio_completion: bool = True
    
    # Social profile completion
    include_avatar_status: bool = True
    include_bio_quality: bool = True
    include_social_connections: bool = True
    include_activity_level: bool = True
    
    # Completion scoring
    weighted_scoring: bool = True
    plant_care_weight: float = 0.4
    social_weight: float = 0.3
    basic_info_weight: float = 0.3
    
    # Recommendations
    personalized_suggestions: bool = True
    priority_order_suggestions: bool = True
    estimated_completion_time: bool = True
    
    # Gamification elements
    include_completion_badges: bool = True
    include_milestone_progress: bool = True
    include_completion_streaks: bool = True
    
    # Context
    requesting_user_id: Optional[str] = None
    admin_analysis: bool = False
    
    # Performance
    use_cache: bool = True
    cache_ttl_minutes: int = 60


@dataclass
class GetNearbyProfilesQuery:
    """
    Query to get nearby profiles in the Plant Care Application.
    Retrieves profiles based on geographic proximity with Plant Care context.
    """
    # Location parameters
    center_coordinates: Dict[str, float]  # lat, lng
    radius_km: float = 50.0
    user_location: Optional[str] = None
    
    # Profile filters
    profile_types: List[str] = field(default_factory=lambda: ["all"])  # all, experts, regular_users
    verified_experts: bool = False
    consultation_available: bool = False
    
    # Plant Care context
    similar_experience_level: Optional[str] = None
    shared_plant_interests: Optional[List[str]] = None
    complementary_expertise: Optional[List[str]] = None
    plant_care_active: bool = True
    
    # Activity filters
    recently_active_days: int = 30
    has_plants: Optional[bool] = None
    shares_plant_content: Optional[bool] = None
    
    # Social filters
    open_to_connections: Optional[bool] = None
    similar_follower_count: Optional[bool] = None
    mutual_connections: Optional[bool] = None
    
    # Expert-specific filters (if looking for experts)
    expert_specialties: Optional[List[str]] = None
    consultation_price_range: Optional[Dict[str, float]] = None
    expert_rating_min: Optional[float] = None
    same_timezone_preference: bool = False
    
    # Distance and location preferences
    same_city: Optional[bool] = None
    same_climate_zone: Optional[bool] = None
    urban_vs_rural: Optional[str] = None  # urban, suburban, rural
    
    # Data inclusion
    include_distance: bool = True
    include_location_info: bool = True
    include_climate_info: bool = True
    include_plant_compatibility: bool = True
    include_meetup_potential: bool = True
    
    # Privacy and safety
    requesting_user_id: Optional[str] = None
    respect_location_privacy: bool = True
    exclude_blocked_users: bool = True
    safe_meetup_locations: bool = True
    
    # Sorting
    sort_by: str = "distance"  # distance, relevance, activity, rating
    max_distance_km: float = 100.0
    prioritize_experts: bool = False
    prioritize_similar_interests: bool = True
    
    # Pagination
    page: int = 1
    page_size: int = 20
    max_results: int = 100
    
    # Performance
    use_geospatial_index: bool = True
    cache_results: bool = True
    cache_ttl_minutes: int = 30
    search_timeout_seconds: int = 5


@dataclass
class GetProfileRecommendationsQuery:
    """
    Query to get profile recommendations in the Plant Care Application.
    Retrieves personalized profile suggestions based on user interests and behavior.
    """
    user_id: str
    
    # Recommendation types
    recommendation_types: List[str] = field(default_factory=lambda: ["experts", "similar_users", "local"])
    max_recommendations_per_type: int = 10
    
    # Plant Care based recommendations
    based_on_plant_interests: bool = True
    based_on_care_level: bool = True
    based_on_plant_problems: bool = True
    based_on_growth_stage: bool = True
    
    # Expertise recommendations
    recommend_experts_for_plants: bool = True
    recommend_problem_solvers: bool = True
    recommend_identification_helpers: bool = True
    recommend_consultation_experts: bool = True
    
    # Social recommendations
    recommend_similar_gardeners: bool = True
    recommend_local_gardeners: bool = True
    recommend_inspiration_profiles: bool = True
    recommend_mentors: bool = True
    
    # Learning and growth recommendations
    recommend_next_level_experts: bool = True
    recommend_skill_builders: bool = True
    recommend_plant_diversifiers: bool = True
    
    # Behavioral factors
    based_on_following_patterns: bool = True
    based_on_interaction_history: bool = True
    based_on_search_history: bool = True
    based_on_consultation_history: bool = True
    
    # Diversity and discovery
    ensure_diversity: bool = True
    include_different_expertise: bool = True
    include_different_locations: bool = True
    include_different_experience_levels: bool = True
    
    # Recommendation quality
    min_profile_completion: int = 50
    min_activity_score: int = 30
    exclude_recently_recommended: bool = True
    exclude_already_following: bool = True
    
    # Expert recommendation criteria
    expert_rating_threshold: float = 4.0
    expert_response_time_max: int = 48  # Hours
    expert_availability_required: bool = False
    
    # Geographic preferences
    prioritize_local: bool = True
    max_distance_km: float = 200.0
    same_climate_preference: bool = True
    
    # Personalization
    user_experience_level: Optional[str] = None
    user_plant_interests: Optional[List[str]] = None
    user_location: Optional[Dict[str, float]] = None
    user_timezone: Optional[str] = None
    
    # Data inclusion
    include_recommendation_reasons: bool = True
    include_compatibility_score: bool = True
    include_mutual_interests: bool = True
    include_introduction_suggestions: bool = True
    
    # Privacy and filtering
    respect_privacy_settings: bool = True
    exclude_blocked_users: bool = True
    exclude_inactive_users: bool = True
    
    # Performance
    use_ml_recommendations: bool = True
    use_recommendation_cache: bool = True
    cache_ttl_hours: int = 24
    max_processing_time_seconds: int = 5