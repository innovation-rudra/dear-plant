# app/modules/user_management/domain/repositories/profile_repository.py
"""
Plant Care Application - Profile Repository Interface

Repository interface for Profile entity persistence and retrieval.
Defines the contract for profile data access without coupling to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.modules.user_management.domain.models.profile import Profile, PrivacyLevel


class ProfileRepository(ABC):
    """
    Repository interface for Profile entity.
    Defines all operations for profile persistence and retrieval.
    """
    
    @abstractmethod
    async def save(self, profile: Profile) -> Profile:
        """
        Save or update profile.
        
        Args:
            profile: Profile entity to save
            
        Returns:
            Profile: Saved profile entity
            
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, profile_id: str) -> Optional[Profile]:
        """
        Find profile by ID.
        
        Args:
            profile_id: Profile ID to search for
            
        Returns:
            Optional[Profile]: Profile entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_user_id(self, user_id: str) -> Optional[Profile]:
        """
        Find profile by user ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Optional[Profile]: Profile entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def exists_by_user_id(self, user_id: str) -> bool:
        """
        Check if profile exists for user.
        
        Args:
            user_id: User ID to check
            
        Returns:
            bool: True if profile exists, False otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_display_name(self, display_name: str) -> Optional[Profile]:
        """
        Find profile by display name.
        
        Args:
            display_name: Display name to search for
            
        Returns:
            Optional[Profile]: Profile entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_verified_experts(self, limit: Optional[int] = None,
                                  offset: Optional[int] = None) -> List[Profile]:
        """
        Find verified expert profiles.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of verified expert profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_experience_level(self, experience_level: str,
                                     limit: Optional[int] = None,
                                     offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles by experience level.
        
        Args:
            experience_level: Experience level to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles with the experience level
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_location(self, location: str, radius_km: Optional[float] = None,
                              limit: Optional[int] = None,
                              offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles by location.
        
        Args:
            location: Location string to search near
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles in the location
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_coordinates(self, latitude: float, longitude: float,
                                 radius_km: float, limit: Optional[int] = None,
                                 offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles by geographic coordinates.
        
        Args:
            latitude: Latitude coordinate
            longitude: Longitude coordinate
            radius_km: Search radius in kilometers
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles within the radius
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_plant_interests(self, plant_types: List[str],
                                    limit: Optional[int] = None,
                                    offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles interested in specific plant types.
        
        Args:
            plant_types: List of plant types to match
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles with matching plant interests
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_experts_by_specialty(self, specialty: str,
                                      limit: Optional[int] = None,
                                      offset: Optional[int] = None) -> List[Profile]:
        """
        Find expert profiles by specialty.
        
        Args:
            specialty: Plant care specialty to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of expert profiles with the specialty
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_available_experts(self, limit: Optional[int] = None,
                                   offset: Optional[int] = None) -> List[Profile]:
        """
        Find experts available for consultation.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of available expert profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_public_profiles(self, limit: Optional[int] = None,
                                 offset: Optional[int] = None) -> List[Profile]:
        """
        Find public profiles.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of public profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def search_profiles(self, query: str, limit: Optional[int] = None,
                            offset: Optional[int] = None) -> List[Profile]:
        """
        Search profiles by display name, bio, or interests.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of matching profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_by_experience_level(self, experience_level: str) -> int:
        """
        Count profiles by experience level.
        
        Args:
            experience_level: Experience level to count
            
        Returns:
            int: Number of profiles with the experience level
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_verified_experts(self) -> int:
        """
        Count verified expert profiles.
        
        Returns:
            int: Number of verified expert profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_popular_plant_types(self, limit: int = 10) -> List[Dict[str, Any]]:
        """
        Get most popular plant types from user preferences.
        
        Args:
            limit: Maximum number of plant types to return
            
        Returns:
            List[Dict[str, Any]]: List of plant types with counts
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def get_location_distribution(self) -> List[Dict[str, Any]]:
        """
        Get distribution of users by location.
        
        Returns:
            List[Dict[str, Any]]: List of locations with user counts
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update_social_counts(self, profile_id: str, followers: int,
                                 following: int) -> bool:
        """
        Update follower and following counts.
        
        Args:
            profile_id: Profile ID to update
            followers: New follower count
            following: New following count
            
        Returns:
            bool: True if updated successfully, False if profile not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def update_expert_rating(self, profile_id: str, new_rating: float) -> bool:
        """
        Update expert rating.
        
        Args:
            profile_id: Profile ID to update
            new_rating: New expert rating
            
        Returns:
            bool: True if updated successfully, False if profile not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def bulk_update_locations(self, location_updates: Dict[str, Dict[str, Any]]) -> int:
        """
        Bulk update profile locations.
        
        Args:
            location_updates: Dictionary mapping profile_id to location data
            
        Returns:
            int: Number of profiles updated
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, profile_id: str) -> bool:
        """
        Delete profile by ID.
        
        Args:
            profile_id: ID of profile to delete
            
        Returns:
            bool: True if profile was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def delete_by_user_id(self, user_id: str) -> bool:
        """
        Delete profile by user ID.
        
        Args:
            user_id: User ID whose profile to delete
            
        Returns:
            bool: True if profile was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def get_profile_statistics(self) -> Dict[str, Any]:
        """
        Get profile statistics for analytics.
        
        Returns:
            Dict[str, Any]: Dictionary containing profile statistics
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_profiles_needing_avatar(self, limit: Optional[int] = None,
                                         offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles that don't have an avatar set.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles without avatars
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_incomplete_profiles(self, limit: Optional[int] = None,
                                     offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles that are incomplete (missing key information).
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of incomplete profiles
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def batch_save(self, profiles: List[Profile]) -> List[Profile]:
        """
        Save multiple profiles in a batch operation.
        
        Args:
            profiles: List of profiles to save
            
        Returns:
            List[Profile]: List of saved profiles
            
        Raises:
            RepositoryError: If batch save fails
        """
        pass
    
    @abstractmethod
    async def find_by_privacy_level(self, privacy_level: PrivacyLevel,
                                   limit: Optional[int] = None,
                                   offset: Optional[int] = None) -> List[Profile]:
        """
        Find profiles by privacy level.
        
        Args:
            privacy_level: Privacy level to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[Profile]: List of profiles with the privacy level
            
        Raises:
            RepositoryError: If query fails
        """
        pass