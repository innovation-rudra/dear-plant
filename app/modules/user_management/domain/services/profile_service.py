# app/modules/user_management/domain/services/profile_service.py
"""
Plant Care Application - Profile Domain Service

Profile management business logic for the Plant Care Application.
Handles profile creation, updates, preferences, expert verification, and avatar management.
"""

import uuid
from datetime import datetime
from typing import Optional, Dict, Any, List, Tuple
from decimal import Decimal

import structlog

from app.modules.user_management.domain.models.user import User, UserRole
from app.modules.user_management.domain.models.profile import (
    Profile, ProfileStatus, ExperienceLevel, PreferredUnits, ProfileVisibility
)
from app.modules.user_management.domain.repositories.user_repository import UserRepository
from app.modules.user_management.domain.repositories.profile_repository import ProfileRepository
from app.modules.user_management.domain.events.user_events import (
    ProfileCreated, ProfileUpdated, ProfileAvatarUpdated, ProfilePreferencesUpdated,
    ExpertVerificationRequested, ExpertVerificationApproved, ExpertVerificationRejected,
    ProfileFollowed, ProfileUnfollowed
)
from app.shared.events.base import EventPublisher
from app.shared.core.exceptions import (
    ValidationError, ResourceNotFoundError, BusinessLogicError,
    AuthorizationError, FileError
)
from app.shared.utils.validators import PlantCareValidator
from app.shared.utils.helpers import PlantCareHelpers

# Setup logger
logger = structlog.get_logger(__name__)


class ProfileService:
    """
    Domain service for profile management in Plant Care Application.
    Handles profile creation, updates, preferences, and expert features.
    """
    
    def __init__(self, 
                 user_repository: UserRepository,
                 profile_repository: ProfileRepository,
                 event_publisher: EventPublisher):
        """
        Initialize profile service.
        
        Args:
            user_repository: User data repository
            profile_repository: Profile data repository
            event_publisher: Event publisher for domain events
        """
        self.user_repository = user_repository
        self.profile_repository = profile_repository
        self.event_publisher = event_publisher
        self.max_bio_length = 500
        self.max_specialties = 10
        self.max_followers = 50000  # Premium feature limit
    
    async def create_profile(self, 
                           user_id: str,
                           display_name: str,
                           bio: Optional[str] = None,
                           location: Optional[str] = None,
                           timezone: Optional[str] = None,
                           preferred_units: PreferredUnits = PreferredUnits.METRIC,
                           experience_level: ExperienceLevel = ExperienceLevel.BEGINNER) -> Profile:
        """
        Create a new profile for Plant Care Application user.
        
        Args:
            user_id: User ID
            display_name: User's display name
            bio: User biography (optional)
            location: User location for weather integration
            timezone: User timezone
            preferred_units: Metric or Imperial units
            experience_level: Plant care experience level
            
        Returns:
            Profile: Created profile
            
        Raises:
            ValidationError: If profile data is invalid
            ResourceNotFoundError: If user not found
            BusinessLogicError: If profile already exists
        """
        try:
            logger.info("Creating profile", user_id=user_id, display_name=display_name)
            
            # Validate user exists
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")
            
            # Check if profile already exists
            existing_profile = await self.profile_repository.find_by_user_id(user_id)
            if existing_profile:
                raise BusinessLogicError("Profile already exists for this user")
            
            # Validate profile data
            await self._validate_profile_data(display_name, bio, location)
            
            # Create profile
            profile = Profile(
                profile_id=str(uuid.uuid4()),
                user_id=user_id,
                display_name=display_name,
                bio=bio,
                location=location,
                timezone=timezone or "UTC",
                preferred_units=preferred_units,
                experience_level=experience_level,
                profile_visibility=ProfileVisibility.PUBLIC,
                status=ProfileStatus.ACTIVE,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            
            # Save profile
            saved_profile = await self.profile_repository.create(profile)
            
            # Publish profile created event
            await self.event_publisher.publish(
                ProfileCreated(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    display_name=display_name,
                    experience_level=experience_level.value,
                    created_at=datetime.utcnow()
                )
            )
            
            logger.info("Profile created successfully", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return saved_profile
            
        except (ValidationError, ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Profile creation failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to create profile: {str(e)}")
    
    async def update_profile(self, 
                           user_id: str,
                           updates: Dict[str, Any]) -> Profile:
        """
        Update user profile for Plant Care Application.
        
        Args:
            user_id: User ID
            updates: Dictionary of fields to update
            
        Returns:
            Profile: Updated profile
            
        Raises:
            ValidationError: If update data is invalid
            ResourceNotFoundError: If profile not found
            AuthorizationError: If user cannot update profile
        """
        try:
            logger.info("Updating profile", user_id=user_id, updates=list(updates.keys()))
            
            # Get existing profile
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            # Validate user can update profile
            await self._validate_profile_update_permission(user_id, profile)
            
            # Validate update data
            await self._validate_profile_updates(updates)
            
            # Track what changed for events
            changes = {}
            
            # Apply updates
            if "display_name" in updates:
                old_name = profile.display_name
                profile.display_name = updates["display_name"]
                changes["display_name"] = {"old": old_name, "new": profile.display_name}
            
            if "bio" in updates:
                old_bio = profile.bio
                profile.bio = updates["bio"]
                changes["bio"] = {"old": old_bio, "new": profile.bio}
            
            if "location" in updates:
                old_location = profile.location
                profile.location = updates["location"]
                changes["location"] = {"old": old_location, "new": profile.location}
            
            if "timezone" in updates:
                old_timezone = profile.timezone
                profile.timezone = updates["timezone"]
                changes["timezone"] = {"old": old_timezone, "new": profile.timezone}
            
            if "preferred_units" in updates:
                old_units = profile.preferred_units
                profile.preferred_units = PreferredUnits(updates["preferred_units"])
                changes["preferred_units"] = {"old": old_units.value, "new": profile.preferred_units.value}
            
            if "experience_level" in updates:
                old_level = profile.experience_level
                profile.experience_level = ExperienceLevel(updates["experience_level"])
                changes["experience_level"] = {"old": old_level.value, "new": profile.experience_level.value}
            
            if "profile_visibility" in updates:
                old_visibility = profile.profile_visibility
                profile.profile_visibility = ProfileVisibility(updates["profile_visibility"])
                changes["profile_visibility"] = {"old": old_visibility.value, "new": profile.profile_visibility.value}
            
            if "plant_care_preferences" in updates:
                old_prefs = profile.plant_care_preferences
                profile.plant_care_preferences.update(updates["plant_care_preferences"])
                changes["plant_care_preferences"] = {"old": old_prefs, "new": profile.plant_care_preferences}
            
            if "notification_preferences" in updates:
                old_notif = profile.notification_preferences
                profile.notification_preferences.update(updates["notification_preferences"])
                changes["notification_preferences"] = {"old": old_notif, "new": profile.notification_preferences}
            
            # Update timestamp
            profile.updated_at = datetime.utcnow()
            
            # Save profile
            updated_profile = await self.profile_repository.update(profile)
            
            # Publish profile updated event
            await self.event_publisher.publish(
                ProfileUpdated(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    changes=changes,
                    updated_at=datetime.utcnow()
                )
            )
            
            logger.info("Profile updated successfully", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return updated_profile
            
        except (ValidationError, ResourceNotFoundError, AuthorizationError):
            raise
        except Exception as e:
            logger.error("Profile update failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to update profile: {str(e)}")
    
    async def update_avatar(self, 
                          user_id: str,
                          avatar_url: str,
                          file_size: int,
                          file_type: str) -> Profile:
        """
        Update user avatar for Plant Care Application.
        
        Args:
            user_id: User ID
            avatar_url: URL of uploaded avatar
            file_size: Size of avatar file in bytes
            file_type: MIME type of avatar file
            
        Returns:
            Profile: Updated profile with new avatar
            
        Raises:
            ValidationError: If avatar data is invalid
            ResourceNotFoundError: If profile not found
            FileError: If avatar file is invalid
        """
        try:
            logger.info("Updating avatar", user_id=user_id, avatar_url=avatar_url)
            
            # Get profile
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            # Validate avatar
            await self._validate_avatar(avatar_url, file_size, file_type)
            
            # Store old avatar for cleanup
            old_avatar_url = profile.avatar_url
            
            # Update avatar
            profile.avatar_url = avatar_url
            profile.updated_at = datetime.utcnow()
            
            # Save profile
            updated_profile = await self.profile_repository.update(profile)
            
            # Publish avatar updated event
            await self.event_publisher.publish(
                ProfileAvatarUpdated(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    old_avatar_url=old_avatar_url,
                    new_avatar_url=avatar_url,
                    updated_at=datetime.utcnow()
                )
            )
            
            logger.info("Avatar updated successfully", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return updated_profile
            
        except (ValidationError, ResourceNotFoundError, FileError):
            raise
        except Exception as e:
            logger.error("Avatar update failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to update avatar: {str(e)}")
    
    async def update_preferences(self, 
                               user_id: str,
                               plant_care_preferences: Optional[Dict[str, Any]] = None,
                               notification_preferences: Optional[Dict[str, Any]] = None) -> Profile:
        """
        Update user preferences for Plant Care Application.
        
        Args:
            user_id: User ID
            plant_care_preferences: Plant care preferences
            notification_preferences: Notification preferences
            
        Returns:
            Profile: Updated profile
            
        Raises:
            ValidationError: If preferences are invalid
            ResourceNotFoundError: If profile not found
        """
        try:
            logger.info("Updating preferences", user_id=user_id)
            
            # Get profile
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            # Validate preferences
            if plant_care_preferences:
                await self._validate_plant_care_preferences(plant_care_preferences)
            
            if notification_preferences:
                await self._validate_notification_preferences(notification_preferences)
            
            # Track changes
            changes = {}
            
            # Update plant care preferences
            if plant_care_preferences:
                old_prefs = profile.plant_care_preferences.copy()
                profile.plant_care_preferences.update(plant_care_preferences)
                changes["plant_care_preferences"] = {
                    "old": old_prefs,
                    "new": profile.plant_care_preferences
                }
            
            # Update notification preferences
            if notification_preferences:
                old_notif = profile.notification_preferences.copy()
                profile.notification_preferences.update(notification_preferences)
                changes["notification_preferences"] = {
                    "old": old_notif,
                    "new": profile.notification_preferences
                }
            
            # Update timestamp
            profile.updated_at = datetime.utcnow()
            
            # Save profile
            updated_profile = await self.profile_repository.update(profile)
            
            # Publish preferences updated event
            await self.event_publisher.publish(
                ProfilePreferencesUpdated(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    changes=changes,
                    updated_at=datetime.utcnow()
                )
            )
            
            logger.info("Preferences updated successfully", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return updated_profile
            
        except (ValidationError, ResourceNotFoundError):
            raise
        except Exception as e:
            logger.error("Preferences update failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to update preferences: {str(e)}")
    
    async def request_expert_verification(self, 
                                        user_id: str,
                                        credentials: Dict[str, Any],
                                        specialties: List[str],
                                        bio_update: str) -> Profile:
        """
        Request expert verification for Plant Care Application.
        
        Args:
            user_id: User ID
            credentials: Expert credentials and certifications
            specialties: List of plant care specialties
            bio_update: Updated bio with expert information
            
        Returns:
            Profile: Updated profile with verification request
            
        Raises:
            ValidationError: If verification data is invalid
            ResourceNotFoundError: If profile not found
            BusinessLogicError: If already verified or request pending
        """
        try:
            logger.info("Requesting expert verification", user_id=user_id)
            
            # Get profile and user
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")
            
            # Validate verification request
            await self._validate_expert_verification_request(profile, credentials, specialties, bio_update)
            
            # Update profile with verification request
            profile.bio = bio_update
            profile.expert_verification_status = "pending"
            profile.expert_credentials = credentials
            profile.expert_specialties = specialties[:self.max_specialties]  # Limit specialties
            profile.verification_requested_at = datetime.utcnow()
            profile.updated_at = datetime.utcnow()
            
            # Save profile
            updated_profile = await self.profile_repository.update(profile)
            
            # Publish verification requested event
            await self.event_publisher.publish(
                ExpertVerificationRequested(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    credentials=credentials,
                    specialties=specialties,
                    requested_at=datetime.utcnow()
                )
            )
            
            logger.info("Expert verification requested", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return updated_profile
            
        except (ValidationError, ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Expert verification request failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to request expert verification: {str(e)}")
    
    async def approve_expert_verification(self, 
                                        user_id: str,
                                        approved_by: str,
                                        verification_notes: Optional[str] = None) -> Tuple[Profile, User]:
        """
        Approve expert verification request.
        
        Args:
            user_id: User ID to approve
            approved_by: Admin user ID who approved
            verification_notes: Optional notes about verification
            
        Returns:
            Tuple[Profile, User]: Updated profile and user
            
        Raises:
            ResourceNotFoundError: If profile/user not found
            BusinessLogicError: If verification cannot be approved
            AuthorizationError: If approver lacks permission
        """
        try:
            logger.info("Approving expert verification", user_id=user_id, approved_by=approved_by)
            
            # Get profile and user
            profile = await self.profile_repository.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            user = await self.user_repository.find_by_id(user_id)
            if not user:
                raise ResourceNotFoundError(f"User not found: {user_id}")
            
            # Validate verification can be approved
            if profile.expert_verification_status != "pending":
                raise BusinessLogicError("No pending verification request found")
            
            # Update profile
            profile.expert_verification_status = "verified"
            profile.is_expert_verified = True
            profile.verification_approved_at = datetime.utcnow()
            profile.verification_approved_by = approved_by
            profile.verification_notes = verification_notes
            profile.updated_at = datetime.utcnow()
            
            # Update user role to expert
            user.role = UserRole.EXPERT
            user.updated_at = datetime.utcnow()
            
            # Save both
            updated_profile = await self.profile_repository.update(profile)
            updated_user = await self.user_repository.update(user)
            
            # Publish verification approved event
            await self.event_publisher.publish(
                ExpertVerificationApproved(
                    user_id=user_id,
                    profile_id=profile.profile_id,
                    approved_by=approved_by,
                    approved_at=datetime.utcnow(),
                    specialties=profile.expert_specialties,
                    notes=verification_notes
                )
            )
            
            logger.info("Expert verification approved", 
                       user_id=user_id, 
                       profile_id=profile.profile_id)
            
            return updated_profile, updated_user
            
        except (ResourceNotFoundError, BusinessLogicError, AuthorizationError):
            raise
        except Exception as e:
            logger.error("Expert verification approval failed", user_id=user_id, error=str(e))
            raise BusinessLogicError(f"Failed to approve expert verification: {str(e)}")
    
    async def follow_profile(self, follower_id: str, following_id: str) -> bool:
        """
        Follow another user's profile in Plant Care Application.
        
        Args:
            follower_id: User ID of follower
            following_id: User ID being followed
            
        Returns:
            bool: True if follow successful
            
        Raises:
            ValidationError: If follow data is invalid
            ResourceNotFoundError: If profiles not found
            BusinessLogicError: If cannot follow
        """
        try:
            logger.info("Following profile", follower_id=follower_id, following_id=following_id)
            
            # Validate different users
            if follower_id == following_id:
                raise ValidationError("Cannot follow yourself")
            
            # Get both profiles
            follower_profile = await self.profile_repository.find_by_user_id(follower_id)
            following_profile = await self.profile_repository.find_by_user_id(following_id)
            
            if not follower_profile:
                raise ResourceNotFoundError(f"Follower profile not found: {follower_id}")
            
            if not following_profile:
                raise ResourceNotFoundError(f"Following profile not found: {following_id}")
            
            # Check if already following
            is_following = await self.profile_repository.is_following(follower_id, following_id)
            if is_following:
                raise BusinessLogicError("Already following this user")
            
            # Check follow limits (premium feature)
            follower_user = await self.user_repository.find_by_id(follower_id)
            if not follower_user.has_premium_features():
                current_following = await self.profile_repository.get_following_count(follower_id)
                if current_following >= 50:  # Free tier limit
                    raise BusinessLogicError("Follow limit reached. Upgrade to premium for unlimited follows.")
            
            # Create follow relationship
            await self.profile_repository.create_follow(follower_id, following_id)
            
            # Update follower counts
            await self.profile_repository.increment_following_count(follower_id)
            await self.profile_repository.increment_followers_count(following_id)
            
            # Publish follow event
            await self.event_publisher.publish(
                ProfileFollowed(
                    follower_id=follower_id,
                    following_id=following_id,
                    followed_at=datetime.utcnow()
                )
            )
            
            logger.info("Profile followed successfully", 
                       follower_id=follower_id, 
                       following_id=following_id)
            
            return True
            
        except (ValidationError, ResourceNotFoundError, BusinessLogicError):
            raise
        except Exception as e:
            logger.error("Follow failed", follower_id=follower_id, following_id=following_id, error=str(e))
            raise BusinessLogicError(f"Failed to follow profile: {str(e)}")
    
    # Private helper methods
    
    async def _validate_profile_data(self, display_name: str, bio: Optional[str], location: Optional[str]) -> None:
        """Validate profile creation data."""
        if not PlantCareValidator.validate_display_name(display_name):
            raise ValidationError("Invalid display name")
        
        if bio and len(bio) > self.max_bio_length:
            raise ValidationError(f"Bio too long. Maximum {self.max_bio_length} characters.")
        
        if location and not PlantCareValidator.validate_location(location):
            raise ValidationError("Invalid location format")
    
    async def _validate_profile_updates(self, updates: Dict[str, Any]) -> None:
        """Validate profile update data."""
        if "display_name" in updates:
            if not PlantCareValidator.validate_display_name(updates["display_name"]):
                raise ValidationError("Invalid display name")
        
        if "bio" in updates:
            bio = updates["bio"]
            if bio and len(bio) > self.max_bio_length:
                raise ValidationError(f"Bio too long. Maximum {self.max_bio_length} characters.")
        
        if "location" in updates:
            location = updates["location"]
            if location and not PlantCareValidator.validate_location(location):
                raise ValidationError("Invalid location format")
    
    async def _validate_profile_update_permission(self, user_id: str, profile: Profile) -> None:
        """Validate user can update this profile."""
        if profile.user_id != user_id:
            raise AuthorizationError("Cannot update another user's profile")
        
        if profile.status != ProfileStatus.ACTIVE:
            raise BusinessLogicError("Cannot update inactive profile")
    
    async def _validate_avatar(self, avatar_url: str, file_size: int, file_type: str) -> None:
        """Validate avatar file."""
        # Check file size (5MB limit)
        max_size = 5 * 1024 * 1024  # 5MB
        if file_size > max_size:
            raise FileError(f"Avatar file too large. Maximum size: {max_size} bytes")
        
        # Check file type
        allowed_types = ["image/jpeg", "image/png", "image/gif", "image/webp"]
        if file_type not in allowed_types:
            raise FileError(f"Invalid avatar file type. Allowed: {', '.join(allowed_types)}")
        
        # Validate URL format
        if not PlantCareValidator.validate_url(avatar_url):
            raise ValidationError("Invalid avatar URL format")
    
    async def _validate_plant_care_preferences(self, preferences: Dict[str, Any]) -> None:
        """Validate plant care preferences."""
        # Validate watering reminder frequency
        if "watering_reminder_frequency" in preferences:
            frequency = preferences["watering_reminder_frequency"]
            if not isinstance(frequency, int) or frequency < 1 or frequency > 30:
                raise ValidationError("Watering reminder frequency must be between 1-30 days")
        
        # Validate care difficulty preference
        if "preferred_care_difficulty" in preferences:
            difficulty = preferences["preferred_care_difficulty"]
            valid_difficulties = ["easy", "moderate", "challenging", "expert"]
            if difficulty not in valid_difficulties:
                raise ValidationError(f"Invalid care difficulty. Valid options: {', '.join(valid_difficulties)}")
    
    async def _validate_notification_preferences(self, preferences: Dict[str, Any]) -> None:
        """Validate notification preferences."""
        # All notification preferences should be boolean
        for key, value in preferences.items():
            if not isinstance(value, bool):
                raise ValidationError(f"Notification preference '{key}' must be boolean")
    
    async def _validate_expert_verification_request(self, profile: Profile, credentials: Dict[str, Any], 
                                                  specialties: List[str], bio_update: str) -> None:
        """Validate expert verification request."""
        if profile.expert_verification_status == "verified":
            raise BusinessLogicError("User is already verified as an expert")
        
        if profile.expert_verification_status == "pending":
            raise BusinessLogicError("Expert verification request already pending")
        
        if len(bio_update) < 100:
            raise ValidationError("Expert bio must be at least 100 characters")
        
        if not specialties or len(specialties) == 0:
            raise ValidationError("At least one specialty is required")
        
        if len(specialties) > self.max_specialties:
            raise ValidationError(f"Maximum {self.max_specialties} specialties allowed")
        
        # Validate credentials structure
        required_fields = ["education", "experience_years", "certifications"]
        for field in required_fields:
            if field not in credentials:
                raise ValidationError(f"Missing required credential field: {field}")


# Convenience functions for dependency injection
def create_profile_service(user_repository: UserRepository,
                         profile_repository: ProfileRepository, 
                         event_publisher: EventPublisher) -> ProfileService:
    """Create profile service instance."""
    return ProfileService(user_repository, profile_repository, event_publisher)