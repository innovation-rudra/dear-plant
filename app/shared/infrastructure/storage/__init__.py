# app/shared/infrastructure/storage/__init__.py
"""
Plant Care Application - Storage Infrastructure

Handles file storage operations for the Plant Care Application.
Integrates with Supabase Storage for plant photos, user avatars, and other media files.

Key Components:
- File upload and validation
- Image processing and compression
- Supabase Storage integration
- CDN management
"""

from app.shared.config.supabase import get_supabase_storage

__all__ = ["get_supabase_storage"]
