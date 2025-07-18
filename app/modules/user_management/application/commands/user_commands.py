# app/modules/user_management/application/commands/user_commands.py
"""
Plant Care Application - User Management Commands

Commands for user lifecycle operations in the Plant Care Application.
Handles registration, activation, deactivation, deletion, and password management.
"""

from dataclasses import dataclass
from typing import Optional, Dict, Any
from datetime import datetime

from app.modules.user_management.application.dto.user_dto import UserRegistrationDTO
from app.modules.user_management.application.dto.profile_dto import ProfileCreationDTO


@dataclass
class RegisterUserCommand:
    """
    Command to register a new user with profile in the Plant Care Application.
    Creates both user account and initial profile with Plant Care preferences.
    """
    # Core registration data
    email: str
    password: str
    display_name: str
    
    # Registration context
    registration_source: str = "web"  # web, mobile, api
    provider: str = "email"  # email, google, apple, facebook
    provider_user_id: Optional[str] = None
    
    # Optional profile data
    bio: Optional[str] = None
    location: Optional[str] = None
    timezone: str = "UTC"
    
    # Plant Care preferences
    experience_level: str = "beginner"
    preferred_units: str = "metric"
    plant_care_preferences: Dict[str, Any] = None
    notification_preferences: Dict[str, Any] = None
    
    # Profile settings
    profile_visibility: str = "public"
    
    # Registration metadata
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    referrer: Optional[str] = None
    marketing_consent: bool = False
    terms_accepted: bool = True
    privacy_policy_accepted: bool = True
    
    # Auto-generation flags
    auto_verify_email: bool = False  # For OAuth registrations
    send_welcome_email: bool = True
    create_default_subscription: bool = True
    
    def __post_init__(self):
        """Initialize default preferences if not provided."""
        if self.plant_care_preferences is None:
            self.plant_care_preferences = {
                "watering_reminder_frequency": 1,
                "fertilizing_reminder_frequency": 30,
                "preferred_care_difficulty": "easy",
                "preferred_plant_types": [],
                "care_notification_time": "09:00",
                "weekend_care_reminders": True,
                "seasonal_care_adjustments": True
            }
        
        if self.notification_preferences is None:
            self.notification_preferences = {
                "email_notifications": True,
                "push_notifications": True,
                "care_reminders": True,
                "plant_health_alerts": True,
                "expert_advice": True,
                "community_updates": False,
                "marketing_emails": self.marketing_consent,
                "weekly_digest": True
            }


@dataclass
class ActivateUserCommand:
    """
    Command to activate a user account in the Plant Care Application.
    Handles email verification and account activation.
    """
    user_id: str
    activation_token: Optional[str] = None
    activation_method: str = "email"  # email, admin, auto
    activated_by: Optional[str] = None  # admin_user_id if activated by admin
    activation_reason: Optional[str] = None
    send_activation_email: bool = True
    grant_initial_credits: bool = True  # AI identification credits
    
    # Activation context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    activation_source: str = "web"


@dataclass
class DeactivateUserCommand:
    """
    Command to deactivate a user account in the Plant Care Application.
    Temporarily suspends account while preserving data.
    """
    user_id: str
    deactivation_reason: str
    deactivated_by: str  # admin_user_id or user_id (self-deactivation)
    
    # Deactivation options
    suspend_subscription: bool = True
    disable_notifications: bool = True
    hide_from_search: bool = True
    preserve_data: bool = True
    
    # Communication
    send_deactivation_email: bool = True
    deactivation_message: Optional[str] = None
    reactivation_instructions: bool = True
    
    # Admin context
    admin_notes: Optional[str] = None
    scheduled_reactivation: Optional[datetime] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class DeleteUserCommand:
    """
    Command to permanently delete a user account (GDPR compliant).
    Handles complete data removal from the Plant Care Application.
    """
    user_id: str
    deletion_reason: str
    deleted_by: str  # admin_user_id or user_id (self-deletion)
    
    # Deletion verification
    password_confirmation: Optional[str] = None  # For self-deletion
    confirmation_token: Optional[str] = None
    
    # GDPR compliance
    gdpr_request: bool = False
    export_data_before_deletion: bool = True
    data_export_email: Optional[str] = None
    
    # Deletion scope
    delete_user_account: bool = True
    delete_profile: bool = True
    delete_plants: bool = True
    delete_photos: bool = True
    delete_subscription: bool = True
    delete_usage_data: bool = True
    
    # Data preservation (for legal/business reasons)
    preserve_anonymized_analytics: bool = True
    preserve_financial_records: bool = True  # Legal requirement
    preserve_violation_records: bool = True  # If any policy violations
    
    # Communication
    send_deletion_confirmation: bool = True
    deletion_grace_period_days: int = 7  # Days before actual deletion
    
    # Admin context
    admin_notes: Optional[str] = None
    legal_hold: bool = False  # Prevents deletion if under legal investigation
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ChangePasswordCommand:
    """
    Command to change user password in the Plant Care Application.
    Handles password updates with security validation.
    """
    user_id: str
    current_password: str
    new_password: str
    
    # Security context
    require_current_password: bool = True
    force_logout_all_sessions: bool = True
    send_password_change_email: bool = True
    
    # Password policy validation
    validate_password_strength: bool = True
    check_password_history: bool = True  # Prevent reusing recent passwords
    
    # Change context
    change_reason: str = "user_requested"  # user_requested, admin_reset, security_incident
    changed_by: Optional[str] = None  # admin_user_id if changed by admin
    
    # Security monitoring
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    suspicious_activity: bool = False
    
    # Two-factor authentication
    two_factor_token: Optional[str] = None
    require_2fa: bool = False


@dataclass
class VerifyEmailCommand:
    """
    Command to verify user email address in the Plant Care Application.
    Handles email verification process and updates.
    """
    user_id: str
    verification_token: str
    
    # Verification context
    verification_method: str = "email_link"  # email_link, email_code, admin
    verified_by: Optional[str] = None  # admin_user_id if verified by admin
    
    # Email update (if verifying new email)
    new_email: Optional[str] = None
    
    # Post-verification actions
    grant_verification_bonus: bool = True  # Extra AI credits for verified users
    send_welcome_series: bool = True  # Welcome email series
    enable_premium_trial: bool = False  # Offer premium trial
    
    # Security
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    
    # Business logic
    mark_as_trusted_user: bool = True
    increase_rate_limits: bool = True  # Higher limits for verified users


@dataclass
class UpdateUserStatusCommand:
    """
    Command to update user status in the Plant Care Application.
    Handles status changes like suspension, verification, etc.
    """
    user_id: str
    new_status: str  # active, inactive, suspended, banned, pending_verification
    status_reason: str
    updated_by: str  # admin_user_id or system
    
    # Status change context
    previous_status: Optional[str] = None
    status_duration: Optional[int] = None  # Days for temporary status
    auto_revert_date: Optional[datetime] = None
    
    # Admin context
    admin_notes: Optional[str] = None
    internal_notes: Optional[str] = None
    
    # User communication
    notify_user: bool = True
    notification_message: Optional[str] = None
    send_status_email: bool = True
    
    # Business impact
    suspend_subscription: bool = False
    revoke_expert_status: bool = False
    disable_plant_sharing: bool = False
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UpdateUserRoleCommand:
    """
    Command to update user role in the Plant Care Application.
    Handles role assignments and permission changes.
    """
    user_id: str
    new_role: str  # user, moderator, expert, admin
    role_reason: str
    updated_by: str  # admin_user_id
    
    # Role change context
    previous_role: Optional[str] = None
    role_effective_date: Optional[datetime] = None
    role_expiry_date: Optional[datetime] = None
    
    # Expert role specific
    expert_specialties: Optional[list] = None
    expert_credentials: Optional[Dict[str, Any]] = None
    consultation_rate: Optional[float] = None
    
    # Moderator role specific
    moderation_permissions: Optional[list] = None
    moderation_areas: Optional[list] = None  # community, content, users
    
    # Admin context
    admin_notes: Optional[str] = None
    approval_required: bool = False
    
    # User communication
    notify_user: bool = True
    send_role_change_email: bool = True
    role_announcement: bool = False  # Announce new experts/moderators
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class MergeUserAccountsCommand:
    """
    Command to merge two user accounts in the Plant Care Application.
    Handles account consolidation when users have multiple accounts.
    """
    primary_user_id: str  # Account to keep
    secondary_user_id: str  # Account to merge and delete
    merge_reason: str
    merged_by: str  # admin_user_id
    
    # Merge options
    merge_profile_data: bool = True
    merge_plants: bool = True
    merge_photos: bool = True
    merge_subscription: str = "keep_primary"  # keep_primary, keep_secondary, merge_benefits
    merge_usage_data: bool = True
    merge_social_connections: bool = True
    
    # Data conflict resolution
    profile_data_preference: str = "primary"  # primary, secondary, manual
    manual_field_selections: Optional[Dict[str, str]] = None
    
    # Communication
    notify_primary_user: bool = True
    notify_secondary_user: bool = True
    send_merge_confirmation: bool = True
    
    # Admin context
    admin_notes: Optional[str] = None
    manual_review_required: bool = False
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ExportUserDataCommand:
    """
    Command to export user data (GDPR compliance).
    Generates complete data export for the Plant Care Application.
    """
    user_id: str
    export_reason: str = "user_request"  # user_request, gdpr, legal, admin
    requested_by: str  # user_id or admin_user_id
    
    # Export scope
    include_profile_data: bool = True
    include_plants: bool = True
    include_photos: bool = True
    include_usage_data: bool = True
    include_subscription_data: bool = True
    include_financial_data: bool = False  # Restricted
    include_system_logs: bool = False  # Admin only
    
    # Export format
    export_format: str = "json"  # json, csv, pdf
    include_metadata: bool = True
    anonymize_related_users: bool = True
    
    # Delivery
    delivery_method: str = "email"  # email, download_link, secure_transfer
    delivery_email: Optional[str] = None
    secure_transfer_details: Optional[Dict[str, Any]] = None
    
    # Security
    encryption_required: bool = True
    password_protect: bool = True
    access_expiry_days: int = 7
    
    # Admin context
    admin_notes: Optional[str] = None
    legal_hold_override: bool = False
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None