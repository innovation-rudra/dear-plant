# app/modules/user_management/application/commands/profile_commands.py
"""
Plant Care Application - Profile Management Commands

Commands for profile operations in the Plant Care Application.
Handles profile creation, updates, expert verification, and social features.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime

from app.modules.user_management.application.dto.profile_dto import (
    ProfileCreationDTO, ProfileUpdateDTO, ProfilePreferencesDTO
)


@dataclass
class CreateProfileCommand:
    """
    Command to create a user profile in the Plant Care Application.
    Creates initial profile with Plant Care preferences and settings.
    """
    # Core profile data (required)
    user_id: str
    display_name: str
    
    # Optional profile information
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Plant Care preferences
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    
    # Profile settings
    profile_visibility: str = "public"
    
    # Plant Care preferences with defaults
    plant_care_preferences: Dict[str, Any] = field(default_factory=lambda: {
        "watering_reminder_frequency": 1,
        "fertilizing_reminder_frequency": 30,
        "preferred_care_difficulty": "easy",
        "preferred_plant_types": [],
        "care_notification_time": "09:00",
        "weekend_care_reminders": True,
        "seasonal_care_adjustments": True
    })
    
    # Notification preferences with defaults
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
    
    # Creation context
    created_by: Optional[str] = None  # admin_user_id if created by admin
    creation_source: str = "registration"  # registration, admin, migration
    
    # Auto-setup options
    auto_follow_experts: bool = True
    setup_default_reminders: bool = True
    generate_welcome_content: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpdateProfileCommand:
    """
    Command to update profile information in the Plant Care Application.
    Handles partial updates with change tracking.
    """
    user_id: str
    profile_id: str
    
    # Basic information updates (all optional)
    display_name: Optional[str] = None
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: Optional[str] = None
    
    # Plant Care preferences
    experience_level: Optional[str] = None
    preferred_units: Optional[str] = None
    
    # Profile settings
    profile_visibility: Optional[str] = None
    
    # Preference updates
    plant_care_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    
    # Update metadata
    update_reason: Optional[str] = None
    updated_by: Optional[str] = None  # admin_user_id if updated by admin
    update_source: str = "user"  # user, admin, system, migration
    
    # Change tracking
    track_changes: bool = True
    notify_followers: bool = False  # Notify followers of significant changes
    
    # Validation options
    validate_changes: bool = True
    require_verification: bool = False  # For sensitive changes
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpdateAvatarCommand:
    """
    Command to update profile avatar in the Plant Care Application.
    Handles image upload, processing, and storage.
    """
    user_id: str
    profile_id: str
    
    # Avatar upload data
    image_data: bytes
    original_filename: str
    content_type: str
    file_size: int
    
    # Image processing options
    auto_resize: bool = True
    max_width: int = 400
    max_height: int = 400
    crop_to_square: bool = True
    optimize_quality: bool = True
    
    # Storage options
    storage_provider: str = "supabase"
    generate_thumbnails: bool = True
    thumbnail_sizes: List[int] = field(default_factory=lambda: [50, 100, 200])
    
    # Previous avatar handling
    delete_previous_avatar: bool = True
    keep_avatar_history: bool = False
    
    # Upload context
    upload_source: str = "profile_edit"  # profile_edit, registration, admin
    uploaded_by: Optional[str] = None  # admin_user_id if uploaded by admin
    
    # Validation
    validate_image: bool = True
    check_inappropriate_content: bool = True
    virus_scan: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpdatePreferencesCommand:
    """
    Command to update Plant Care and notification preferences.
    Handles preference updates with validation and defaults.
    """
    user_id: str
    profile_id: str
    
    # Plant Care preference updates
    plant_care_preferences: Optional[Dict[str, Any]] = None
    notification_preferences: Optional[Dict[str, Any]] = None
    
    # Update options
    merge_with_existing: bool = True  # Merge or replace completely
    apply_defaults: bool = True  # Apply defaults for missing values
    validate_preferences: bool = True
    
    # Plant Care specific updates
    update_care_reminders: bool = True  # Update existing reminders
    recalculate_schedules: bool = True  # Recalculate care schedules
    notify_preference_changes: bool = False
    
    # Update context
    update_reason: Optional[str] = None
    update_source: str = "user"  # user, admin, system, onboarding
    
    # Preference migration
    migrate_old_preferences: bool = False
    preference_version: str = "1.0"
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RequestExpertVerificationCommand:
    """
    Command to request expert verification in the Plant Care Application.
    Initiates the expert verification workflow.
    """
    user_id: str
    profile_id: str
    
    # Expert credentials
    credentials: Dict[str, Any]  # Education, certifications, experience
    specialties: List[str]  # Plant care specialties
    experience_years: int
    
    # Professional information
    professional_title: Optional[str] = None
    organization: Optional[str] = None
    website: Optional[str] = None
    social_media_links: Optional[Dict[str, str]] = None
    
    # Verification documents
    document_urls: List[str] = field(default_factory=list)  # Uploaded documents
    portfolio_urls: List[str] = field(default_factory=list)  # Work examples
    reference_contacts: Optional[List[Dict[str, str]]] = None
    
    # Application details
    motivation: str  # Why they want to be an expert
    contribution_plans: str  # How they plan to contribute
    consultation_interest: bool = True  # Interest in offering consultations
    content_creation_interest: bool = True  # Interest in creating content
    
    # Consultation setup (if interested)
    consultation_rate: Optional[float] = None
    consultation_types: List[str] = field(default_factory=list)
    availability_hours: Optional[Dict[str, Any]] = None
    
    # Application context
    application_source: str = "profile"  # profile, invitation, admin
    referred_by: Optional[str] = None  # user_id who referred them
    
    # Processing preferences
    priority_review: bool = False  # For special cases
    expedited_processing: bool = False
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ApproveExpertVerificationCommand:
    """
    Command to approve expert verification in the Plant Care Application.
    Completes the expert verification process.
    """
    user_id: str
    profile_id: str
    verification_request_id: str
    approved_by: str  # admin_user_id
    
    # Approval details
    approval_status: str = "approved"  # approved, rejected, needs_revision
    approval_reason: str
    approval_notes: Optional[str] = None
    
    # Expert permissions
    grant_expert_role: bool = True
    enable_consultations: bool = True
    enable_content_creation: bool = True
    enable_community_moderation: bool = False
    
    # Approved credentials and specialties
    approved_credentials: Dict[str, Any]
    approved_specialties: List[str]
    expert_level: str = "verified"  # verified, senior, master
    
    # Consultation setup
    approved_consultation_rate: Optional[float] = None
    approved_consultation_types: List[str] = field(default_factory=list)
    consultation_booking_enabled: bool = True
    
    # Expert profile setup
    expert_badge_type: str = "verified_expert"
    featured_expert: bool = False
    expert_bio_addition: Optional[str] = None
    
    # Communication
    send_approval_email: bool = True
    announce_new_expert: bool = True  # Community announcement
    create_expert_welcome_content: bool = True
    
    # Administrative
    verification_expiry_date: Optional[datetime] = None
    review_schedule: str = "annual"  # annual, biannual, none
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RejectExpertVerificationCommand:
    """
    Command to reject expert verification in the Plant Care Application.
    Handles verification rejection with feedback.
    """
    user_id: str
    profile_id: str
    verification_request_id: str
    rejected_by: str  # admin_user_id
    
    # Rejection details
    rejection_reason: str
    rejection_feedback: str  # Detailed feedback for user
    improvement_suggestions: List[str] = field(default_factory=list)
    
    # Reapplication options
    allow_reapplication: bool = True
    reapplication_wait_days: int = 30
    required_improvements: List[str] = field(default_factory=list)
    
    # Communication
    send_rejection_email: bool = True
    include_improvement_guide: bool = True
    offer_consultation: bool = False  # Admin consultation to help improve
    
    # Administrative
    internal_notes: Optional[str] = None
    flag_for_review: bool = False  # Flag suspicious applications
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class FollowUserCommand:
    """
    Command to follow another user in the Plant Care Application.
    Handles social following with Plant Care context.
    """
    follower_user_id: str  # User who wants to follow
    followed_user_id: str  # User to be followed
    
    # Follow context
    follow_reason: Optional[str] = None  # interest_in_plants, expert_advice, friend
    follow_source: str = "profile"  # profile, search, recommendation, plant_post
    
    # Plant Care context
    interested_in_plants: List[str] = field(default_factory=list)  # Plant types of interest
    interested_in_expertise: List[str] = field(default_factory=list)  # Expertise areas
    
    # Privacy and permissions
    respect_privacy_settings: bool = True
    request_permission_if_private: bool = True
    
    # Notifications
    notify_followed_user: bool = True
    follow_notification_type: str = "standard"  # standard, expert_follow, friend_follow
    
    # Follow settings
    enable_notifications: bool = True  # Notifications for their posts
    notification_frequency: str = "real_time"  # real_time, daily, weekly
    
    # Business logic
    check_follow_limits: bool = True  # Based on subscription tier
    check_blocking_status: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UnfollowUserCommand:
    """
    Command to unfollow a user in the Plant Care Application.
    Handles unfollowing with cleanup.
    """
    follower_user_id: str  # User who wants to unfollow
    followed_user_id: str  # User to be unfollowed
    
    # Unfollow context
    unfollow_reason: Optional[str] = None  # not_interested, too_many_posts, privacy
    unfollow_source: str = "profile"  # profile, settings, bulk_cleanup
    
    # Cleanup options
    remove_notifications: bool = True
    cleanup_interaction_history: bool = False
    preserve_mutual_plants: bool = True  # Keep shared plant interests
    
    # Privacy
    notify_unfollowed_user: bool = False  # Usually don't notify
    remove_from_followers_list: bool = True
    
    # Business logic
    update_follower_counts: bool = True
    recalculate_recommendations: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class BlockUserCommand:
    """
    Command to block a user in the Plant Care Application.
    Handles user blocking with comprehensive restrictions.
    """
    blocker_user_id: str  # User who is blocking
    blocked_user_id: str  # User to be blocked
    
    # Block details
    block_reason: str
    block_type: str = "full"  # full, content_only, interaction_only
    
    # Block scope
    block_direct_messages: bool = True
    block_comments: bool = True
    block_plant_interactions: bool = True
    block_follow_attempts: bool = True
    hide_from_search: bool = True
    hide_content: bool = True
    
    # Expert consultation blocking
    block_consultation_requests: bool = True
    cancel_existing_consultations: bool = False
    
    # Administrative
    report_associated: bool = False  # If this is part of a report
    report_id: Optional[str] = None
    admin_escalation: bool = False
    
    # Duration
    permanent_block: bool = True
    block_duration_days: Optional[int] = None
    auto_unblock_date: Optional[datetime] = None
    
    # Context
    ip_address: Optional[str] = None