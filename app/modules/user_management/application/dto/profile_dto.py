# app/modules/user_management/application/dto/profile_dto.py
"""
Plant Care Application - Profile Management DTOs

Data Transfer Objects for profile-related operations in the Plant Care Application.
Defines data structures for profile creation, updates, preferences, and expert features.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from decimal import Decimal
from dataclasses import dataclass, field

from app.modules.user_management.domain.models.profile import (
    Profile, ProfileStatus, ExperienceLevel, PreferredUnits, ProfileVisibility
)


@dataclass
class ProfileDTO:
    """
    Complete profile data transfer object for Plant Care Application.
    Used for detailed profile information including Plant Care preferences.
    """
    # Core profile data
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    
    # Plant Care information
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    specialties: List[str] = field(default_factory=list)
    plant_count: int = 0
    
    # Expert information
    is_expert_verified: bool = False
    expert_rating: Optional[float] = None
    expert_reviews_count: int = 0
    
    # Social metrics
    followers_count: int = 0
    following_count: int = 0
    
    # Search relevance
    relevance_score: float = 0.0
    match_criteria: List[str] = field(default_factory=list)
    distance_km: Optional[float] = None  # If location-based search
    
    # Interaction capabilities
    can_follow: bool = True
    can_message: bool = True
    can_book_consultation: bool = False
    
    # Profile status
    profile_visibility: str = "public"
    is_active: bool = True
    last_activity: Optional[str] = None


@dataclass
class ExpertProfileDTO:
    """
    Expert profile data transfer object.
    Specialized for verified expert profiles with additional expert information.
    """
    # Basic profile information
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] = None
    
    # Expert verification
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
    
    # Social proof
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


# Factory functions for creating DTOs from domain models

def create_profile_dto(profile: Profile, current_user_id: Optional[str] = None,
                      is_following: bool = False, plant_count: int = 0) -> ProfileDTO:
    """
    Create ProfileDTO from domain Profile model.
    
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


def _calculate_profile_completion_dto(profile: Profile) -> Dict[str, Any]:
    """Calculate profile completion for DTO."""
    total_fields = 10
    completed_fields = 0
    missing_fields = []
    
    # Check completion of important fields
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
    """Generate expert badges based on profile and performance."""
    badges = []
    
    # Verification badge
    if profile.is_expert_verified:
        badges.append({
            "type": "verification",
            "title": "Verified Expert",
            "description": "Verified plant care expert",
            "icon": "verified",
            "color": "#4CAF50"
        })
    
    # Rating badges
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
    
    # Speciality badges
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
    """Calculate years of experience from profile creation and verification."""
    if not profile.verification_approved_at:
        return 0
    
    years = (datetime.utcnow() - profile.verification_approved_at).days // 365
    return max(0, years)


# Additional utility functions for profile DTOs

def validate_profile_creation_dto(dto: ProfileCreationDTO) -> List[str]:
    """
    Validate profile creation DTO.
    
    Args:
        dto: ProfileCreationDTO to validate
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Validate display name
    if not dto.display_name or len(dto.display_name.strip()) < 2:
        errors.append("Display name must be at least 2 characters long")
    
    if len(dto.display_name) > 100:
        errors.append("Display name cannot exceed 100 characters")
    
    # Validate bio if provided
    if dto.bio and len(dto.bio) > 500:
        errors.append("Bio cannot exceed 500 characters")
    
    # Validate location if provided
    if dto.location and len(dto.location) > 200:
        errors.append("Location cannot exceed 200 characters")
    
    # Validate experience level
    valid_levels = ["beginner", "intermediate", "advanced", "expert"]
    if dto.experience_level not in valid_levels:
        errors.append(f"Experience level must be one of: {', '.join(valid_levels)}")
    
    # Validate preferred units
    valid_units = ["metric", "imperial"]
    if dto.preferred_units not in valid_units:
        errors.append(f"Preferred units must be one of: {', '.join(valid_units)}")
    
    # Validate profile visibility
    valid_visibility = ["public", "private", "followers_only"]
    if dto.profile_visibility not in valid_visibility:
        errors.append(f"Profile visibility must be one of: {', '.join(valid_visibility)}")
    
    # Validate plant care preferences
    if dto.plant_care_preferences:
        pref_errors = _validate_plant_care_preferences(dto.plant_care_preferences)
        errors.extend(pref_errors)
    
    # Validate notification preferences
    if dto.notification_preferences:
        notif_errors = _validate_notification_preferences(dto.notification_preferences)
        errors.extend(notif_errors)
    
    return errors


def validate_profile_update_dto(dto: ProfileUpdateDTO) -> List[str]:
    """
    Validate profile update DTO.
    
    Args:
        dto: ProfileUpdateDTO to validate
        
    Returns:
        List[str]: List of validation errors
    """
    errors = []
    
    # Validate display name if provided
    if dto.display_name is not None:
        if not dto.display_name or len(dto.display_name.strip()) < 2:
            errors.append("Display name must be at least 2 characters long")
        if len(dto.display_name) > 100:
            errors.append("Display name cannot exceed 100 characters")
    
    # Validate bio if provided
    if dto.bio is not None and len(dto.bio) > 500:
        errors.append("Bio cannot exceed 500 characters")
    
    # Validate location if provided
    if dto.location is not None and len(dto.location) > 200:
        errors.append("Location cannot exceed 200 characters")
    
    # Validate experience level if provided
    if dto.experience_level is not None:
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if dto.experience_level not in valid_levels:
            errors.append(f"Experience level must be one of: {', '.join(valid_levels)}")
    
    # Validate preferred units if provided
    if dto.preferred_units is not None:
        valid_units = ["metric", "imperial"]
        if dto.preferred_units not in valid_units:
            errors.append(f"Preferred units must be one of: {', '.join(valid_units)}")
    
    # Validate profile visibility if provided
    if dto.profile_visibility is not None:
        valid_visibility = ["public", "private", "followers_only"]
        if dto.profile_visibility not in valid_visibility:
            errors.append(f"Profile visibility must be one of: {', '.join(valid_visibility)}")
    
    # Validate plant care preferences if provided
    if dto.plant_care_preferences is not None:
        pref_errors = _validate_plant_care_preferences(dto.plant_care_preferences)
        errors.extend(pref_errors)
    
    # Validate notification preferences if provided
    if dto.notification_preferences is not None:
        notif_errors = _validate_notification_preferences(dto.notification_preferences)
        errors.extend(notif_errors)
    
    return errors


def _validate_plant_care_preferences(preferences: Dict[str, Any]) -> List[str]:
    """Validate plant care preferences."""
    errors = []
    
    # Validate watering reminder frequency
    if "watering_reminder_frequency" in preferences:
        freq = preferences["watering_reminder_frequency"]
        if not isinstance(freq, int) or freq < 1 or freq > 30:
            errors.append("Watering reminder frequency must be between 1-30 days")
    
    # Validate fertilizing reminder frequency
    if "fertilizing_reminder_frequency" in preferences:
        freq = preferences["fertilizing_reminder_frequency"]
        if not isinstance(freq, int) or freq < 1 or freq > 365:
            errors.append("Fertilizing reminder frequency must be between 1-365 days")
    
    # Validate preferred care difficulty
    if "preferred_care_difficulty" in preferences:
        difficulty = preferences["preferred_care_difficulty"]
        valid_difficulties = ["easy", "moderate", "challenging", "expert"]
        if difficulty not in valid_difficulties:
            errors.append(f"Preferred care difficulty must be one of: {', '.join(valid_difficulties)}")
    
    # Validate care notification time
    if "care_notification_time" in preferences:
        time_str = preferences["care_notification_time"]
        try:
            # Validate time format (HH:MM)
            datetime.strptime(time_str, "%H:%M")
        except ValueError:
            errors.append("Care notification time must be in HH:MM format")
    
    # Validate boolean preferences
    bool_prefs = ["weekend_care_reminders", "seasonal_care_adjustments"]
    for pref in bool_prefs:
        if pref in preferences and not isinstance(preferences[pref], bool):
            errors.append(f"{pref} must be a boolean value")
    
    return errors


def _validate_notification_preferences(preferences: Dict[str, Any]) -> List[str]:
    """Validate notification preferences."""
    errors = []
    
    # All notification preferences should be boolean
    for key, value in preferences.items():
        if not isinstance(value, bool):
            errors.append(f"Notification preference '{key}' must be a boolean value")
    
    return errors


def create_profile_list_dto(profiles: List[Profile], 
                           total_count: int, 
                           page: int = 1, 
                           page_size: int = 20,
                           filters: Dict[str, Any] = None) -> Dict[str, Any]:
    """
    Create a paginated profile list DTO.
    
    Args:
        profiles: List of Profile domain models
        total_count: Total number of profiles
        page: Current page number
        page_size: Number of profiles per page
        filters: Applied filters
        
    Returns:
        Dict[str, Any]: Paginated profile list
    """
    profile_briefs = [create_profile_brief_dto(profile) for profile in profiles]
    
    total_pages = (total_count + page_size - 1) // page_size
    has_next = page < total_pages
    has_previous = page > 1
    
    return {
        "profiles": profile_briefs,
        "pagination": {
            "total_count": total_count,
            "page": page,
            "page_size": page_size,
            "total_pages": total_pages,
            "has_next": has_next,
            "has_previous": has_previous
        },
        "filters": filters or {},
        "generated_at": datetime.utcnow().isoformat()
    }


def create_expert_search_result_dto(profile: Profile, 
                                   consultation_data: Dict[str, Any] = None,
                                   relevance_score: float = 0.0,
                                   distance_km: Optional[float] = None) -> Dict[str, Any]:
    """
    Create expert search result DTO.
    
    Args:
        profile: Expert profile
        consultation_data: Consultation availability data
        relevance_score: Search relevance score
        distance_km: Distance from searcher
        
    Returns:
        Dict[str, Any]: Expert search result
    """
    if not profile.is_expert_verified:
        raise ValueError("Profile must be expert verified")
    
    consultation_data = consultation_data or {}
    
    return {
        "profile_id": profile.profile_id,
        "user_id": profile.user_id,
        "display_name": profile.display_name,
        "bio": profile.bio,
        "avatar_url": profile.avatar_url,
        "location": profile.location,
        "experience_level": profile.experience_level.value,
        "expert_specialties": profile.expert_specialties or [],
        "expert_rating": float(profile.expert_rating) if profile.expert_rating else 0.0,
        "expert_reviews_count": profile.expert_reviews_count,
        "consultation_price": consultation_data.get("price"),
        "consultation_duration": consultation_data.get("duration", 60),
        "is_available": consultation_data.get("is_available", True),
        "next_available_slot": consultation_data.get("next_available_slot"),
        "response_time_hours": consultation_data.get("response_time_hours", 24),
        "relevance_score": relevance_score,
        "distance_km": distance_km,
        "can_book_consultation": consultation_data.get("can_book", True)
    }


def merge_profile_preferences(existing_preferences: Dict[str, Any], 
                             new_preferences: Dict[str, Any]) -> Dict[str, Any]:
    """
    Merge new preferences with existing ones.
    
    Args:
        existing_preferences: Current preferences
        new_preferences: New preferences to merge
        
    Returns:
        Dict[str, Any]: Merged preferences
    """
    merged = existing_preferences.copy()
    
    # Update with new preferences
    merged.update(new_preferences)
    
    # Ensure required defaults are present
    default_plant_care = {
        "watering_reminder_frequency": 1,
        "fertilizing_reminder_frequency": 30,
        "preferred_care_difficulty": "easy",
        "preferred_plant_types": [],
        "care_notification_time": "09:00",
        "weekend_care_reminders": True,
        "seasonal_care_adjustments": True
    }
    
    default_notifications = {
        "email_notifications": True,
        "push_notifications": True,
        "care_reminders": True,
        "plant_health_alerts": True,
        "expert_advice": True,
        "community_updates": False,
        "marketing_emails": False,
        "weekly_digest": True
    }
    
    # Apply defaults for missing keys
    for key, default_value in default_plant_care.items():
        if key not in merged:
            merged[key] = default_value
    
    # For notification preferences, if it's a notification merge
    if any(key in new_preferences for key in default_notifications.keys()):
        for key, default_value in default_notifications.items():
            if key not in merged:
                merged[key] = default_value
    
    return merged None
    timezone: str = "UTC"
    
    # Plant Care preferences
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Profile settings
    profile_visibility: str = "public"
    status: str = "active"
    
    # Expert information
    is_expert_verified: bool = False
    expert_verification_status: Optional[str] = None
    expert_credentials: Optional[Dict[str, Any]] = None
    expert_specialties: Optional[List[str]] = None
    expert_rating: Optional[float] = None
    expert_reviews_count: int = 0
    
    # Social features
    followers_count: int = 0
    following_count: int = 0
    
    # Plant Care preferences
    plant_care_preferences: Dict[str, Any] = field(default_factory=dict)
    notification_preferences: Dict[str, Any] = field(default_factory=dict)
    
    # Timestamps
    created_at: str = ""
    updated_at: str = ""
    verification_requested_at: Optional[str] = None
    verification_approved_at: Optional[str] = None
    
    # Computed fields
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
    Contains data needed for creating a new profile.
    """
    # Required fields
    user_id: str
    display_name: str
    
    # Optional basic info
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Plant Care preferences
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Profile settings
    profile_visibility: str = "public"
    
    # Plant Care preferences
    plant_care_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "watering_reminder_frequency": 1,  # days
        "fertilizing_reminder_frequency": 30,  # days
        "preferred_care_difficulty": "easy",
        "preferred_plant_types": [],
        "care_notification_time": "09:00",
        "weekend_care_reminders": True,
        "seasonal_care_adjustments": True
    })
    
    # Notification preferences
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
    Contains fields that can be updated in a profile.
    """
    # Basic information updates
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    
    # Plant Care preferences
    experience_level: Optional[str] = None
    preferred_units: Optional[str] = None
    
    # Profile settings
    profile_visibility: Optional[str] = None
    
    # Plant Care preferences updates
    plant_care_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    
    # Metadata
    updated_fields: List[str] = field(default_factory=list)
    update_reason: Optional[str] = None


@dataclass
class ProfilePreferencesDTO:
    """
    Profile preferences data transfer object.
    Focused on Plant Care and notification preferences.
    """
    # Plant Care preferences
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
    Contains avatar upload and management data.
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
    
    # Expert metrics (if applicable)
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
    Optimized for profile search and discovery.
    """
    profile_id: str
    user_id: str
    display_name: str
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    location: Optional[str] =