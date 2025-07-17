"""
Plant Care Application - Supabase Client Configuration
"""
from functools import lru_cache
from typing import Optional

from supabase import Client, create_client
from gotrue import SyncGoTrueClient
from storage3 import SyncStorageClient
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import ConfigurationError

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class SupabaseManager:
    """
    Supabase client manager for Plant Care Application.
    Handles authentication, database, and storage operations.
    """
    
    def __init__(self):
        self._client: Optional[Client] = None
        self._service_client: Optional[Client] = None
        self._initialized = False
    
    def initialize(self) -> None:
        """Initialize Supabase clients."""
        try:
            # Validate configuration
            if not settings.SUPABASE_URL:
                raise ConfigurationError("SUPABASE_URL is required")
            if not settings.SUPABASE_KEY:
                raise ConfigurationError("SUPABASE_KEY is required")
            if not settings.SUPABASE_SERVICE_KEY:
                raise ConfigurationError("SUPABASE_SERVICE_KEY is required")
            
            # Create client for public operations (with anon key)
            self._client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_KEY
            )
            
            # Create service client for admin operations (with service key)
            self._service_client = create_client(
                supabase_url=settings.SUPABASE_URL,
                supabase_key=settings.SUPABASE_SERVICE_KEY
            )
            
            self._initialized = True
            logger.info("Supabase clients initialized successfully")
            
        except Exception as e:
            logger.error("Failed to initialize Supabase clients", error=str(e))
            raise ConfigurationError(f"Failed to initialize Supabase: {str(e)}")
    
    def get_client(self, service: bool = False) -> Client:
        """
        Get Supabase client.
        
        Args:
            service: Whether to use service client (admin privileges)
            
        Returns:
            Client: Supabase client instance
        """
        if not self._initialized:
            self.initialize()
        
        if service:
            return self._service_client
        return self._client
    
    def get_auth_client(self, service: bool = False) -> SyncGoTrueClient:
        """
        Get Supabase Auth client.
        
        Args:
            service: Whether to use service client
            
        Returns:
            SyncGoTrueClient: Auth client instance
        """
        client = self.get_client(service=service)
        return client.auth
    
    def get_storage_client(self, service: bool = False) -> SyncStorageClient:
        """
        Get Supabase Storage client.
        
        Args:
            service: Whether to use service client
            
        Returns:
            SyncStorageClient: Storage client instance
        """
        client = self.get_client(service=service)
        return client.storage
    
    async def health_check(self) -> dict:
        """
        Perform Supabase health check.
        
        Returns:
            dict: Health check results
        """
        try:
            # Test database connection
            client = self.get_client()
            result = client.table("health_check").select("*").limit(1).execute()
            
            # Test auth service
            auth_client = self.get_auth_client()
            # Note: We don't test actual auth operations in health check
            
            # Test storage service
            storage_client = self.get_storage_client()
            buckets = storage_client.list_buckets()
            
            return {
                "status": "healthy",
                "database": "connected",
                "auth": "connected", 
                "storage": "connected",
                "buckets_count": len(buckets),
                "supabase_url": settings.SUPABASE_URL,
            }
            
        except Exception as e:
            logger.error("Supabase health check failed", error=str(e))
            return {
                "status": "unhealthy",
                "error": str(e),
                "supabase_url": settings.SUPABASE_URL,
            }


# Global Supabase manager instance
_supabase_manager: Optional[SupabaseManager] = None


def get_supabase_manager() -> SupabaseManager:
    """
    Get the global Supabase manager instance.
    
    Returns:
        SupabaseManager: Supabase manager instance
    """
    global _supabase_manager
    if _supabase_manager is None:
        _supabase_manager = SupabaseManager()
    return _supabase_manager


@lru_cache()
def get_supabase_client(service: bool = False) -> Client:
    """
    Get cached Supabase client.
    
    Args:
        service: Whether to use service client
        
    Returns:
        Client: Supabase client instance
    """
    manager = get_supabase_manager()
    return manager.get_client(service=service)


@lru_cache()
def get_supabase_auth(service: bool = False) -> SyncGoTrueClient:
    """
    Get cached Supabase Auth client.
    
    Args:
        service: Whether to use service client
        
    Returns:
        SyncGoTrueClient: Auth client instance
    """
    manager = get_supabase_manager()
    return manager.get_auth_client(service=service)


@lru_cache()
def get_supabase_storage(service: bool = False) -> SyncStorageClient:
    """
    Get cached Supabase Storage client.
    
    Args:
        service: Whether to use service client
        
    Returns:
        SyncStorageClient: Storage client instance
    """
    manager = get_supabase_manager()
    return manager.get_storage_client(service=service)


# Supabase utilities for Plant Care Application
class SupabaseUtils:
    """Utility functions for Supabase operations."""
    
    @staticmethod
    def create_user_profile(user_id: str, profile_data: dict) -> dict:
        """
        Create user profile in Supabase.
        
        Args:
            user_id: User ID from Supabase Auth
            profile_data: Profile data
            
        Returns:
            dict: Created profile data
        """
        client = get_supabase_client(service=True)
        
        profile_data.update({
            "user_id": user_id,
            "created_at": "now()",
            "updated_at": "now()"
        })
        
        result = client.table("profiles").insert(profile_data).execute()
        logger.info("User profile created", user_id=user_id)
        
        return result.data[0] if result.data else {}
    
    @staticmethod
    def get_user_profile(user_id: str) -> Optional[dict]:
        """
        Get user profile from Supabase.
        
        Args:
            user_id: User ID
            
        Returns:
            Optional[dict]: User profile data
        """
        client = get_supabase_client()
        result = client.table("profiles").select("*").eq("user_id", user_id).single().execute()
        
        return result.data if result.data else None
    
    @staticmethod
    def update_user_profile(user_id: str, profile_data: dict) -> dict:
        """
        Update user profile in Supabase.
        
        Args:
            user_id: User ID
            profile_data: Updated profile data
            
        Returns:
            dict: Updated profile data
        """
        client = get_supabase_client()
        
        profile_data.update({
            "updated_at": "now()"
        })
        
        result = client.table("profiles").update(profile_data).eq("user_id", user_id).execute()
        logger.info("User profile updated", user_id=user_id)
        
        return result.data[0] if result.data else {}
    
    @staticmethod
    def upload_file(bucket: str, file_path: str, file_data: bytes, content_type: str = None) -> str:
        """
        Upload file to Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: File path in bucket
            file_data: File binary data
            content_type: MIME type
            
        Returns:
            str: Public URL of uploaded file
        """
        storage = get_supabase_storage(service=True)
        
        # Upload file
        result = storage.from_(bucket).upload(
            path=file_path,
            file=file_data,
            file_options={
                "content-type": content_type,
                "cache-control": "3600"
            }
        )
        
        if result.get("error"):
            raise Exception(f"File upload failed: {result['error']}")
        
        # Get public URL
        public_url = storage.from_(bucket).get_public_url(file_path)
        
        logger.info("File uploaded to Supabase Storage", bucket=bucket, file_path=file_path)
        
        return public_url
    
    @staticmethod
    def delete_file(bucket: str, file_path: str) -> bool:
        """
        Delete file from Supabase Storage.
        
        Args:
            bucket: Storage bucket name
            file_path: File path in bucket
            
        Returns:
            bool: True if successful
        """
        storage = get_supabase_storage(service=True)
        
        result = storage.from_(bucket).remove([file_path])
        
        if result.get("error"):
            logger.error("File deletion failed", bucket=bucket, file_path=file_path, error=result["error"])
            return False
        
        logger.info("File deleted from Supabase Storage", bucket=bucket, file_path=file_path)
        return True
    
    @staticmethod
    def create_signed_url(bucket: str, file_path: str, expires_in: int = 3600) -> str:
        """
        Create signed URL for private file access.
        
        Args:
            bucket: Storage bucket name
            file_path: File path in bucket
            expires_in: URL expiration time in seconds
            
        Returns:
            str: Signed URL
        """
        storage = get_supabase_storage(service=True)
        
        result = storage.from_(bucket).create_signed_url(
            path=file_path,
            expires_in=expires_in
        )
        
        if result.get("error"):
            raise Exception(f"Signed URL creation failed: {result['error']}")
        
        return result["signedURL"]


# Export Supabase utilities
__all__ = [
    "SupabaseManager",
    "get_supabase_manager",
    "get_supabase_client",
    "get_supabase_auth",
    "get_supabase_storage",
    "SupabaseUtils",
]