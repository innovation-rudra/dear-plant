# app/modules/user_management/domain/models/profile.py
"""
Plant Care Application - Profile Domain Model

Extended user profile for the Plant Care Application.
Contains Plant Care specific preferences, settings, and profile information.
"""

import uuid
from datetime import datetime
from enum import Enum
from typing import Optional, Dict, Any, List
from dataclasses import dataclass, field

import structlog

# Setup logger
logger = structlog.get_logger(__name__)


class NotificationType(str, Enum):
    """Types of notifications in Plant Care Application."""
    WATERING_REMINDER = "watering_reminder"
    FERTILIZING_REMINDER = "fertilizing_reminder"
    REPOTTING_REMINDER = "repotting_reminder"
    PLANT_HEALTH_ALERT = "plant_health_alert"
    COMMUNITY_UPDATES = "community_updates"
    EXPERT_RESPONSES = "expert_responses"
    WEEKLY_SUMMARY = "weekly_summary"
    PROMOTIONAL = "promotional"


class MeasurementUnit(str, Enum):
    """Measurement units for Plant Care Application."""
    METRIC = "metric"      # Celsius, cm, ml, kg
    IMPERIAL = "imperial"  # Fahrenheit, inches, fl oz, lbs


class PrivacyLevel(str, Enum):
    """Privacy levels for profile visibility."""
    PUBLIC = "public"      # Visible to all users
    FRIENDS = "friends"    # Visible to friends only
    PRIVATE = "private"    # Visible only to user


@dataclass
class NotificationSettings:
    """
    User notification preferences for Plant Care Application.
    Controls when and how users receive notifications.
    """
    
    # Care reminders
    watering_reminders: bool = True
    fertilizing_reminders: bool = True
    repotting_reminders: bool = True
    
    # Plant health
    health_alerts: bool = True
    growth_milestones: bool = True
    
    # Community
    community_updates: bool = True
    expert_responses: bool = True
    
    # Summary and promotional
    weekly_summary: bool = True
    promotional: bool = False
    
    # Delivery methods
    email_notifications: bool = True
    push_notifications: bool = True
    sms_notifications: bool = False
    
    # Timing preferences
    quiet_hours_start: str = "22:00"  # 10 PM
    quiet_hours_end: str = "08:00"    # 8 AM
    timezone: str = "UTC"
    
    def is_notification_enabled(self, notification_type: NotificationType) -> bool:
        """
        Check if specific notification type is enabled.
        
        Args:
            notification_type: Type of notification to check
            
        Returns:
            bool: True if notification is enabled
        """
        mapping = {
            NotificationType.WATERING_REMINDER: self.watering_reminders,
            NotificationType.FERTILIZING_REMINDER: self.fertilizing_reminders,
            NotificationType.REPOTTING_REMINDER: self.repotting_reminders,
            NotificationType.PLANT_HEALTH_ALERT: self.health_alerts,
            NotificationType.COMMUNITY_UPDATES: self.community_updates,
            NotificationType.EXPERT_RESPONSES: self.expert_responses,
            NotificationType.WEEKLY_SUMMARY: self.weekly_summary,
            NotificationType.PROMOTIONAL: self.promotional,
        }
        
        return mapping.get(notification_type, False)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "watering_reminders": self.watering_reminders,
            "fertilizing_reminders": self.fertilizing_reminders,
            "repotting_reminders": self.repotting_reminders,
            "health_alerts": self.health_alerts,
            "growth_milestones": self.growth_milestones,
            "community_updates": self.community_updates,
            "expert_responses": self.expert_responses,
            "weekly_summary": self.weekly_summary,
            "promotional": self.promotional,
            "email_notifications": self.email_notifications,
            "push_notifications": self.push_notifications,
            "sms_notifications": self.sms_notifications,
            "quiet_hours_start": self.quiet_hours_start,
            "quiet_hours_end": self.quiet_hours_end,
            "timezone": self.timezone,
        }


@dataclass
class UserPreferences:
    """
    Plant Care specific user preferences.
    Controls application behavior and default settings.
    """
    
    # Measurement preferences
    measurement_unit: MeasurementUnit = MeasurementUnit.METRIC
    
    # Location for weather-based recommendations
    location: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    
    # Plant care preferences
    care_reminder_advance_days: int = 1  # Days before care task due
    default_watering_frequency: int = 7  # Default days between watering
    
    # Display preferences
    theme: str = "light"  # light, dark, auto
    language: str = "en"  # ISO language code
    
    # Privacy preferences
    profile_visibility: PrivacyLevel = PrivacyLevel.PUBLIC
    share_plant_collection: bool = True
    share_care_progress: bool = True
    allow_expert_contact: bool = True
    
    # Expert preferences (for expert users)
    expert_specialties: List[str] = field(default_factory=list)  # Plant types they specialize in
    expert_available_for_consultation: bool = False
    
    def update_location(self, location: str, latitude: float, longitude: float) -> None:
        """
        Update user location for weather-based care recommendations.
        
        Args:
            location: Human-readable location name
            latitude: Latitude coordinate
            longitude: Longitude coordinate
        """
        if not (-90 <= latitude <= 90):
            raise ValueError("Latitude must be between -90 and 90")
        if not (-180 <= longitude <= 180):
            raise ValueError("Longitude must be between -180 and 180")
        
        self.location = location
        self.latitude = latitude
        self.longitude = longitude
        
        logger.info("User location updated", location=location)
    
    def add_expert_specialty(self, specialty: str) -> None:
        """
        Add expert specialty for expert users.
        
        Args:
            specialty: Plant type or care specialty
        """
        if specialty and specialty not in self.expert_specialties:
            self.expert_specialties.append(specialty)
    
    def remove_expert_specialty(self, specialty: str) -> None:
        """
        Remove expert specialty.
        
        Args:
            specialty: Specialty to remove
        """
        if specialty in self.expert_specialties:
            self.expert_specialties.remove(specialty)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "measurement_unit": self.measurement_unit.value,
            "location": self.location,
            "latitude": self.latitude,
            "longitude": self.longitude,
            "care_reminder_advance_days": self.care_reminder_advance_days,
            "default_watering_frequency": self.default_watering_frequency,
            "theme": self.theme,
            "language": self.language,
            "profile_visibility": self.profile_visibility.value,
            "share_plant_collection": self.share_plant_collection,
            "share_care_progress": self.share_care_progress,
            "allow_expert_contact": self.allow_expert_contact,
            "expert_specialties": self.expert_specialties,
            "expert_available_for_consultation": self.expert_available_for_consultation,
        }


@dataclass
class Profile:
    """
    Extended user profile for Plant Care Application.
    Contains personal information, preferences, and Plant Care specific settings.
    """
    
    # Identity
    profile_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    user_id: str = ""
    
    # Personal Information
    display_name: Optional[str] = None
    first_name: Optional[str] = None
    last_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None
    
    # Plant Care Information
    experience_level: str = "beginner"  # beginner, intermediate, advanced, expert
    favorite_plant_types: List[str] = field(default_factory=list)
    gardening_goals: List[str] = field(default_factory=list)
    
    # Preferences and Settings
    preferences: UserPreferences = field(default_factory=UserPreferences)
    notification_settings: NotificationSettings = field(default_factory=NotificationSettings)
    
    # Social Features
    follower_count: int = 0
    following_count: int = 0
    is_verified_expert: bool = False
    expert_rating: Optional[float] = None
    
    # Timestamps
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    
    # Metadata
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Post-initialization validation."""
        self._validate_profile_id()
        self._validate_user_id()
        self._validate_bio()
        
    def _validate_profile_id(self) -> None:
        """Validate profile ID format."""
        if not self.profile_id:
            raise ValueError("Profile ID is required")
        
        try:
            uuid.UUID(self.profile_id)
        except ValueError:
            raise ValueError("Invalid profile ID format")
    
    def _validate_user_id(self) -> None:
        """Validate user ID format."""
        if not self.user_id:
            raise ValueError("User ID is required")
        
        try:
            uuid.UUID(self.user_id)
        except ValueError:
            raise ValueError("Invalid user ID format")
    
    def _validate_bio(self) -> None:
        """Validate bio length."""
        if self.bio and len(self.bio) > 500:
            raise ValueError("Bio cannot exceed 500 characters")
    
    def update_personal_info(self, display_name: Optional[str] = None, 
                           first_name: Optional[str] = None,
                           last_name: Optional[str] = None, 
                           bio: Optional[str] = None) -> None:
        """
        Update personal information.
        
        Args:
            display_name: Display name for profile
            first_name: First name
            last_name: Last name
            bio: User bio/description
        """
        if display_name is not None:
            self.display_name = display_name.strip() if display_name else None
            
        if first_name is not None:
            self.first_name = first_name.strip() if first_name else None
            
        if last_name is not None:
            self.last_name = last_name.strip() if last_name else None
            
        if bio is not None:
            if bio and len(bio) > 500:
                raise ValueError("Bio cannot exceed 500 characters")
            self.bio = bio.strip() if bio else None
        
        self.updated_at = datetime.utcnow()
        
        logger.info("Profile personal info updated", 
                   profile_id=self.profile_id, user_id=self.user_id)
    
    def update_avatar(self, avatar_url: str) -> None:
        """
        Update profile avatar.
        
        Args:
            avatar_url: URL to avatar image
        """
        if not avatar_url:
            raise ValueError("Avatar URL is required")
        
        # Basic URL validation
        if not avatar_url.startswith(('http://', 'https://')):
            raise ValueError("Invalid avatar URL format")
        
        self.avatar_url = avatar_url
        self.updated_at = datetime.utcnow()
        
        logger.info("Profile avatar updated", profile_id=self.profile_id)
    
    def update_experience_level(self, level: str) -> None:
        """
        Update gardening experience level.
        
        Args:
            level: Experience level (beginner, intermediate, advanced, expert)
        """
        valid_levels = ["beginner", "intermediate", "advanced", "expert"]
        if level not in valid_levels:
            raise ValueError(f"Invalid experience level. Must be one of: {valid_levels}")
        
        self.experience_level = level
        self.updated_at = datetime.utcnow()
        
        logger.info("Experience level updated", 
                   profile_id=self.profile_id, level=level)
    
    def add_favorite_plant_type(self, plant_type: str) -> None:
        """
        Add favorite plant type.
        
        Args:
            plant_type: Type of plant (e.g., "succulents", "herbs", "flowering")
        """
        if not plant_type:
            raise ValueError("Plant type is required")
        
        plant_type = plant_type.strip().lower()
        if plant_type not in self.favorite_plant_types:
            self.favorite_plant_types.append(plant_type)
            self.updated_at = datetime.utcnow()
    
    def remove_favorite_plant_type(self, plant_type: str) -> None:
        """
        Remove favorite plant type.
        
        Args:
            plant_type: Plant type to remove
        """
        plant_type = plant_type.strip().lower()
        if plant_type in self.favorite_plant_types:
            self.favorite_plant_types.remove(plant_type)
            self.updated_at = datetime.utcnow()
    
    def add_gardening_goal(self, goal: str) -> None:
        """
        Add gardening goal.
        
        Args:
            goal: Gardening goal (e.g., "grow herbs for cooking", "create indoor garden")
        """
        if not goal:
            raise ValueError("Goal is required")
        
        goal = goal.strip()
        if goal not in self.gardening_goals:
            self.gardening_goals.append(goal)
            self.updated_at = datetime.utcnow()
    
    def remove_gardening_goal(self, goal: str) -> None:
        """
        Remove gardening goal.
        
        Args:
            goal: Goal to remove
        """
        goal = goal.strip()
        if goal in self.gardening_goals:
            self.gardening_goals.remove(goal)
            self.updated_at = datetime.utcnow()
    
    def verify_as_expert(self, rating: float = 5.0) -> None:
        """
        Verify user as plant care expert.
        
        Args:
            rating: Initial expert rating (1.0 to 5.0)
        """
        if not (1.0 <= rating <= 5.0):
            raise ValueError("Expert rating must be between 1.0 and 5.0")
        
        self.is_verified_expert = True
        self.expert_rating = rating
        self.experience_level = "expert"
        self.updated_at = datetime.utcnow()
        
        logger.info("User verified as expert", 
                   profile_id=self.profile_id, rating=rating)
    
    def update_expert_rating(self, new_rating: float) -> None:
        """
        Update expert rating.
        
        Args:
            new_rating: New expert rating (1.0 to 5.0)
        """
        if not self.is_verified_expert:
            raise ValueError("User is not a verified expert")
        
        if not (1.0 <= new_rating <= 5.0):
            raise ValueError("Expert rating must be between 1.0 and 5.0")
        
        self.expert_rating = new_rating
        self.updated_at = datetime.utcnow()
    
    def update_social_counts(self, followers: int, following: int) -> None:
        """
        Update follower and following counts.
        
        Args:
            followers: Number of followers
            following: Number of users being followed
        """
        if followers < 0 or following < 0:
            raise ValueError("Social counts cannot be negative")
        
        self.follower_count = followers
        self.following_count = following
        self.updated_at = datetime.utcnow()
    
    def get_display_name(self) -> str:
        """
        Get display name for profile.
        Fallback logic: display_name -> first_name last_name -> email prefix
        
        Returns:
            str: Display name to show in UI
        """
        if self.display_name:
            return self.display_name
        
        if self.first_name or self.last_name:
            return f"{self.first_name or ''} {self.last_name or ''}".strip()
        
        # Fallback to user email prefix (handled by caller)
        return "Plant Lover"
    
    def is_public_profile(self) -> bool:
        """Check if profile is publicly visible."""
        return self.preferences.profile_visibility == PrivacyLevel.PUBLIC
    
    def can_be_contacted_by_experts(self) -> bool:
        """Check if user allows expert contact."""
        return self.preferences.allow_expert_contact
    
    def get_location_info(self) -> Optional[Dict[str, Any]]:
        """
        Get location information for weather-based recommendations.
        
        Returns:
            Optional[Dict[str, Any]]: Location data or None
        """
        if self.preferences.location and self.preferences.latitude and self.preferences.longitude:
            return {
                "location": self.preferences.location,
                "latitude": self.preferences.latitude,
                "longitude": self.preferences.longitude,
            }
        return None
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert profile to dictionary for serialization.
        
        Returns:
            Dict[str, Any]: Profile data as dictionary
        """
        return {
            "profile_id": self.profile_id,
            "user_id": self.user_id,
            "display_name": self.display_name,
            "first_name": self.first_name,
            "last_name": self.last_name,
            "bio": self.bio,
            "avatar_url": self.avatar_url,
            "experience_level": self.experience_level,
            "favorite_plant_types": self.favorite_plant_types,
            "gardening_goals": self.gardening_goals,
            "preferences": self.preferences.to_dict(),
            "notification_settings": self.notification_settings.to_dict(),
            "follower_count": self.follower_count,
            "following_count": self.following_count,
            "is_verified_expert": self.is_verified_expert,
            "expert_rating": self.expert_rating,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "metadata": self.metadata,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Profile":
        """
        Create profile from dictionary.
        
        Args:
            data: Profile data dictionary
            
        Returns:
            Profile: Profile instance
        """
        # Parse datetime fields
        created_at = datetime.fromisoformat(data["created_at"]) if data.get("created_at") else datetime.utcnow()
        updated_at = datetime.fromisoformat(data["updated_at"]) if data.get("updated_at") else datetime.utcnow()
        
        # Parse preferences
        preferences_data = data.get("preferences", {})
        preferences = UserPreferences(
            measurement_unit=MeasurementUnit(preferences_data.get("measurement_unit", MeasurementUnit.METRIC.value)),
            location=preferences_data.get("location"),
            latitude=preferences_data.get("latitude"),
            longitude=preferences_data.get("longitude"),
            care_reminder_advance_days=preferences_data.get("care_reminder_advance_days", 1),
            default_watering_frequency=preferences_data.get("default_watering_frequency", 7),
            theme=preferences_data.get("theme", "light"),
            language=preferences_data.get("language", "en"),
            profile_visibility=PrivacyLevel(preferences_data.get("profile_visibility", PrivacyLevel.PUBLIC.value)),
            share_plant_collection=preferences_data.get("share_plant_collection", True),
            share_care_progress=preferences_data.get("share_care_progress", True),
            allow_expert_contact=preferences_data.get("allow_expert_contact", True),
            expert_specialties=preferences_data.get("expert_specialties", []),
            expert_available_for_consultation=preferences_data.get("expert_available_for_consultation", False),
        )
        
        # Parse notification settings
        notification_data = data.get("notification_settings", {})
        notification_settings = NotificationSettings(
            watering_reminders=notification_data.get("watering_reminders", True),
            fertilizing_reminders=notification_data.get("fertilizing_reminders", True),
            repotting_reminders=notification_data.get("repotting_reminders", True),
            health_alerts=notification_data.get("health_alerts", True),
            growth_milestones=notification_data.get("growth_milestones", True),
            community_updates=notification_data.get("community_updates", True),
            expert_responses=notification_data.get("expert_responses", True),
            weekly_summary=notification_data.get("weekly_summary", True),
            promotional=notification_data.get("promotional", False),
            email_notifications=notification_data.get("email_notifications", True),
            push_notifications=notification_data.get("push_notifications", True),
            sms_notifications=notification_data.get("sms_notifications", False),
            quiet_hours_start=notification_data.get("quiet_hours_start", "22:00"),
            quiet_hours_end=notification_data.get("quiet_hours_end", "08:00"),
            timezone=notification_data.get("timezone", "UTC"),
        )
        
        return cls(
            profile_id=data["profile_id"],
            user_id=data["user_id"],
            display_name=data.get("display_name"),
            first_name=data.get("first_name"),
            last_name=data.get("last_name"),
            bio=data.get("bio"),
            avatar_url=data.get("avatar_url"),
            experience_level=data.get("experience_level", "beginner"),
            favorite_plant_types=data.get("favorite_plant_types", []),
            gardening_goals=data.get("gardening_goals", []),
            preferences=preferences,
            notification_settings=notification_settings,
            follower_count=data.get("follower_count", 0),
            following_count=data.get("following_count", 0),
            is_verified_expert=data.get("is_verified_expert", False),
            expert_rating=data.get("expert_rating"),
            created_at=created_at,
            updated_at=updated_at,
            metadata=data.get("metadata", {}),
        )
    
    def __str__(self) -> str:
        display_name = self.get_display_name()
        return f"Profile(id={self.profile_id}, user={self.user_id}, name={display_name})"
    
    def __repr__(self) -> str:
        return self.__str__()