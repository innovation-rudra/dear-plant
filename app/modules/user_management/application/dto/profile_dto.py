# app/modules/user_management/application/dto/profile_dto.py
"""
Plant Care Application - Profile Management DTOs

Data Transfer Objects for profile-related operations in the Plant Care Application.
Defines data structures for profile creation, updates, preferences, and expert verification.
Connected to domain models from previous conversation threads.
"""

import uuid
from datetime import datetime, timedelta
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field
from decimal import Decimal

from app.modules.user_management.domain.models.profile import (
    Profile, ProfileStatus, ExperienceLevel, PreferredUnits, ProfileVisibility
)
from app.shared.core.exceptions import ValidationError


@dataclass
class ProfileDTO:
    """
    Complete profile data transfer object for Plant Care Application.
    Connects to Profile domain model from previous conversation threads.
    """
    # Core profile data (matches domain model)
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Plant Care information (from domain model)
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Profile settings (from domain model)
    profile_visibility: str = "public"
    status: str = "active"
    
    # Expert information (from domain model)
    is_expert_verified: bool = False
    expert_verification_status: Optional[str] = None
    expert_credentials: Optional[Dict[str, Any]] = None
    expert_specialties: Optional[List[str]] = None
    expert_rating: Optional[float] = None
    expert_reviews_count: int = 0
    
    # Social features (from domain model)
    followers_count: int = 0
    following_count: int = 0
    
    # Plant Care preferences (from domain model)
    plant_care_preferences: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps (from domain model)
    created_at: str = ""
    updated_at: str = ""
    verification_requested_at: Optional[str] = None
    verification_approved_at: Optional[str] = None
    
    # Computed fields for DTOs
    profile_completion: Dict[str, Any] = field(default_factory=dict)
    is_following: bool = False  # If current user is following this profile
    can_follow: bool = True
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ProfileBriefDTO:
    """
    Brief profile information for lists and references.
    Minimal profile data for performance optimization.
    """
    profile_id: str
    user_id: str
    display_name: str
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    experience_level: str = "beginner"
    is_expert_verified: bool = False
    expert_rating: Optional[float] = None
    followers_count: int = 0
    plant_count: int = 0  # Will be populated from plant management module


@dataclass
class ProfileCreationDTO:
    """
    Profile creation data transfer object.
    Contains data needed for creating a new profile - connects to domain model.
    """
    # Required fields (matches domain model constructor)
    user_id: str
    display_name: str
    
    # Optional basic info
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Plant Care preferences (matches domain model)
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Profile settings (matches domain model)
    profile_visibility: str = "public"
    
    # Plant Care preferences (matches domain model structure)
    plant_care_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "watering_reminder_frequency": 1,  # days
        "fertilizing_reminder_frequency": 30,  # days
        "preferred_care_difficulty": "easy",
        "preferred_plant_types": [],
        "care_notification_time": "09:00",
        "weekend_care_reminders": True,
        "seasonal_care_adjustments": True
    })
    
    # Notification preferences (matches domain model structure)
    notification_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "email_notifications": True,
        "push_notifications": True,
        "care_reminders": True,
        "plant_health_alerts": True,
        "expert_advice": True,
        "community_updates": False,
        "marketing_emails": False,
        "weekly_digest": True
    })


@dataclass
class ProfileUpdateDTO:
    """
    Profile update data transfer object.
    Contains fields that can be updated in a profile - matches domain model methods.
    """
    # Basic information updates (matches domain model update methods)
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    
    # Plant Care preferences (matches domain model)
    experience_level: Optional[str] = None
    preferred_units: Optional[str] = None
    
    # Profile settings (matches domain model)
    profile_visibility: Optional[str] = None
    
    # Plant Care preferences updates (matches domain model)
    plant_care_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    
    # Metadata
    updated_fields: List[str] = field(default_factory=list)
    update_reason: Optional[str] = None


@dataclass
class ProfilePreferencesDTO:
    """
    Profile preferences data transfer object.
    Focused on Plant Care and notification preferences - matches domain model structure.
    """
    # Plant Care preferences (matches domain model)
    plant_care_preferences: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Preference metadata
    preferences_version: str = "1.0"
    last_updated: str = ""
    updated_by: str = ""
    
    # Validation results
    validation_errors: List[str] = field(default_factory=list)
    applied_defaults: List[str] = field(default_factory=list)


@dataclass
class ProfileAvatarDTO:
    """
    Profile avatar data transfer object.
    Contains avatar upload and management data - supports domain model avatar methods.
    """
    # Avatar information
    avatar_url: str
    original_filename: str
    file_size: int
    file_type: str
    
    # Image metadata
    width: Optional[int] = None
    height: Optional[int] = None
    is_optimized: bool = False
    
    # Upload metadata
    uploaded_at: str = ""
    uploaded_by: str = ""
    storage_provider: str = "supabase"
    
    # Processing status
    processing_status: str = "completed"
    processing_errors: List[str] = field(default_factory=list)


@dataclass
class ProfileAnalyticsDTO:
    """
    Profile analytics data transfer object.
    Contains analytical data about profile performance and engagement.
    """
    profile_id: str
    user_id: str
    
    # Profile metrics
    profile_views: int = 0
    profile_completion_percentage: float = 0.0
    
    # Social metrics
    followers_count: int = 0
    following_count: int = 0
    followers_growth_rate: float = 0.0
    
    # Plant Care metrics
    plants_count: int = 0
    care_tasks_completed: int = 0
    care_success_rate: float = 0.0
    
    # Expert metrics (if applicable - matches domain model expert fields)
    expert_rating: Optional[float] = None
    consultations_given: int = 0
    consultation_rating: Optional[float] = None
    expertise_score: float = 0.0
    
    # Engagement metrics
    posts_created: int = 0
    comments_made: int = 0
    likes_received: int = 0
    shares_received: int = 0
    
    # Activity metrics
    login_frequency: float = 0.0
    session_duration_avg: float = 0.0
    feature_usage_score: float = 0.0
    
    # Time-based metrics
    active_days_last_30: int = 0
    peak_activity_hours: List[int] = field(default_factory=list)
    
    # Generated metadata
    generated_at: str = field(default_factory=lambda: datetime.utcnow().isoformat())
    period: str = "last_30_days"


@dataclass
class ProfileSearchResultDTO:
    """
    Profile search result data transfer object.
    Optimized for profile search and discovery - connects to domain model.
    """
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    
    # Plant Care information (from domain model)
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    specialties: List[str] = field(default_factory=list)
    plant_count: int = 0
    
    # Expert information (from domain model)
    is_expert_verified: bool = False
    expert_rating: Optional[float] = None
    expert_reviews_count: int = 0
    
    # Social metrics (from domain model)
    followers_count: int = 0
    following_count: int = 0
    is_following: bool = False
    
    # Search relevance
    relevance_score: float = 0.0
    match_criteria: List[str] = field(default_factory=list)
    distance_km: Optional[float] = None  # If location-based search
    
    # Interaction capabilities
    can_follow: bool = True
    can_message: bool = True
    can_book_consultation: bool = False
    
    # Profile status (from domain model)
    profile_visibility: str = "public"
    is_active: bool = True
    last_activity: Optional[str] = None


@dataclass
class ExpertProfileDTO:
    """
    Expert profile data transfer object.
    Specialized for verified expert profiles - connects to domain model expert features.
    """
    # Basic profile information (from domain model)
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    
    # Expert verification (from domain model)
    is_expert_verified: bool = True
    expert_verification_status: str = "verified"
    expert_credentials: Dict[str, Any] = field(default_factory=dict)
    expert_specialties: List[str] = field(default_factory=list)
    verification_approved_at: Optional[str] = None
    
    # Expert performance metrics
    expert_rating: float = 0.0
    expert_reviews_count: int = 0
    consultations_given: int = 0
    consultation_success_rate: float = 0.0
    response_time_avg: float = 0.0  # Average response time in hours
    
    # Expert services
    consultation_price: Optional[Decimal] = None
    consultation_duration: int = 60  # minutes
    available_time_slots: List[str] = field(default_factory=list)
    consultation_types: List[str] = field(default_factory=list)
    
    # Expert content
    articles_written: int = 0
    plant_guides_created: int = 0
    questions_answered: int = 0
    
    # Social proof (from domain model)
    followers_count: int = 0
    plants_helped: int = 0
    success_stories: int = 0
    
    # Availability
    is_available_for_consultation: bool = True
    next_available_slot: Optional[str] = None
    timezone: str = "UTC"
    
    # Expert badge information
    expert_badges: List[Dict[str, Any]] = field(default_factory=list)
    years_of_experience: int = 0
    
    # Performance tracking
    monthly_consultations: int = 0
    consultation_booking_rate: float = 0.0
    client_retention_rate: float = 0.0


@dataclass
class ProfileListDTO:
    """Data transfer object for paginated profile lists."""
    profiles: List[ProfileBriefDTO]
    total_count: int
    page: int
    page_size: int
    has_next: bool
    has_previous: bool
    total_pages: int
    filters: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ExpertSearchResultDTO:
    """Data transfer object for expert search results with consultation data."""
    expert_profile: ExpertProfileDTO
    profile_brief: ProfileBriefDTO
    consultation_availability: bool
    next_available_slot: Optional[datetime] = None
    distance_km: Optional[float] = None
    relevance_score: float = 0.0


# Factory functions for creating DTOs from domain models

def create_profile_dto(profile: Profile, current_user_id: Optional[str] = None,
                      is_following: bool = False, plant_count: int = 0) -> ProfileDTO:
    """
    Create ProfileDTO from domain Profile model.
    Connects to Profile domain model from previous conversation threads.
    
    Args:
        profile: Profile domain model
        current_user_id: ID of current user (for relationship context)
        is_following: Whether current user is following this profile
        plant_count: Number of plants this user has
        
    Returns:
        ProfileDTO: Complete profile data transfer object
    """
    # Calculate profile completion
    profile_completion = _calculate_profile_completion_dto(profile)
    
    # Determine if current user can follow this profile
    can_follow = (
        current_user_id is not None and 
        current_user_id != profile.user_id and
        profile.profile_visibility != ProfileVisibility.PRIVATE
    )
    
    return ProfileDTO(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        location=profile.location,
        timezone=profile.timezone,
        experience_level=profile.experience_level.value,
        preferred_units=profile.preferred_units.value,
        profile_visibility=profile.profile_visibility.value,
        status=profile.status.value,
        is_expert_verified=profile.is_expert_verified,
        expert_verification_status=profile.expert_verification_status,
        expert_credentials=profile.expert_credentials,
        expert_specialties=profile.expert_specialties,
        expert_rating=float(profile.expert_rating) if profile.expert_rating else None,
        expert_reviews_count=profile.expert_reviews_count,
        followers_count=profile.followers_count,
        following_count=profile.following_count,
        plant_care_preferences=profile.plant_care_preferences,
        notification_preferences=profile.notification_preferences,
        created_at=profile.created_at.isoformat(),
        updated_at=profile.updated_at.isoformat(),
        verification_requested_at=profile.verification_requested_at.isoformat() if profile.verification_requested_at else None,
        verification_approved_at=profile.verification_approved_at.isoformat() if profile.verification_approved_at else None,
        profile_completion=profile_completion,
        is_following=is_following,
        can_follow=can_follow,
        metadata={"plant_count": plant_count}
    )


def create_profile_brief_dto(profile: Profile, plant_count: int = 0) -> ProfileBriefDTO:
    """
    Create ProfileBriefDTO from domain Profile model.
    
    Args:
        profile: Profile domain model
        plant_count: Number of plants this user has
        
    Returns:
        ProfileBriefDTO: Brief profile information
    """
    return ProfileBriefDTO(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        avatar_url=profile.avatar_url,
        location=profile.location,
        experience_level=profile.experience_level.value,
        is_expert_verified=profile.is_expert_verified,
        expert_rating=float(profile.expert_rating) if profile.expert_rating else None,
        followers_count=profile.followers_count,
        plant_count=plant_count
    )


def create_expert_profile_dto(profile: Profile, consultation_data: Optional[Dict[str, Any]] = None,
                             performance_metrics: Optional[Dict[str, Any]] = None) -> ExpertProfileDTO:
    """
    Create ExpertProfileDTO from domain Profile model.
    Connects to expert verification features from domain model.
    
    Args:
        profile: Profile domain model (must be expert verified)
        consultation_data: Consultation service data (optional)
        performance_metrics: Expert performance metrics (optional)
        
    Returns:
        ExpertProfileDTO: Expert profile data transfer object
    """
    if not profile.is_expert_verified:
        raise ValueError("Profile must be expert verified to create ExpertProfileDTO")
    
    # Default consultation data
    consultation_data = consultation_data or {}
    performance_metrics = performance_metrics or {}
    
    return ExpertProfileDTO(
        profile_id=profile.profile_id,
        user_id=profile.user_id,
        display_name=profile.display_name,
        bio=profile.bio,
        avatar_url=profile.avatar_url,
        location=profile.location,
        is_expert_verified=profile.is_expert_verified,
        expert_verification_status=profile.expert_verification_status,
        expert_credentials=profile.expert_credentials or {},
        expert_specialties=profile.expert_specialties or [],
        verification_approved_at=profile.verification_approved_at.isoformat() if profile.verification_approved_at else None,
        expert_rating=float(profile.expert_rating) if profile.expert_rating else 0.0,
        expert_reviews_count=profile.expert_reviews_count,
        consultations_given=performance_metrics.get("consultations_given", 0),
        consultation_success_rate=performance_metrics.get("consultation_success_rate", 0.0),
        response_time_avg=performance_metrics.get("response_time_avg", 0.0),
        consultation_price=consultation_data.get("consultation_price"),
        consultation_duration=consultation_data.get("consultation_duration", 60),
        available_time_slots=consultation_data.get("available_time_slots", []),
        consultation_types=consultation_data.get("consultation_types", []),
        articles_written=performance_metrics.get("articles_written", 0),
        plant_guides_created=performance_metrics.get("plant_guides_created", 0),
        questions_answered=performance_metrics.get("questions_answered", 0),
        followers_count=profile.followers_count,
        plants_helped=performance_metrics.get("plants_helped", 0),
        success_stories=performance_metrics.get("success_stories", 0),
        is_available_for_consultation=consultation_data.get("is_available", True),
        next_available_slot=consultation_data.get("next_available_slot"),
        timezone=profile.timezone,
        expert_badges=_generate_expert_badges(profile, performance_metrics),
        years_of_experience=_calculate_years_of_experience(profile),
        monthly_consultations=performance_metrics.get("monthly_consultations", 0),
        consultation_booking_rate=performance_metrics.get("consultation_booking_rate", 0.0),
        client_retention_rate=performance_metrics.get("client_retention_rate", 0.0)
    )


def create_profile_list_dto(profiles: List[Profile], 
                           total_count: int,
                           page: int,
                           page_size: int) -> ProfileListDTO:
    """
    Create ProfileListDTO from profile list.
    
    Args:
        profiles: List of profile domain models
        total_count: Total number of profiles
        page: Current page number
        page_size: Number of items per page
        
    Returns:
        ProfileListDTO: Paginated profile list
    """
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    profile_briefs = [create_profile_brief_dto(profile) for profile in profiles]
    
    return ProfileListDTO(
        profiles=profile_briefs,
        total_count=total_count,
        page=page,
        page_size=page_size,
        has_next=has_next,
        has_previous=has_previous,
        total_pages=total_pages
    )


def create_expert_search_result_dto(profile: Profile,
                                  distance_km: Optional[float] = None,
                                  relevance_score: float = 0.0) -> ExpertSearchResultDTO:
    """
    Create ExpertSearchResultDTO from expert profile.
    
    Args:
        profile: Expert profile domain model
        distance_km: Distance from search location
        relevance_score: Search relevance score
        
    Returns:
        ExpertSearchResultDTO: Expert search result
    """
    expert_profile = create_expert_profile_dto(profile)
    profile_brief = create_profile_brief_dto(profile)
    
    # Calculate next available slot (mock implementation)
    next_slot = None
    if profile.consultation_availability:
        next_slot = datetime.utcnow() + timedelta(days=1)
    
    return ExpertSearchResultDTO(
        expert_profile=expert_profile,
        profile_brief=profile_brief,
        consultation_availability=profile.consultation_availability,
        next_available_slot=next_slot,
        distance_km=distance_km,
        relevance_score=relevance_score
    )


def _calculate_profile_completion_dto(profile: Profile) -> Dict[str, Any]:
    """Calculate profile completion for DTO - connects to domain model fields."""
    total_fields = 10
    completed_fields = 0
    missing_fields = []
    
    # Check completion of important fields (matches domain model fields)
    if profile.display_name:
        completed_fields += 1
    else:
        missing_fields.append("display_name")
        
    if profile.bio:
        completed_fields += 1
    else:
        missing_fields.append("bio")
        
    if profile.avatar_url:
        completed_fields += 1
    else:
        missing_fields.append("avatar")
        
    if profile.location:
        completed_fields += 1
    else:
        missing_fields.append("location")
        
    if profile.plant_care_preferences:
        completed_fields += 1
    else:
        missing_fields.append("plant_care_preferences")
        
    if profile.notification_preferences:
        completed_fields += 1
    else:
        missing_fields.append("notification_preferences")
        
    if profile.experience_level != ExperienceLevel.BEGINNER:
        completed_fields += 1
    else:
        missing_fields.append("experience_level")
        
    if profile.preferred_units:
        completed_fields += 1
        
    if profile.timezone != "UTC":
        completed_fields += 1
    else:
        missing_fields.append("timezone")
        
    if profile.profile_visibility:
        completed_fields += 1
    
    completion_percentage = (completed_fields / total_fields) * 100
    
    return {
        "percentage": round(completion_percentage, 1),
        "completed_fields": completed_fields,
        "total_fields": total_fields,
        "missing_fields": missing_fields,
        "recommendations": _get_completion_recommendations(missing_fields)
    }


def _get_completion_recommendations(missing_fields: List[str]) -> List[str]:
    """Get recommendations for completing profile."""
    recommendations = []
    
    if "bio" in missing_fields:
        recommendations.append("Add a bio to help other plant enthusiasts connect with you")
    if "avatar" in missing_fields:
        recommendations.append("Upload a profile picture to personalize your account")
    if "location" in missing_fields:
        recommendations.append("Add your location to get weather-based plant care recommendations")
    if "plant_care_preferences" in missing_fields:
        recommendations.append("Set up your plant care preferences for personalized reminders")
    if "experience_level" in missing_fields:
        recommendations.append("Update your experience level to get appropriate plant recommendations")
    
    return recommendations


def _generate_expert_badges(profile: Profile, performance_metrics: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Generate expert badges based on profile and performance - connects to domain model."""
    badges = []
    
    # Verification badge (from domain model)
    if profile.is_expert_verified:
        badges.append({
            "type": "verification",
            "title": "Verified Expert",
            "description": "Verified plant care expert",
            "icon": "verified",
            "color": "#4CAF50"
        })
    
    # Rating badges (from domain model)
    expert_rating = float(profile.expert_rating) if profile.expert_rating else 0.0
    if expert_rating >= 4.5:
        badges.append({
            "type": "rating",
            "title": "Top Rated Expert",
            "description": f"{expert_rating:.1f} star rating",
            "icon": "star",
            "color": "#FFD700"
        })
    
    # Experience badges
    consultations_given = performance_metrics.get("consultations_given", 0)
    if consultations_given >= 100:
        badges.append({
            "type": "experience",
            "title": "Experienced Consultant",
            "description": f"{consultations_given}+ consultations",
            "icon": "award",
            "color": "#9C27B0"
        })
    
    # Speciality badges (from domain model)
    if profile.expert_specialties:
        for specialty in profile.expert_specialties[:3]:  # Show top 3 specialties
            badges.append({
                "type": "specialty",
                "title": f"{specialty.title()} Specialist",
                "description": f"Expert in {specialty}",
                "icon": "leaf",
                "color": "#4CAF50"
            })
    
    return badges


def _calculate_years_of_experience(profile: Profile) -> int:
    """Calculate years of experience from profile creation and verification - connects to domain model."""
    if not profile.verification_approved_at:
        return 0
    
    years = (datetime.utcnow() - profile.verification_approved_at).days // 365
    return max(0, years)


# Validation Functions

def validate_profile_creation_dto(dto: ProfileCreationDTO) -> None:
    """
    Validate profile creation data.
    
    Args:
        dto: Profile creation DTO
        
    Raises:
        ValidationError: If validation fails
    """
    if not dto.display_name or len(dto.display_name.strip()) < 2:
        raise ValidationError("Display name must be at least 2 characters")
    
    if len(dto.display_name) > 100:
        raise ValidationError("Display name cannot exceed 100 characters")
    
    if dto.bio and len(dto.bio) > 500:
        raise ValidationError("Bio cannot exceed 500 characters")
    
    if dto.location and len(dto.location) > 200:
        raise ValidationError("Location cannot exceed 200 characters")
    
    if dto.experience_level not in ["beginner", "intermediate", "advanced", "expert"]:
        raise ValidationError("Invalid experience level")
    
    if dto.preferred_units not in ["metric", "imperial"]:
        raise ValidationError("Preferred units must be 'metric' or 'imperial'")
    
    if dto.profile_visibility not in ["public", "private", "followers_only"]:
        raise ValidationError("Invalid profile visibility setting")
    
    # Validate Plant Care preferences
    if dto.plant_care_preferences:
        _validate_plant_care_preferences(dto.plant_care_preferences)
    
    # Validate notification preferences
    if dto.notification_preferences:
        _validate_notification_preferences(dto.notification_preferences)


def validate_profile_update_dto(dto: ProfileUpdateDTO) -> None:
    """
    Validate profile update data.
    
    Args:
        dto: Profile update DTO
        
    Raises:
        ValidationError: If validation fails
    """
    if dto.display_name is not None:
        if not dto.display_name or len(dto.display_name.strip()) < 2:
            raise ValidationError("Display name must be at least 2 characters")
        if len(dto.display_name) > 100:
            raise ValidationError("Display name cannot exceed 100 characters")
    
    if dto.bio is not None and len(dto.bio) > 500:
        raise ValidationError("Bio cannot exceed 500 characters")
    
    if dto.location is not None and len(dto.location) > 200:
        raise ValidationError("Location cannot exceed 200 characters")
    
    if dto.experience_level is not None and dto.experience_level not in ["beginner", "intermediate", "advanced", "expert"]:
        raise ValidationError("Invalid experience level")
    
    if dto.preferred_units is not None and dto.preferred_units not in ["metric", "imperial"]:
        raise ValidationError("Preferred units must be 'metric' or 'imperial'")
    
    if dto.profile_visibility is not None and dto.profile_visibility not in ["public", "private", "followers_only"]:
        raise ValidationError("Invalid profile visibility setting")
    
    if dto.specialties is not None and len(dto.specialties) > 10:
        raise ValidationError("Cannot have more than 10 specialties")
    
    # Validate Plant Care preferences
    if dto.plant_care_preferences:
        _validate_plant_care_preferences(dto.plant_care_preferences)
    
    # Validate notification preferences
    if dto.notification_preferences:
        _validate_notification_preferences(dto.notification_preferences)


def _validate_plant_care_preferences(preferences: Dict[str, Any]) -> None:
    """Validate Plant Care preferences."""
    if "watering_reminder_frequency" in preferences:
        days = preferences["watering_reminder_frequency"]
        if not isinstance(days, int) or days < 1 or days > 30:
            raise ValidationError("Watering reminder frequency must be between 1-30 days")
    
    if "fertilizing_reminder_frequency" in preferences:
        days = preferences["fertilizing_reminder_frequency"]
        if not isinstance(days, int) or days < 1 or days > 365:
            raise ValidationError("Fertilizing reminder frequency must be between 1-365 days")
    
    if "preferred_care_difficulty" in preferences:
        difficulty = preferences["preferred_care_difficulty"]
        if difficulty not in ["easy", "moderate", "challenging", "expert"]:
            raise ValidationError("Invalid care difficulty level")
    
    if "care_notification_time" in preferences:
        time_str = preferences["care_notification_time"]
        try:
            # Validate HH:MM format
            time_parts = time_str.split(":")
            if len(time_parts) != 2:
                raise ValueError()
            hour, minute = int(time_parts[0]), int(time_parts[1])
            if hour < 0 or hour > 23 or minute < 0 or minute > 59:
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValidationError("Care reminder time must be in HH:MM format")
    
    # Validate boolean preferences
    boolean_prefs = [
        "weekend_care_reminders", 
        "seasonal_care_adjustments"
    ]
    for pref in boolean_prefs:
        if pref in preferences and not isinstance(preferences[pref], bool):
            raise ValidationError(f"{pref} must be a boolean value")


def _validate_notification_preferences(preferences: Dict[str, bool]) -> None:
    """Validate notification preferences."""
    valid_preferences = [
        "email_notifications",
        "push_notifications", 
        "care_reminders",
        "plant_health_alerts",
        "community_updates",
        "expert_tips",
        "marketing_emails"
    ]
    
    for key, value in preferences.items():
        if key not in valid_preferences:
            raise ValidationError(f"Invalid notification preference: {key}")
        if not isinstance(value, bool):
            raise ValidationError(f"Notification preference '{key}' must be a boolean value")


def merge_profile_preferences(existing: Dict[str, Any], 
                            updates: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge profile preference updates with existing preferences.
    
    Args:
        existing: Existing preferences
        updates: New preference updates
        
    Returns:
        Dict[str, Any]: Merged preferences
    """
    merged = existing.copy()
    merged.update(updates)
    
    # Ensure required defaults are present
    defaults = {
        "watering_reminder_frequency": 1,
        "fertilizing_reminder_frequency": 30,
        "preferred_care_difficulty": "easy",
        "care_notification_time": "09:00",
        "weekend_care_reminders": True,
        "seasonal_care_adjustments": True
    }
    
    for key, default_value in defaults.items():
        if key not in merged:
            merged[key] = default_value
    
    return merged


def get_default_notification_preferences() -> Dict[str, bool]:
    """Get default notification preferences for new profiles."""
    return {
        "email_notifications": True,
        "push_notifications": True,
        "care_reminders": True,
        "plant_health_alerts": True,
        "community_updates": True,
        "expert_tips": True,
        "marketing_emails": False  # Privacy-friendly default
    }


def get_profile_completion_recommendations(profile: Profile) -> List[str]:
    """Get recommendations for improving profile completion."""
    recommendations = []
    
    if not profile.bio:
        recommendations.append("Add a bio to help others know about your plant care journey")
    
    if not profile.avatar_url:
        recommendations.append("Upload a profile picture to personalize your account")
    
    if not profile.location:
        recommendations.append("Add your location for local plant care tips and weather integration")
    
    if not profile.specialties or len(profile.specialties) == 0:
        recommendations.append("Add your plant specialties to connect with like-minded gardeners")
    
    if profile.plant_count == 0:
        recommendations.append("Add your first plant to start tracking your garden")
    
    if profile.experience_level == ExperienceLevel.BEGINNER and profile.plant_count > 5:
        recommendations.append("Consider updating your experience level based on your plant collection")
    
    return recommendations


def generate_expert_badges(profile: Profile) -> List[str]:
    """Generate expert achievement badges based on profile data."""
    badges = []
    
    if profile.is_expert_verified and profile.expert_verification_status == "approved":
        badges.append("verified_expert")
    
    if profile.expert_rating and profile.expert_rating >= Decimal("4.5"):
        badges.append("top_rated")
    
    if profile.total_consultations and profile.total_consultations >= 100:
        badges.append("consultation_master")
    
    if profile.followers_count >= 1000:
        badges.append("community_leader")
    
    if profile.plant_count >= 50:
        badges.append("plant_collector")
    
    years_exp = _calculate_years_of_experience(profile)
    if years_exp >= 5:
        badges.append("experienced_gardener")
    
    return badges


def calculate_profile_completion_score(profile: Profile) -> float:
    """
    Calculate profile completion score as percentage.
    
    Args:
        profile: Profile domain model
        
    Returns:
        float: Completion score from 0.0 to 100.0
    """
    completion_data = _calculate_profile_completion_dto(profile)
    return completion_data["percentage"]


def is_profile_search_visible(profile: Profile, current_user_id: Optional[str] = None) -> bool:
    """
    Check if profile should be visible in search results.
    
    Args:
        profile: Profile domain model
        current_user_id: ID of user performing search
        
    Returns:
        bool: True if profile should be visible in search
    """
    # Private profiles are not visible in search
    if profile.profile_visibility == ProfileVisibility.PRIVATE:
        return False
    
    # Inactive profiles are not visible
    if profile.status != ProfileStatus.ACTIVE:
        return False
    
    # Public profiles are always visible
    if profile.profile_visibility == ProfileVisibility.PUBLIC:
        return True
    
    # Followers-only profiles need additional checking
    if profile.profile_visibility == ProfileVisibility.FOLLOWERS_ONLY:
        # TODO: Check if current_user_id is following this profile
        # This would require a follow relationship check
        return False
    
    return True


def can_user_follow_profile(profile: Profile, current_user_id: str) -> bool:
    """
    Check if current user can follow this profile.
    
    Args:
        profile: Profile domain model to follow
        current_user_id: ID of user wanting to follow
        
    Returns:
        bool: True if user can follow this profile
    """
    # Can't follow yourself
    if profile.user_id == current_user_id:
        return False
    
    # Can't follow private profiles (unless already following)
    if profile.profile_visibility == ProfileVisibility.PRIVATE:
        return False
    
    # Can't follow inactive profiles
    if profile.status != ProfileStatus.ACTIVE:
        return False
    
    return True


def format_expert_specialties(specialties: List[str]) -> str:
    """
    Format expert specialties for display.
    
    Args:
        specialties: List of specialty strings
        
    Returns:
        str: Formatted specialty string
    """
    if not specialties:
        return "General Plant Care"
    
    if len(specialties) == 1:
        return specialties[0].title()
    elif len(specialties) == 2:
        return f"{specialties[0].title()} & {specialties[1].title()}"
    else:
        return f"{specialties[0].title()}, {specialties[1].title()} +{len(specialties)-2} more"


def get_experience_level_display(experience_level: str) -> Dict[str, Any]:
    """
    Get display information for experience level.
    
    Args:
        experience_level: Experience level string
        
    Returns:
        Dict[str, Any]: Display information
    """
    experience_map = {
        "beginner": {
            "display": "Beginner",
            "description": "New to plant care",
            "icon": "🌱",
            "color": "#4CAF50"
        },
        "intermediate": {
            "display": "Intermediate", 
            "description": "Some plant care experience",
            "icon": "🌿",
            "color": "#2196F3"
        },
        "advanced": {
            "display": "Advanced",
            "description": "Experienced plant caretaker", 
            "icon": "🌳",
            "color": "#FF9800"
        },
        "expert": {
            "display": "Expert",
            "description": "Plant care professional",
            "icon": "🏆", 
            "color": "#9C27B0"
        }
    }
    
    return experience_map.get(experience_level, experience_map["beginner"])


def get_profile_summary_stats(profile: Profile) -> Dict[str, Any]:
    """
    Get summary statistics for a profile.
    
    Args:
        profile: Profile domain model
        
    Returns:
        Dict[str, Any]: Summary statistics
    """
    completion_score = calculate_profile_completion_score(profile)
    experience_info = get_experience_level_display(profile.experience_level.value)
    
    stats = {
        "profile_completion": completion_score,
        "experience_level": experience_info,
        "social": {
            "followers_count": profile.followers_count,
            "following_count": profile.following_count,
            "is_expert": profile.is_expert_verified
        },
        "activity": {
            "created_at": profile.created_at.isoformat(),
            "updated_at": profile.updated_at.isoformat(),
            "days_since_creation": (datetime.utcnow() - profile.created_at).days
        }
    }
    
    # Add expert-specific stats if applicable
    if profile.is_expert_verified:
        stats["expert"] = {
            "rating": float(profile.expert_rating) if profile.expert_rating else 0.0,
            "reviews_count": profile.expert_reviews_count,
            "specialties_count": len(profile.expert_specialties or []),
            "verification_date": profile.verification_approved_at.isoformat() if profile.verification_approved_at else None
        }
    
    return stats


def create_profile_for_api_response(profile: Profile, 
                                   current_user_id: Optional[str] = None,
                                   include_sensitive: bool = False) -> Dict[str, Any]:
    """
    Create profile data optimized for API responses.
    
    Args:
        profile: Profile domain model
        current_user_id: Current user's ID (for permission checks)
        include_sensitive: Whether to include sensitive data
        
    Returns:
        Dict[str, Any]: API-optimized profile data
    """
    # Base profile data
    profile_data = {
        "profile_id": profile.profile_id,
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "avatar_url": profile.avatar_url,
        "experience_level": profile.experience_level.value,
        "is_expert_verified": profile.is_expert_verified,
        "created_at": profile.created_at.isoformat()
    }
    
    # Add public information based on visibility settings
    if profile.profile_visibility == ProfileVisibility.PUBLIC or current_user_id == profile.user_id:
        profile_data.update({
            "bio": profile.bio,
            "location": profile.location,
            "followers_count": profile.followers_count,
            "following_count": profile.following_count
        })
    
    # Add expert information if verified
    if profile.is_expert_verified:
        profile_data["expert"] = {
            "rating": float(profile.expert_rating) if profile.expert_rating else 0.0,
            "reviews_count": profile.expert_reviews_count,
            "specialties": profile.expert_specialties or []
        }
    
    # Add sensitive information only for profile owner
    if include_sensitive and current_user_id == profile.user_id:
        profile_data.update({
            "timezone": profile.timezone,
            "preferred_units": profile.preferred_units.value,
            "profile_visibility": profile.profile_visibility.value,
            "plant_care_preferences": profile.plant_care_preferences,
            "notification_preferences": profile.notification_preferences,
            "profile_completion": calculate_profile_completion_score(profile)
        })
    
    return profile_data