# app/modules/user_management/application/dto/user_dto.py
"""
Plant Care Application - User Management DTOs

Data Transfer Objects for user-related operations in the Plant Care Application.
Defines data structures for user registration, updates, dashboard, and analytics.
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field
from enum import Enum

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.models.profile import Profile
from app.modules.user_management.domain.models.subscription import Subscription


@dataclass
class UserDTO:
    """
    Complete user data transfer object for Plant Care Application.
    Used for detailed user information including profile and subscription.
    """
    # Core user data
    user_id: str
    email: str
    role: str
    status: str
    is_verified: bool
    is_onboarded: bool
    
    # Plant Care specific
    plant_limit: int
    provider: str
    
    # Timestamps
    created_at: str
    updated_at: str
    last_login_at: Optional[str] = None
    last_activity_at: Optional[str] = None
    email_verified_at: Optional[str] = None
    onboarded_at: Optional[str] = None
    
    # Profile data (if included)
    profile: Optional[Dict[str, Any]] = None
    
    # Subscription data (if included)
    subscription: Optional[Dict[str, Any]] = None
    
    # Additional metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class UserBriefDTO:
    """
    Brief user information for lists and references.
    Minimal user data for performance optimization.
    """
    user_id: str
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    role: str = "user"
    is_verified: bool = False
    is_expert_verified: bool = False
    plant_count: int = 0
    member_since: str = ""


@dataclass
class UserRegistrationDTO:
    """
    User registration data transfer object.
    Contains all data needed for new user registration.
    """
    # Required fields
    email: str
    password: str
    display_name: str
    
    # Optional fields
    provider: str = "email"
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Plant Care preferences
    plant_care_preferences: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Subscription preferences
    subscription_tier: str = "free"
    start_trial: bool = False
    
    # OAuth data (if applicable)
    oauth_provider: Optional[str] = None
    oauth_provider_id: Optional[str] = None
    supabase_user_id: Optional[str] = None
    
    # Marketing preferences
    marketing_consent: bool = False
    referral_code: Optional[str] = None


@dataclass
class UserUpdateDTO:
    """
    User update data transfer object.
    Contains fields that can be updated by the user.
    """
    # User level updates
    email: Optional[str] = None
    timezone: Optional[str] = None
    
    # Profile updates
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    experience_level: Optional[str] = None
    preferred_units: Optional[str] = None
    profile_visibility: Optional[str] = None
    
    # Plant Care preferences
    plant_care_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    
    # Metadata
    updated_fields: List[str] = field(default_factory=list)
    update_reason: Optional[str] = None


@dataclass
class UserDashboardDTO:
    """
    User dashboard data transfer object.
    Contains comprehensive data for the user dashboard.
    """
    # User summary
    user: UserBriefDTO
    
    # Profile summary
    profile: Dict[str, Any]
    
    # Subscription summary
    subscription: Dict[str, Any]
    
    # Plant Care statistics
    plant_stats: Dict[str, Any] = field(default_factory=lambda: {
        "total_plants": 0,
        "healthy_plants": 0,
        "plants_needing_care": 0,
        "plants_added_this_month": 0,
        "favorite_plant_types": []
    })
    
    # Care activity
    care_activity: Dict[str, Any] = field(default_factory=lambda: {
        "pending_tasks": 0,
        "completed_tasks_today": 0,
        "care_streak_days": 0,
        "next_care_due": None,
        "recent_activities": []
    })
    
    # Community activity
    community_activity: Dict[str, Any] = field(default_factory=lambda: {
        "followers_count": 0,
        "following_count": 0,
        "posts_count": 0,
        "expert_consultations": 0,
        "community_score": 0
    })
    
    # Feature usage
    feature_usage: Dict[str, Any] = field(default_factory=lambda: {
        "ai_identifications_used": 0,
        "ai_identifications_limit": 10,
        "expert_consultations_used": 0,
        "expert_consultations_limit": 0,
        "premium_features_available": []
    })
    
    # Recommendations
    recommendations: Dict[str, Any] = field(default_factory=lambda: {
        "suggested_plants": [],
        "care_tips": [],
        "expert_advice": [],
        "subscription_suggestions": []
    })
    
    # Alerts and notifications
    alerts: List[Dict[str, Any]] = field(default_factory=list)
    
    # Metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    cache_ttl: int = 300  # 5 minutes


@dataclass
class UserStatsDTO:
    """
    User statistics data transfer object.
    Contains analytical data about user behavior and performance.
    """
    user_id: str
    
    # Basic stats
    total_plants: int = 0
    active_plants: int = 0
    plants_added_this_month: int = 0
    
    # Care statistics
    care_tasks_completed: int = 0
    care_streak_days: int = 0
    avg_care_frequency: float = 0.0
    
    # Community engagement
    followers_count: int = 0
    following_count: int = 0
    posts_count: int = 0
    likes_received: int = 0
    comments_made: int = 0
    
    # Expert metrics (if expert user)
    expert_rating: Optional[float] = None
    consultations_given: int = 0
    consultation_rating: Optional[float] = None
    specialties: List[str] = field(default_factory=list)
    
    # Subscription metrics
    subscription_tier: str = "free"
    subscription_duration_days: int = 0
    feature_usage_percentage: float = 0.0
    
    # Engagement metrics
    login_frequency: float = 0.0
    session_duration_avg: float = 0.0
    feature_adoption_score: float = 0.0
    
    # Plant health success
    plant_health_improvement: float = 0.0
    successful_plant_care_rate: float = 0.0
    
    # Generated metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    period: str = "all_time"


@dataclass
class UserSearchResultDTO:
    """
    User search result data transfer object.
    Optimized for search results and user discovery.
    """
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    
    # Plant Care info
    experience_level: str = "beginner"
    plant_count: int = 0
    specialties: List[str] = field(default_factory=list)
    
    # Social proof
    followers_count: int = 0
    is_expert_verified: bool = False
    expert_rating: Optional[float] = None
    
    # Matching info
    relevance_score: float = 0.0
    match_reason: List[str] = field(default_factory=list)
    
    # Privacy settings
    profile_visibility: str = "public"
    can_follow: bool = True
    can_message: bool = True


@dataclass
class UserListDTO:
    """
    User list data transfer object.
    Contains paginated list of users with metadata.
    """
    users: List[UserBriefDTO] = field(default_factory=list)
    
    # Pagination
    total_count: int = 0
    page: int = 1
    page_size: int = 20
    total_pages: int = 0
    has_next: bool = False
    has_previous: bool = False
    
    # Filtering metadata
    filters_applied: Dict[str, Any] = field(default_factory=dict)
    sort_by: str = "created_at"
    sort_order: str = "desc"
    
    # Generated metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())


# Factory functions for creating DTOs from domain models

def create_user_dto(user: User, include_profile: bool = False, 
                   include_subscription: bool = False, 
                   profile: Optional[Profile] = None,
                   subscription: Optional[Subscription] = None) -> UserDTO:
    """
    Create UserDTO from domain User model.
    
    Args:
        user: User domain model
        include_profile: Whether to include profile data
        include_subscription: Whether to include subscription data
        profile: Profile domain model (optional)
        subscription: Subscription domain model (optional)
        
    Returns:
        UserDTO: Complete user data transfer object
    """
    # Basic user data
    user_dto = UserDTO(
        user_id=user.user_id,
        email=user.email,
        role=user.role.value,
        status=user.status.value,
        is_verified=user.is_verified,
        is_onboarded=user.is_onboarded,
        plant_limit=user.plant_limit,
        provider=user.provider,
        created_at=user.created_at.isoformat(),
        updated_at=user.updated_at.isoformat(),
        last_login_at=user.last_login_at.isoformat() if user.last_login_at else None,
        last_activity_at=user.last_activity_at.isoformat() if user.last_activity_at else None,
        email_verified_at=user.email_verified_at.isoformat() if user.email_verified_at else None,
        onboarded_at=user.onboarded_at.isoformat() if user.onboarded_at else None
    )
    
    # Include profile data if requested
    if include_profile and profile:
        user_dto.profile = {
            "profile_id": profile.profile_id,
            "display_name": profile.display_name,
            "bio": profile.bio,
            "avatar_url": profile.avatar_url,
            "location": profile.location,
            "experience_level": profile.experience_level.value,
            "preferred_units": profile.preferred_units.value,
            "is_expert_verified": profile.is_expert_verified,
            "followers_count": profile.followers_count,
            "following_count": profile.following_count
        }
    
    # Include subscription data if requested
    if include_subscription and subscription:
        user_dto.subscription = {
            "subscription_id": subscription.subscription_id,
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "trial_end_date": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            "current_period_end": subscription.current_period_end.isoformat(),
            "is_trial": subscription.is_trial(),
            "is_active": subscription.is_active()
        }
    
    return user_dto


def create_user_brief_dto(user: User, profile: Optional[Profile] = None,
                         plant_count: int = 0) -> UserBriefDTO:
    """
    Create UserBriefDTO from domain models.
    
    Args:
        user: User domain model
        profile: Profile domain model (optional)
        plant_count: Number of plants user has
        
    Returns:
        UserBriefDTO: Brief user information
    """
    display_name = profile.display_name if profile else user.email.split('@')[0]
    avatar_url = profile.avatar_url if profile else None
    is_expert_verified = profile.is_expert_verified if profile else False
    
    return UserBriefDTO(
        user_id=user.user_id,
        email=user.email,
        display_name=display_name,
        avatar_url=avatar_url,
        role=user.role.value,
        is_verified=user.is_verified,
        is_expert_verified=is_expert_verified,
        plant_count=plant_count,
        member_since=user.created_at.isoformat()
    )


def create_user_dashboard_dto(user: User, profile: Profile, 
                             subscription: Optional[Subscription] = None,
                             plant_stats: Optional[Dict[str, Any]] = None,
                             care_activity: Optional[Dict[str, Any]] = None,
                             community_activity: Optional[Dict[str, Any]] = None,
                             feature_usage: Optional[Dict[str, Any]] = None) -> UserDashboardDTO:
    """
    Create UserDashboardDTO from domain models and statistics.
    
    Args:
        user: User domain model
        profile: Profile domain model
        subscription: Subscription domain model (optional)
        plant_stats: Plant statistics (optional)
        care_activity: Care activity data (optional)
        community_activity: Community activity data (optional)
        feature_usage: Feature usage data (optional)
        
    Returns:
        UserDashboardDTO: Complete dashboard data
    """
    # Create user brief
    user_brief = create_user_brief_dto(user, profile)
    
    # Profile summary
    profile_summary = {
        "display_name": profile.display_name,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "location": profile.location,
        "experience_level": profile.experience_level.value,
        "is_expert_verified": profile.is_expert_verified,
        "profile_completion": _calculate_profile_completion(profile)
    }
    
    # Subscription summary
    subscription_summary = {}
    if subscription:
        subscription_summary = {
            "tier": subscription.tier.value,
            "status": subscription.status.value,
            "is_trial": subscription.is_trial(),
            "trial_ends_at": subscription.trial_end_date.isoformat() if subscription.trial_end_date else None,
            "next_billing_date": subscription.next_billing_date.isoformat() if subscription.next_billing_date else None,
            "can_upgrade": subscription.tier.value == "free"
        }
    
    return UserDashboardDTO(
        user=user_brief,
        profile=profile_summary,
        subscription=subscription_summary,
        plant_stats=plant_stats or {},
        care_activity=care_activity or {},
        community_activity=community_activity or {},
        feature_usage=feature_usage or {}
    )


def _calculate_profile_completion(profile: Profile) -> Dict[str, Any]:
    """Calculate profile completion percentage."""
    total_fields = 8
    completed_fields = 0
    
    # Check required/important fields
    if profile.display_name:
        completed_fields += 1
    if profile.bio:
        completed_fields += 1
    if profile.avatar_url:
        completed_fields += 1
    if profile.location:
        completed_fields += 1
    if profile.plant_care_preferences:
        completed_fields += 1
    if profile.notification_preferences:
        completed_fields += 1
    if profile.experience_level.value != "beginner":
        completed_fields += 1
    if profile.preferred_units:
        completed_fields += 1
    
    completion_percentage = (completed_fields / total_fields) * 100
    
    return {
        "percentage": round(completion_percentage, 1),
        "completed_fields": completed_fields,
        "total_fields": total_fields,
        "missing_fields": _get_missing_profile_fields(profile)
    }


def _get_missing_profile_fields(profile: Profile) -> List[str]:
    """Get list of missing profile fields."""
    missing = []
    
    if not profile.bio:
        missing.append("bio")
    if not profile.avatar_url:
        missing.append("avatar")
    if not profile.location:
        missing.append("location")
    if not profile.plant_care_preferences:
        missing.append("plant_care_preferences")
    if not profile.notification_preferences:
        missing.append("notification_preferences")
    
    return missing