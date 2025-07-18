# app/modules/user_management/infrastructure/database/profile_repository_impl.py
"""
Plant Care Application - PostgreSQL Profile Repository Implementation

Concrete implementation of ProfileRepository interface using SQLAlchemy and PostgreSQL.
Handles all profile data persistence operations for the Plant Care Application.
"""

from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
from sqlalchemy.orm import Session, selectinload
from sqlalchemy import and_, or_, func, desc, asc
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

import structlog

from app.modules.user_management.domain.models.profile import (
    Profile, ProfileStatus, ExperienceLevel, PreferredUnits, ProfileVisibility
)
from app.modules.user_management.domain.repositories.profile_repository import ProfileRepository
from app.modules.user_management.infrastructure.database.models import (
    ProfileModel, UserModel, FollowModel
)
from app.shared.core.exceptions import (
    DatabaseError, ResourceNotFoundError, ValidationError, BusinessLogicError
)
from app.shared.infrastructure.database.connection import get_database_session

# Setup logger
logger = structlog.get_logger(__name__)


class PostgreSQLProfileRepository(ProfileRepository):
    """
    PostgreSQL implementation of ProfileRepository for Plant Care Application.
    Provides CRUD operations and complex queries for profile management.
    """
    
    def __init__(self, session: Optional[Session] = None):
        """
        Initialize repository with database session.
        
        Args:
            session: SQLAlchemy session (optional, will create if not provided)
        """
        self._session = session
    
    async def _get_session(self) -> Session:
        """Get database session."""
        if self._session:
            return self._session
        return await get_database_session()
    
    async def create(self, profile: Profile) -> Profile:
        """
        Create a new profile in the database.
        
        Args:
            profile: Profile domain model to create
            
        Returns:
            Profile: Created profile with updated database information
            
        Raises:
            DatabaseError: If profile creation fails
            ValidationError: If profile data is invalid
        """
        try:
            session = await self._get_session()
            
            logger.info("Creating profile in database", 
                       profile_id=profile.profile_id, 
                       user_id=profile.user_id)
            
            # Convert domain model to database model
            profile_model = ProfileModel(
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
                verification_requested_at=profile.verification_requested_at,
                verification_approved_at=profile.verification_approved_at,
                verification_approved_by=profile.verification_approved_by,
                verification_notes=profile.verification_notes,
                expert_rating=profile.expert_rating,
                expert_reviews_count=profile.expert_reviews_count,
                followers_count=profile.followers_count,
                following_count=profile.following_count,
                plant_care_preferences=profile.plant_care_preferences,
                notification_preferences=profile.notification_preferences,
                created_at=profile.created_at,
                updated_at=profile.updated_at
            )
            
            session.add(profile_model)
            await session.commit()
            await session.refresh(profile_model)
            
            # Convert back to domain model
            created_profile = await self._model_to_domain(profile_model)
            
            logger.info("Profile created successfully", profile_id=created_profile.profile_id)
            
            return created_profile
            
        except IntegrityError as e:
            await session.rollback()
            logger.error("Profile creation failed - integrity error", 
                        profile_id=profile.profile_id, error=str(e))
            if "user_id" in str(e):
                raise ValidationError("Profile already exists for this user")
            else:
                raise DatabaseError(f"Profile creation failed: {str(e)}")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Profile creation failed - database error", 
                        profile_id=profile.profile_id, error=str(e))
            raise DatabaseError(f"Failed to create profile: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error("Profile creation failed - unexpected error", 
                        profile_id=profile.profile_id, error=str(e))
            raise DatabaseError(f"Unexpected error creating profile: {str(e)}")
    
    async def update(self, profile: Profile) -> Profile:
        """
        Update an existing profile in the database.
        
        Args:
            profile: Profile domain model with updates
            
        Returns:
            Profile: Updated profile
            
        Raises:
            ResourceNotFoundError: If profile not found
            DatabaseError: If update fails
        """
        try:
            session = await self._get_session()
            
            logger.info("Updating profile in database", profile_id=profile.profile_id)
            
            # Find existing profile
            profile_model = await session.get(ProfileModel, profile.profile_id)
            if not profile_model:
                raise ResourceNotFoundError(f"Profile not found: {profile.profile_id}")
            
            # Update fields
            profile_model.display_name = profile.display_name
            profile_model.bio = profile.bio
            profile_model.avatar_url = profile.avatar_url
            profile_model.location = profile.location
            profile_model.timezone = profile.timezone
            profile_model.experience_level = profile.experience_level.value
            profile_model.preferred_units = profile.preferred_units.value
            profile_model.profile_visibility = profile.profile_visibility.value
            profile_model.status = profile.status.value
            profile_model.is_expert_verified = profile.is_expert_verified
            profile_model.expert_verification_status = profile.expert_verification_status
            profile_model.expert_credentials = profile.expert_credentials
            profile_model.expert_specialties = profile.expert_specialties
            profile_model.verification_requested_at = profile.verification_requested_at
            profile_model.verification_approved_at = profile.verification_approved_at
            profile_model.verification_approved_by = profile.verification_approved_by
            profile_model.verification_notes = profile.verification_notes
            profile_model.expert_rating = profile.expert_rating
            profile_model.expert_reviews_count = profile.expert_reviews_count
            profile_model.followers_count = profile.followers_count
            profile_model.following_count = profile.following_count
            profile_model.plant_care_preferences = profile.plant_care_preferences
            profile_model.notification_preferences = profile.notification_preferences
            profile_model.updated_at = profile.updated_at
            
            await session.commit()
            await session.refresh(profile_model)
            
            # Convert back to domain model
            updated_profile = await self._model_to_domain(profile_model)
            
            logger.info("Profile updated successfully", profile_id=updated_profile.profile_id)
            
            return updated_profile
            
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Profile update failed - database error", 
                        profile_id=profile.profile_id, error=str(e))
            raise DatabaseError(f"Failed to update profile: {str(e)}")
        except Exception as e:
            await session.rollback()
            logger.error("Profile update failed - unexpected error", 
                        profile_id=profile.profile_id, error=str(e))
            raise DatabaseError(f"Unexpected error updating profile: {str(e)}")
    
    async def find_by_id(self, profile_id: str) -> Optional[Profile]:
        """
        Find profile by ID.
        
        Args:
            profile_id: Profile ID to search for
            
        Returns:
            Optional[Profile]: Profile if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            profile_model = await session.get(ProfileModel, profile_id)
            
            if not profile_model:
                return None
            
            return await self._model_to_domain(profile_model)
            
        except SQLAlchemyError as e:
            logger.error("Find profile by ID failed", profile_id=profile_id, error=str(e))
            raise DatabaseError(f"Failed to find profile: {str(e)}")
    
    async def find_by_user_id(self, user_id: str) -> Optional[Profile]:
        """
        Find profile by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Optional[Profile]: Profile if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            profile_model = await session.query(ProfileModel).filter(
                ProfileModel.user_id == user_id
            ).first()
            
            if not profile_model:
                return None
            
            return await self._model_to_domain(profile_model)
            
        except SQLAlchemyError as e:
            logger.error("Find profile by user ID failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to find profile by user ID: {str(e)}")
    
    async def find_by_display_name(self, display_name: str) -> Optional[Profile]:
        """
        Find profile by display name.
        
        Args:
            display_name: Display name to search for
            
        Returns:
            Optional[Profile]: Profile if found, None otherwise
        """
        try:
            session = await self._get_session()
            
            profile_model = await session.query(ProfileModel).filter(
                ProfileModel.display_name == display_name
            ).first()
            
            if not profile_model:
                return None
            
            return await self._model_to_domain(profile_model)
            
        except SQLAlchemyError as e:
            logger.error("Find profile by display name failed", 
                        display_name=display_name, error=str(e))
            raise DatabaseError(f"Failed to find profile by display name: {str(e)}")
    
    async def find_by_experience_level(self, level: ExperienceLevel, 
                                     limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Find profiles by experience level.
        
        Args:
            level: Experience level to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles with the specified experience level
        """
        try:
            session = await self._get_session()
            
            profile_models = await session.query(ProfileModel).filter(
                and_(
                    ProfileModel.experience_level == level.value,
                    ProfileModel.status == ProfileStatus.ACTIVE.value
                )
            ).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Find profiles by experience level failed", 
                        level=level.value, error=str(e))
            raise DatabaseError(f"Failed to find profiles by experience level: {str(e)}")
    
    async def find_by_location(self, location: str, limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Find profiles by location.
        
        Args:
            location: Location to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles in the specified location
        """
        try:
            session = await self._get_session()
            
            location_pattern = f"%{location}%"
            
            profile_models = await session.query(ProfileModel).filter(
                and_(
                    ProfileModel.location.ilike(location_pattern),
                    ProfileModel.status == ProfileStatus.ACTIVE.value,
                    ProfileModel.profile_visibility.in_([
                        ProfileVisibility.PUBLIC.value,
                        ProfileVisibility.FOLLOWERS_ONLY.value
                    ])
                )
            ).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Find profiles by location failed", location=location, error=str(e))
            raise DatabaseError(f"Failed to find profiles by location: {str(e)}")
    
    async def find_verified_experts(self, specialty: Optional[str] = None, 
                                   limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Find verified expert profiles.
        
        Args:
            specialty: Optional specialty to filter by
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of verified expert profiles
        """
        try:
            session = await self._get_session()
            
            query = session.query(ProfileModel).filter(
                and_(
                    ProfileModel.is_expert_verified == True,
                    ProfileModel.expert_verification_status == "verified",
                    ProfileModel.status == ProfileStatus.ACTIVE.value,
                    ProfileModel.profile_visibility.in_([
                        ProfileVisibility.PUBLIC.value,
                        ProfileVisibility.FOLLOWERS_ONLY.value
                    ])
                )
            )
            
            # Filter by specialty if provided
            if specialty:
                query = query.filter(
                    ProfileModel.expert_specialties.contains([specialty])
                )
            
            # Order by expert rating (highest first)
            query = query.order_by(desc(ProfileModel.expert_rating))
            
            profile_models = await query.offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Find verified experts failed", specialty=specialty, error=str(e))
            raise DatabaseError(f"Failed to find verified experts: {str(e)}")
    
    async def find_pending_verifications(self, limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Find profiles with pending expert verification.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles pending verification
        """
        try:
            session = await self._get_session()
            
            profile_models = await session.query(ProfileModel).filter(
                ProfileModel.expert_verification_status == "pending"
            ).order_by(asc(ProfileModel.verification_requested_at)).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Find pending verifications failed", error=str(e))
            raise DatabaseError(f"Failed to find pending verifications: {str(e)}")
    
    async def search_profiles(self, query: str, limit: int = 50, offset: int = 0) -> List[Profile]:
        """
        Search profiles by display name, bio, or location.
        
        Args:
            query: Search query
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of matching profiles
        """
        try:
            session = await self._get_session()
            
            search_term = f"%{query}%"
            
            profile_models = await session.query(ProfileModel).filter(
                and_(
                    or_(
                        ProfileModel.display_name.ilike(search_term),
                        ProfileModel.bio.ilike(search_term),
                        ProfileModel.location.ilike(search_term)
                    ),
                    ProfileModel.status == ProfileStatus.ACTIVE.value,
                    ProfileModel.profile_visibility == ProfileVisibility.PUBLIC.value
                )
            ).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Search profiles failed", query=query, error=str(e))
            raise DatabaseError(f"Failed to search profiles: {str(e)}")
    
    async def get_followers(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Get followers of a user.
        
        Args:
            user_id: User ID to get followers for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of follower profiles
        """
        try:
            session = await self._get_session()
            
            profile_models = await session.query(ProfileModel).join(
                FollowModel, ProfileModel.user_id == FollowModel.follower_id
            ).filter(
                FollowModel.following_id == user_id
            ).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Get followers failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get followers: {str(e)}")
    
    async def get_following(self, user_id: str, limit: int = 100, offset: int = 0) -> List[Profile]:
        """
        Get users that a user is following.
        
        Args:
            user_id: User ID to get following for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles being followed
        """
        try:
            session = await self._get_session()
            
            profile_models = await session.query(ProfileModel).join(
                FollowModel, ProfileModel.user_id == FollowModel.following_id
            ).filter(
                FollowModel.follower_id == user_id
            ).offset(offset).limit(limit).all()
            
            profiles = []
            for profile_model in profile_models:
                profile = await self._model_to_domain(profile_model)
                profiles.append(profile)
            
            return profiles
            
        except SQLAlchemyError as e:
            logger.error("Get following failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get following: {str(e)}")
    
    async def is_following(self, follower_id: str, following_id: str) -> bool:
        """
        Check if one user is following another.
        
        Args:
            follower_id: ID of potential follower
            following_id: ID of user potentially being followed
            
        Returns:
            bool: True if following relationship exists
        """
        try:
            session = await self._get_session()
            
            follow = await session.query(FollowModel).filter(
                and_(
                    FollowModel.follower_id == follower_id,
                    FollowModel.following_id == following_id
                )
            ).first()
            
            return follow is not None
            
        except SQLAlchemyError as e:
            logger.error("Check following failed", 
                        follower_id=follower_id, following_id=following_id, error=str(e))
            raise DatabaseError(f"Failed to check following relationship: {str(e)}")
    
    async def create_follow(self, follower_id: str, following_id: str) -> bool:
        """
        Create a follow relationship.
        
        Args:
            follower_id: ID of follower
            following_id: ID of user being followed
            
        Returns:
            bool: True if relationship created successfully
            
        Raises:
            DatabaseError: If creation fails
            ValidationError: If relationship already exists
        """
        try:
            session = await self._get_session()
            
            # Check if relationship already exists
            existing = await self.is_following(follower_id, following_id)
            if existing:
                raise ValidationError("Follow relationship already exists")
            
            # Create follow relationship
            follow = FollowModel(
                follower_id=follower_id,
                following_id=following_id,
                followed_at=datetime.utcnow()
            )
            
            session.add(follow)
            await session.commit()
            
            return True
            
        except ValidationError:
            raise
        except IntegrityError as e:
            await session.rollback()
            logger.error("Create follow failed - integrity error", 
                        follower_id=follower_id, following_id=following_id, error=str(e))
            raise ValidationError("Invalid follow relationship")
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Create follow failed", 
                        follower_id=follower_id, following_id=following_id, error=str(e))
            raise DatabaseError(f"Failed to create follow relationship: {str(e)}")
    
    async def remove_follow(self, follower_id: str, following_id: str) -> bool:
        """
        Remove a follow relationship.
        
        Args:
            follower_id: ID of follower
            following_id: ID of user being followed
            
        Returns:
            bool: True if relationship removed successfully
        """
        try:
            session = await self._get_session()
            
            follow = await session.query(FollowModel).filter(
                and_(
                    FollowModel.follower_id == follower_id,
                    FollowModel.following_id == following_id
                )
            ).first()
            
            if not follow:
                return False
            
            await session.delete(follow)
            await session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Remove follow failed", 
                        follower_id=follower_id, following_id=following_id, error=str(e))
            raise DatabaseError(f"Failed to remove follow relationship: {str(e)}")
    
    async def get_followers_count(self, user_id: str) -> int:
        """
        Get count of followers for a user.
        
        Args:
            user_id: User ID to count followers for
            
        Returns:
            int: Number of followers
        """
        try:
            session = await self._get_session()
            
            count = await session.query(func.count(FollowModel.follower_id)).filter(
                FollowModel.following_id == user_id
            ).scalar()
            
            return count or 0
            
        except SQLAlchemyError as e:
            logger.error("Get followers count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get followers count: {str(e)}")
    
    async def get_following_count(self, user_id: str) -> int:
        """
        Get count of users that a user is following.
        
        Args:
            user_id: User ID to count following for
            
        Returns:
            int: Number of users being followed
        """
        try:
            session = await self._get_session()
            
            count = await session.query(func.count(FollowModel.following_id)).filter(
                FollowModel.follower_id == user_id
            ).scalar()
            
            return count or 0
            
        except SQLAlchemyError as e:
            logger.error("Get following count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get following count: {str(e)}")
    
    async def increment_followers_count(self, user_id: str) -> None:
        """
        Increment followers count for a user.
        
        Args:
            user_id: User ID to increment count for
        """
        try:
            session = await self._get_session()
            
            await session.query(ProfileModel).filter(
                ProfileModel.user_id == user_id
            ).update({
                ProfileModel.followers_count: ProfileModel.followers_count + 1
            })
            
            await session.commit()
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Increment followers count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to increment followers count: {str(e)}")
    
    async def decrement_followers_count(self, user_id: str) -> None:
        """
        Decrement followers count for a user.
        
        Args:
            user_id: User ID to decrement count for
        """
        try:
            session = await self._get_session()
            
            await session.query(ProfileModel).filter(
                and_(
                    ProfileModel.user_id == user_id,
                    ProfileModel.followers_count > 0
                )
            ).update({
                ProfileModel.followers_count: ProfileModel.followers_count - 1
            })
            
            await session.commit()
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Decrement followers count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to decrement followers count: {str(e)}")
    
    async def increment_following_count(self, user_id: str) -> None:
        """
        Increment following count for a user.
        
        Args:
            user_id: User ID to increment count for
        """
        try:
            session = await self._get_session()
            
            await session.query(ProfileModel).filter(
                ProfileModel.user_id == user_id
            ).update({
                ProfileModel.following_count: ProfileModel.following_count + 1
            })
            
            await session.commit()
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Increment following count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to increment following count: {str(e)}")
    
    async def decrement_following_count(self, user_id: str) -> None:
        """
        Decrement following count for a user.
        
        Args:
            user_id: User ID to decrement count for
        """
        try:
            session = await self._get_session()
            
            await session.query(ProfileModel).filter(
                and_(
                    ProfileModel.user_id == user_id,
                    ProfileModel.following_count > 0
                )
            ).update({
                ProfileModel.following_count: ProfileModel.following_count - 1
            })
            
            await session.commit()
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Decrement following count failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to decrement following count: {str(e)}")
    
    async def get_profile_analytics(self, user_id: str) -> Dict[str, Any]:
        """
        Get analytics data for a profile.
        
        Args:
            user_id: User ID to get analytics for
            
        Returns:
            Dict[str, Any]: Profile analytics data
        """
        try:
            session = await self._get_session()
            
            # Get profile
            profile = await self.find_by_user_id(user_id)
            if not profile:
                raise ResourceNotFoundError(f"Profile not found for user: {user_id}")
            
            # Get follower/following counts
            followers_count = await self.get_followers_count(user_id)
            following_count = await self.get_following_count(user_id)
            
            # Get recent followers (last 30 days)
            thirty_days_ago = datetime.utcnow() - timedelta(days=30)
            recent_followers = await session.query(func.count(FollowModel.follower_id)).filter(
                and_(
                    FollowModel.following_id == user_id,
                    FollowModel.followed_at >= thirty_days_ago
                )
            ).scalar()
            
            analytics = {
                "profile_id": profile.profile_id,
                "user_id": user_id,
                "display_name": profile.display_name,
                "experience_level": profile.experience_level.value,
                "is_expert_verified": profile.is_expert_verified,
                "social_stats": {
                    "followers_count": followers_count,
                    "following_count": following_count,
                    "recent_followers_30d": recent_followers or 0
                },
                "expert_stats": {
                    "is_verified": profile.is_expert_verified,
                    "rating": float(profile.expert_rating) if profile.expert_rating else None,
                    "reviews_count": profile.expert_reviews_count,
                    "specialties": profile.expert_specialties or []
                },
                "profile_completion": self._calculate_profile_completion(profile),
                "generated_at": datetime.utcnow().isoformat()
            }
            
            return analytics
            
        except ResourceNotFoundError:
            raise
        except SQLAlchemyError as e:
            logger.error("Get profile analytics failed", user_id=user_id, error=str(e))
            raise DatabaseError(f"Failed to get profile analytics: {str(e)}")
    
    async def delete(self, profile_id: str) -> bool:
        """
        Delete a profile from the database.
        
        Args:
            profile_id: Profile ID to delete
            
        Returns:
            bool: True if profile was deleted, False if not found
        """
        try:
            session = await self._get_session()
            
            profile_model = await session.get(ProfileModel, profile_id)
            if not profile_model:
                return False
            
            await session.delete(profile_model)
            await session.commit()
            
            return True
            
        except SQLAlchemyError as e:
            await session.rollback()
            logger.error("Profile deletion failed", profile_id=profile_id, error=str(e))
            raise DatabaseError(f"Failed to delete profile: {str(e)}")
    
    # Private helper methods
    
    async def _model_to_domain(self, profile_model: ProfileModel) -> Profile:
        """Convert database model to domain model."""
        return Profile(
            profile_id=profile_model.profile_id,
            user_id=profile_model.user_id,
            display_name=profile_model.display_name,
            bio=profile_model.bio,
            avatar_url=profile_model.avatar_url,
            location=profile_model.location,
            timezone=profile_model.timezone,
            experience_level=ExperienceLevel(profile_model.experience_level),
            preferred_units=PreferredUnits(profile_model.preferred_units),
            profile_visibility=ProfileVisibility(profile_model.profile_visibility),
            status=ProfileStatus(profile_model.status),
            is_expert_verified=profile_model.is_expert_verified,
            expert_verification_status=profile_model.expert_verification_status,
            expert_credentials=profile_model.expert_credentials,
            expert_specialties=profile_model.expert_specialties,
            verification_requested_at=profile_model.verification_requested_at,
            verification_approved_at=profile_model.verification_approved_at,
            verification_approved_by=profile_model.verification_approved_by,
            verification_notes=profile_model.verification_notes,
            expert_rating=profile_model.expert_rating,
            expert_reviews_count=profile_model.expert_reviews_count,
            followers_count=profile_model.followers_count,
            following_count=profile_model.following_count,
            plant_care_preferences=profile_model.plant_care_preferences or {},
            notification_preferences=profile_model.notification_preferences or {},
            created_at=profile_model.created_at,
            updated_at=profile_model.updated_at
        )
    
    def _calculate_profile_completion(self, profile: Profile) -> Dict[str, Any]:
        """Calculate profile completion percentage."""
        total_fields = 10
        completed_fields = 0
        
        # Required fields
        if profile.display_name:
            completed_fields += 1
        
        # Optional but important fields
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
        if profile.experience_level != ExperienceLevel.BEGINNER:
            completed_fields += 1
        if profile.preferred_units:
            completed_fields += 1
        if profile.timezone != "UTC":
            completed_fields += 1
        if profile.profile_visibility:
            completed_fields += 1
        
        completion_percentage = (completed_fields / total_fields) * 100
        
        return {
            "percentage": round(completion_percentage, 1),
            "completed_fields": completed_fields,
            "total_fields": total_fields,
            "missing_fields": [
                field for field, value in [
                    ("bio", profile.bio),
                    ("avatar", profile.avatar_url),
                    ("location", profile.location),
                    ("plant_care_preferences", profile.plant_care_preferences),
                    ("notification_preferences", profile.notification_preferences)
                ] if not value
            ]
        }


# Factory function for dependency injection
def create_postgresql_profile_repository(session: Optional[Session] = None) -> PostgreSQLProfileRepository:
    """Create PostgreSQL profile repository instance."""
    return PostgreSQLProfileRepository(session)