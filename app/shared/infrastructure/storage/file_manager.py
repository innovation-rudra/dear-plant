"""
app/shared/infrastructure/storage/file_manager.py
Plant Care Application - File Upload and Management

Handles file uploads, validation, processing, and storage for the Plant Care Application.
Integrates with Supabase Storage for plant photos, user avatars, and other media files.
"""
import uuid
import mimetypes
from typing import BinaryIO, Dict, List, Optional, Tuple
from datetime import datetime
from pathlib import Path
import hashlib

from PIL import Image, ImageOps
import structlog

from app.shared.config.settings import get_settings
from app.shared.config.supabase import SupabaseUtils
from app.shared.core.exceptions import (
    FileError,
    InvalidFileTypeError,
    FileSizeExceededError,
    FileUploadError,
)
from app.shared.utils.logging import log_user_action

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class PlantCareFileManager:
    """
    File manager for Plant Care Application.
    Handles plant photos, user avatars, and other media files.
    """
    
    def __init__(self):
        self.storage_bucket = settings.STORAGE_BUCKET
        self.max_file_size = settings.MAX_FILE_SIZE
        self.allowed_image_types = settings.allowed_image_types_list
        self.compression_quality = settings.IMAGE_COMPRESSION_QUALITY
        
        # File type configurations for Plant Care
        self.file_configs = {
            "plant_photos": {
                "max_size": 10 * 1024 * 1024,  # 10MB
                "allowed_types": ["image/jpeg", "image/png", "image/webp"],
                "resize": (1920, 1920),  # Max dimensions
                "generate_thumbnails": True,
                "path_prefix": "plants"
            },
            "user_avatars": {
                "max_size": 5 * 1024 * 1024,  # 5MB
                "allowed_types": ["image/jpeg", "image/png", "image/webp"],
                "resize": (512, 512),
                "generate_thumbnails": True,
                "path_prefix": "users"
            },
            "growth_photos": {
                "max_size": 15 * 1024 * 1024,  # 15MB
                "allowed_types": ["image/jpeg", "image/png", "image/webp"],
                "resize": (2048, 2048),
                "generate_thumbnails": True,
                "path_prefix": "growth"
            },
            "health_photos": {
                "max_size": 10 * 1024 * 1024,  # 10MB
                "allowed_types": ["image/jpeg", "image/png", "image/webp"],
                "resize": (1920, 1920),
                "generate_thumbnails": True,
                "path_prefix": "health"
            },
            "community_photos": {
                "max_size": 8 * 1024 * 1024,  # 8MB
                "allowed_types": ["image/jpeg", "image/png", "image/webp"],
                "resize": (1600, 1600),
                "generate_thumbnails": True,
                "path_prefix": "community"
            }
        }
    
    async def upload_plant_photo(
        self,
        user_id: str,
        plant_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, str]:
        """
        Upload plant photo with processing and thumbnail generation.
        
        Args:
            user_id: User ID
            plant_id: Plant ID
            file_data: File binary data
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Dict containing URLs for original and thumbnail
        """
        try:
            config = self.file_configs["plant_photos"]
            
            # Validate file
            self._validate_file(file_data, content_type, config)
            
            # Process image
            processed_data, thumbnail_data = await self._process_image(
                file_data, config
            )
            
            # Generate file paths
            file_extension = self._get_file_extension(filename, content_type)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            
            original_path = f"{config['path_prefix']}/{user_id}/{plant_id}/original_{timestamp}_{file_id}.{file_extension}"
            thumbnail_path = f"{config['path_prefix']}/{user_id}/{plant_id}/thumb_{timestamp}_{file_id}.{file_extension}"
            
            # Upload to Supabase Storage
            original_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=original_path,
                file_data=processed_data,
                content_type=content_type
            )
            
            thumbnail_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=thumbnail_path,
                file_data=thumbnail_data,
                content_type=content_type
            )
            
            # Log upload action
            log_user_action(
                user_id=user_id,
                action="plant_photo_uploaded",
                plant_id=plant_id,
                file_size=len(file_data),
                file_type=content_type
            )
            
            logger.info(
                "Plant photo uploaded successfully",
                user_id=user_id,
                plant_id=plant_id,
                original_url=original_url,
                thumbnail_url=thumbnail_url
            )
            
            return {
                "original_url": original_url,
                "thumbnail_url": thumbnail_url,
                "file_path": original_path,
                "thumbnail_path": thumbnail_path,
                "file_size": len(processed_data)
            }
            
        except Exception as e:
            logger.error(
                "Plant photo upload failed",
                user_id=user_id,
                plant_id=plant_id,
                error=str(e)
            )
            raise FileUploadError(f"Failed to upload plant photo: {str(e)}")
    
    async def upload_user_avatar(
        self,
        user_id: str,
        file_data: bytes,
        filename: str,
        content_type: str
    ) -> Dict[str, str]:
        """
        Upload user avatar with processing.
        
        Args:
            user_id: User ID
            file_data: File binary data
            filename: Original filename
            content_type: MIME type
            
        Returns:
            Dict containing URLs for avatar and thumbnail
        """
        try:
            config = self.file_configs["user_avatars"]
            
            # Validate file
            self._validate_file(file_data, content_type, config)
            
            # Process image (square crop for avatars)
            processed_data, thumbnail_data = await self._process_avatar(
                file_data, config
            )
            
            # Generate file paths
            file_extension = self._get_file_extension(filename, content_type)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            avatar_path = f"{config['path_prefix']}/{user_id}/avatar_{timestamp}.{file_extension}"
            thumbnail_path = f"{config['path_prefix']}/{user_id}/avatar_thumb_{timestamp}.{file_extension}"
            
            # Upload to Supabase Storage
            avatar_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=avatar_path,
                file_data=processed_data,
                content_type=content_type
            )
            
            thumbnail_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=thumbnail_path,
                file_data=thumbnail_data,
                content_type=content_type
            )
            
            # Log upload action
            log_user_action(
                user_id=user_id,
                action="avatar_uploaded",
                file_size=len(file_data),
                file_type=content_type
            )
            
            return {
                "avatar_url": avatar_url,
                "thumbnail_url": thumbnail_url,
                "file_path": avatar_path,
                "thumbnail_path": thumbnail_path
            }
            
        except Exception as e:
            logger.error("Avatar upload failed", user_id=user_id, error=str(e))
            raise FileUploadError(f"Failed to upload avatar: {str(e)}")
    
    async def upload_growth_photo(
        self,
        user_id: str,
        plant_id: str,
        file_data: bytes,
        filename: str,
        content_type: str,
        growth_date: Optional[datetime] = None
    ) -> Dict[str, str]:
        """
        Upload growth tracking photo.
        
        Args:
            user_id: User ID
            plant_id: Plant ID
            file_data: File binary data
            filename: Original filename
            content_type: MIME type
            growth_date: Date when photo was taken
            
        Returns:
            Dict containing URLs and metadata
        """
        try:
            config = self.file_configs["growth_photos"]
            
            # Validate file
            self._validate_file(file_data, content_type, config)
            
            # Process image
            processed_data, thumbnail_data = await self._process_image(
                file_data, config
            )
            
            # Generate file paths with growth date
            file_extension = self._get_file_extension(filename, content_type)
            date_str = (growth_date or datetime.now()).strftime("%Y%m%d")
            timestamp = datetime.now().strftime("%H%M%S")
            file_id = str(uuid.uuid4())[:8]
            
            original_path = f"{config['path_prefix']}/{user_id}/{plant_id}/{date_str}/growth_{timestamp}_{file_id}.{file_extension}"
            thumbnail_path = f"{config['path_prefix']}/{user_id}/{plant_id}/{date_str}/growth_thumb_{timestamp}_{file_id}.{file_extension}"
            
            # Upload to Supabase Storage
            original_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=original_path,
                file_data=processed_data,
                content_type=content_type
            )
            
            thumbnail_url = SupabaseUtils.upload_file(
                bucket=self.storage_bucket,
                file_path=thumbnail_path,
                file_data=thumbnail_data,
                content_type=content_type
            )
            
            # Log upload action
            log_user_action(
                user_id=user_id,
                action="growth_photo_uploaded",
                plant_id=plant_id,
                growth_date=date_str,
                file_size=len(file_data)
            )
            
            return {
                "original_url": original_url,
                "thumbnail_url": thumbnail_url,
                "file_path": original_path,
                "thumbnail_path": thumbnail_path,
                "growth_date": date_str
            }
            
        except Exception as e:
            logger.error("Growth photo upload failed", user_id=user_id, plant_id=plant_id, error=str(e))
            raise FileUploadError(f"Failed to upload growth photo: {str(e)}")
    
    async def delete_file(self, file_path: str, user_id: str) -> bool:
        """
        Delete file from storage.
        
        Args:
            file_path: Path to file in storage
            user_id: User ID for logging
            
        Returns:
            bool: True if successful
        """
        try:
            success = SupabaseUtils.delete_file(
                bucket=self.storage_bucket,
                file_path=file_path
            )
            
            if success:
                log_user_action(
                    user_id=user_id,
                    action="file_deleted",
                    file_path=file_path
                )
            
            return success
            
        except Exception as e:
            logger.error("File deletion failed", file_path=file_path, error=str(e))
            return False
    
    async def create_signed_url(
        self,
        file_path: str,
        expires_in: int = 3600
    ) -> str:
        """
        Create signed URL for private file access.
        
        Args:
            file_path: Path to file in storage
            expires_in: URL expiration time in seconds
            
        Returns:
            str: Signed URL
        """
        return SupabaseUtils.create_signed_url(
            bucket=self.storage_bucket,
            file_path=file_path,
            expires_in=expires_in
        )
    
    def _validate_file(
        self,
        file_data: bytes,
        content_type: str,
        config: Dict
    ) -> None:
        """Validate file size and type."""
        # Check file size
        if len(file_data) > config["max_size"]:
            raise FileSizeExceededError(
                file_size=len(file_data),
                max_size=config["max_size"]
            )
        
        # Check file type
        if content_type not in config["allowed_types"]:
            raise InvalidFileTypeError(
                file_type=content_type,
                allowed_types=config["allowed_types"]
            )
        
        # Validate image data
        try:
            Image.open(io.BytesIO(file_data)).verify()
        except Exception:
            raise InvalidFileTypeError(
                file_type="corrupted_image",
                allowed_types=config["allowed_types"]
            )
    
    async def _process_image(
        self,
        file_data: bytes,
        config: Dict
    ) -> Tuple[bytes, bytes]:
        """Process image with resizing and thumbnail generation."""
        import io
        
        # Open image
        image = Image.open(io.BytesIO(file_data))
        
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Apply EXIF orientation
        image = ImageOps.exif_transpose(image)
        
        # Resize if needed
        max_size = config.get("resize", (1920, 1920))
        if image.size[0] > max_size[0] or image.size[1] > max_size[1]:
            image.thumbnail(max_size, Image.Resampling.LANCZOS)
        
        # Generate original
        original_io = io.BytesIO()
        image.save(
            original_io,
            format="JPEG",
            quality=self.compression_quality,
            optimize=True
        )
        original_data = original_io.getvalue()
        
        # Generate thumbnail
        thumbnail = image.copy()
        thumbnail.thumbnail((400, 400), Image.Resampling.LANCZOS)
        
        thumbnail_io = io.BytesIO()
        thumbnail.save(
            thumbnail_io,
            format="JPEG",
            quality=85,
            optimize=True
        )
        thumbnail_data = thumbnail_io.getvalue()
        
        return original_data, thumbnail_data
    
    async def _process_avatar(
        self,
        file_data: bytes,
        config: Dict
    ) -> Tuple[bytes, bytes]:
        """Process avatar image with square cropping."""
        import io
        
        # Open image
        image = Image.open(io.BytesIO(file_data))
        
        # Convert to RGB if necessary
        if image.mode in ("RGBA", "P"):
            image = image.convert("RGB")
        
        # Apply EXIF orientation
        image = ImageOps.exif_transpose(image)
        
        # Square crop
        size = min(image.size)
        left = (image.width - size) // 2
        top = (image.height - size) // 2
        right = left + size
        bottom = top + size
        
        image = image.crop((left, top, right, bottom))
        
        # Resize to avatar size
        avatar_size = config.get("resize", (512, 512))
        image = image.resize(avatar_size, Image.Resampling.LANCZOS)
        
        # Generate avatar
        avatar_io = io.BytesIO()
        image.save(
            avatar_io,
            format="JPEG",
            quality=self.compression_quality,
            optimize=True
        )
        avatar_data = avatar_io.getvalue()
        
        # Generate small thumbnail
        thumbnail = image.resize((128, 128), Image.Resampling.LANCZOS)
        thumbnail_io = io.BytesIO()
        thumbnail.save(
            thumbnail_io,
            format="JPEG",
            quality=85,
            optimize=True
        )
        thumbnail_data = thumbnail_io.getvalue()
        
        return avatar_data, thumbnail_data
    
    def _get_file_extension(self, filename: str, content_type: str) -> str:
        """Get appropriate file extension."""
        # Try to get extension from filename
        if "." in filename:
            ext = filename.rsplit(".", 1)[1].lower()
            if ext in ["jpg", "jpeg", "png", "webp"]:
                return "jpg" if ext in ["jpg", "jpeg"] else ext
        
        # Fallback to content type
        if content_type == "image/jpeg":
            return "jpg"
        elif content_type == "image/png":
            return "png"
        elif content_type == "image/webp":
            return "webp"
        
        return "jpg"  # Default fallback
    
    def calculate_file_hash(self, file_data: bytes) -> str:
        """Calculate SHA-256 hash of file data."""
        return hashlib.sha256(file_data).hexdigest()


# Global file manager instance
_file_manager: Optional[PlantCareFileManager] = None


def get_file_manager() -> PlantCareFileManager:
    """
    Get the global file manager instance.
    
    Returns:
        PlantCareFileManager: File manager instance
    """
    global _file_manager
    if _file_manager is None:
        _file_manager = PlantCareFileManager()
    return _file_manager


# Export file manager utilities
__all__ = [
    "PlantCareFileManager",
    "get_file_manager",
]