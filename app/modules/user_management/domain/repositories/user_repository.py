# app/modules/user_management/domain/repositories/user_repository.py
"""
Plant Care Application - User Repository Interface

Repository interface for User entity persistence and retrieval.
Defines the contract for user data access without coupling to specific implementations.
"""

from abc import ABC, abstractmethod
from typing import Optional, List, Dict, Any
from datetime import datetime

from app.modules.user_management.domain.models.user import User, UserRole, UserStatus
from app.modules.user_management.domain.models.subscription import Subscription


class UserRepository(ABC):
    """
    Repository interface for User entity.
    Defines all operations for user persistence and retrieval.
    """
    
    @abstractmethod
    async def save(self, user: User) -> User:
        """
        Save or update user.
        
        Args:
            user: User entity to save
            
        Returns:
            User: Saved user entity
            
        Raises:
            RepositoryError: If save operation fails
        """
        pass
    
    @abstractmethod
    async def find_by_id(self, user_id: str) -> Optional[User]:
        """
        Find user by ID.
        
        Args:
            user_id: User ID to search for
            
        Returns:
            Optional[User]: User entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_email(self, email: str) -> Optional[User]:
        """
        Find user by email address.
        
        Args:
            email: Email address to search for
            
        Returns:
            Optional[User]: User entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_supabase_id(self, supabase_user_id: str) -> Optional[User]:
        """
        Find user by Supabase user ID.
        
        Args:
            supabase_user_id: Supabase user ID to search for
            
        Returns:
            Optional[User]: User entity if found, None otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def exists_by_email(self, email: str) -> bool:
        """
        Check if user exists by email.
        
        Args:
            email: Email address to check
            
        Returns:
            bool: True if user exists, False otherwise
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_role(self, role: UserRole, limit: Optional[int] = None, 
                          offset: Optional[int] = None) -> List[User]:
        """
        Find users by role.
        
        Args:
            role: User role to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the specified role
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_by_status(self, status: UserStatus, limit: Optional[int] = None,
                           offset: Optional[int] = None) -> List[User]:
        """
        Find users by status.
        
        Args:
            status: User status to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the specified status
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_premium_users(self, limit: Optional[int] = None,
                                offset: Optional[int] = None) -> List[User]:
        """
        Find premium users.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of premium users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_experts(self, limit: Optional[int] = None,
                          offset: Optional[int] = None) -> List[User]:
        """
        Find expert users.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of expert users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_users_needing_verification(self, limit: Optional[int] = None,
                                            offset: Optional[int] = None) -> List[User]:
        """
        Find users that need email verification.
        
        Args:
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users needing verification
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_inactive_users(self, inactive_since: datetime,
                                 limit: Optional[int] = None,
                                 offset: Optional[int] = None) -> List[User]:
        """
        Find users inactive since a specific date.
        
        Args:
            inactive_since: Date to check for inactivity
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of inactive users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_by_status(self, status: UserStatus) -> int:
        """
        Count users by status.
        
        Args:
            status: User status to count
            
        Returns:
            int: Number of users with the specified status
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_premium_users(self) -> int:
        """
        Count premium users.
        
        Returns:
            int: Number of premium users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def count_by_registration_date(self, start_date: datetime,
                                       end_date: datetime) -> int:
        """
        Count users registered within date range.
        
        Args:
            start_date: Start of date range
            end_date: End of date range
            
        Returns:
            int: Number of users registered in the date range
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def search_users(self, query: str, limit: Optional[int] = None,
                          offset: Optional[int] = None) -> List[User]:
        """
        Search users by email or metadata.
        
        Args:
            query: Search query string
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of matching users
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def bulk_update_plant_count(self, user_plant_counts: Dict[str, int]) -> int:
        """
        Bulk update plant counts for multiple users.
        
        Args:
            user_plant_counts: Dictionary mapping user_id to plant count
            
        Returns:
            int: Number of users updated
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def delete(self, user_id: str) -> bool:
        """
        Delete user by ID (hard delete).
        
        Args:
            user_id: ID of user to delete
            
        Returns:
            bool: True if user was deleted, False if not found
            
        Raises:
            RepositoryError: If delete operation fails
        """
        pass
    
    @abstractmethod
    async def soft_delete(self, user_id: str) -> bool:
        """
        Soft delete user by setting status to deleted.
        
        Args:
            user_id: ID of user to soft delete
            
        Returns:
            bool: True if user was soft deleted, False if not found
            
        Raises:
            RepositoryError: If update operation fails
        """
        pass
    
    @abstractmethod
    async def get_user_statistics(self) -> Dict[str, Any]:
        """
        Get user statistics for analytics.
        
        Returns:
            Dict[str, Any]: Dictionary containing user statistics
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def find_users_with_subscription(self, subscription_tier: str,
                                         limit: Optional[int] = None,
                                         offset: Optional[int] = None) -> List[User]:
        """
        Find users with specific subscription tier.
        
        Args:
            subscription_tier: Subscription tier to search for
            limit: Maximum number of results
            offset: Number of results to skip
            
        Returns:
            List[User]: List of users with the subscription tier
            
        Raises:
            RepositoryError: If query fails
        """
        pass
    
    @abstractmethod
    async def update_last_login(self, user_id: str, login_time: datetime) -> bool:
        """
        Update user's last login time.
        
        Args:
            user_id: ID of user to update
            login_time: Login timestamp
            
        Returns:
            bool: True if updated successfully, False if user not found
            
        Raises:
            RepositoryError: If update fails
        """
        pass
    
    @abstractmethod
    async def batch_save(self, users: List[User]) -> List[User]:
        """
        Save multiple users in a batch operation.
        
        Args:
            users: List of users to save
            
        Returns:
            List[User]: List of saved users
            
        Raises:
            RepositoryError: If batch save fails
        """
        pass