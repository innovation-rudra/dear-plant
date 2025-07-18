# app/modules/user_management/application/commands/auth_commands.py
"""
Plant Care Application - Authentication Commands

Commands for authentication operations in the Plant Care Application.
Handles login, logout, token management, OAuth, and password reset operations.
"""

from dataclasses import dataclass, field
from typing import Optional, Dict, Any, List
from datetime import datetime


@dataclass
class LoginCommand:
    """
    Command to authenticate user login in the Plant Care Application.
    Handles credential validation and session creation.
    """
    # Login credentials
    email: str
    password: str
    
    # Login context
    login_source: str = "web"  # web, mobile, api
    device_type: str = "web"  # web, ios, android, desktop
    device_name: Optional[str] = None
    
    # Security options
    remember_me: bool = False
    session_duration_hours: int = 24
    require_2fa: bool = False
    two_factor_token: Optional[str] = None
    
    # Plant Care context
    last_viewed_plants: Optional[List[str]] = None
    restore_session_data: bool = True
    sync_offline_data: bool = True
    
    # Security monitoring
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None  # lat, lng
    
    # Login behavior
    force_login: bool = False  # Force login even if account issues
    check_suspicious_activity: bool = True
    log_security_event: bool = True
    
    # Session preferences
    enable_push_notifications: bool = True
    sync_preferences: bool = True
    load_dashboard_data: bool = True
    preload_plant_data: bool = True
    
    # Business logic
    track_login_streak: bool = True
    update_last_active: bool = True
    grant_daily_credits: bool = True  # Daily AI identification credits
    
    # Rate limiting context
    failed_attempts_count: int = 0
    lockout_until: Optional[datetime] = None


@dataclass
class LogoutCommand:
    """
    Command to handle user logout in the Plant Care Application.
    Handles session cleanup and security measures.
    """
    user_id: str
    session_id: Optional[str] = None
    
    # Logout scope
    logout_type: str = "current_session"  # current_session, all_sessions, specific_session
    device_logout: bool = False  # Logout from specific device
    
    # Session cleanup
    invalidate_tokens: bool = True
    clear_session_data: bool = True
    revoke_refresh_tokens: bool = False  # Keep refresh tokens for convenience
    
    # Plant Care data handling
    save_session_data: bool = True
    sync_offline_changes: bool = True
    preserve_draft_content: bool = True
    cache_plant_data: bool = True  # For faster next login
    
    # Security measures
    log_security_event: bool = True
    notify_other_sessions: bool = False  # Notify other active sessions
    check_suspicious_logout: bool = True
    
    # User experience
    show_logout_confirmation: bool = False
    provide_quick_login_option: bool = True
    preserve_ui_preferences: bool = True
    
    # Context
    logout_reason: str = "user_initiated"  # user_initiated, security, admin, timeout
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RefreshTokenCommand:
    """
    Command to refresh authentication tokens in the Plant Care Application.
    Handles token renewal with security validation.
    """
    user_id: str
    refresh_token: str
    current_access_token: Optional[str] = None
    
    # Token refresh options
    extend_session: bool = True
    generate_new_refresh_token: bool = False
    validate_device_fingerprint: bool = True
    
    # Security validation
    check_token_blacklist: bool = True
    validate_ip_consistency: bool = False  # Allow IP changes for mobile users
    check_suspicious_activity: bool = True
    
    # Plant Care context
    sync_recent_activity: bool = True
    refresh_plant_data: bool = False  # Only if specifically requested
    update_care_reminders: bool = True
    
    # Token configuration
    new_token_expiry_hours: int = 24
    refresh_token_expiry_days: int = 30
    
    # Business logic
    grant_daily_credits_if_new_day: bool = True
    update_last_active: bool = True
    check_subscription_status: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None


@dataclass
class OAuthLoginCommand:
    """
    Command to handle OAuth provider login in the Plant Care Application.
    Handles third-party authentication with account linking.
    """
    # OAuth provider details
    provider: str  # google, apple, facebook
    provider_user_id: str
    provider_access_token: str
    
    # User information from OAuth provider
    email: str
    display_name: str
    avatar_url: Optional[str] = None
    verified_email: bool = False
    
    # Provider-specific data
    provider_profile_data: Dict[str, Any] = field(default_factory=dict)
    provider_permissions: List[str] = field(default_factory=list)
    
    # Account linking behavior
    link_to_existing_account: bool = True
    create_new_account_if_needed: bool = True
    merge_with_email_account: bool = True
    
    # Registration data (for new accounts)
    auto_generate_username: bool = True
    default_experience_level: str = "beginner"
    default_preferred_units: str = "metric"
    default_timezone: str = "UTC"
    
    # Plant Care setup for new users
    setup_default_preferences: bool = True
    grant_oauth_welcome_credits: bool = True
    enable_social_features: bool = True
    
    # OAuth session
    remember_oauth_login: bool = True
    sync_provider_contacts: bool = False  # Plant Care social features
    import_provider_interests: bool = False  # Plant-related interests
    
    # Privacy and permissions
    respect_provider_privacy: bool = True
    request_minimal_permissions: bool = True
    allow_provider_sync: bool = False
    
    # Security
    validate_oauth_signature: bool = True
    check_provider_reputation: bool = True
    log_oauth_event: bool = True
    
    # Context
    login_source: str = "oauth"
    device_type: str = "web"
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ResetPasswordCommand:
    """
    Command to handle password reset in the Plant Care Application.
    Handles password reset request and validation.
    """
    # Password reset initiation
    email: str
    reset_method: str = "email"  # email, sms, security_questions
    
    # Reset token (for reset completion)
    reset_token: Optional[str] = None
    new_password: Optional[str] = None
    
    # Security validation
    validate_user_exists: bool = True
    check_recent_resets: bool = True
    require_additional_verification: bool = False
    
    # Plant Care context
    preserve_session_data: bool = True
    maintain_plant_data: bool = True
    keep_care_reminders: bool = True
    
    # Security measures
    invalidate_all_sessions: bool = True
    revoke_all_tokens: bool = True
    log_security_event: bool = True
    notify_security_email: bool = True
    
    # Rate limiting
    max_reset_attempts_per_hour: int = 3
    max_reset_attempts_per_day: int = 10
    lockout_duration_minutes: int = 30
    
    # Communication
    send_reset_email: bool = True
    email_template: str = "password_reset"
    include_security_tips: bool = True
    provide_support_contact: bool = True
    
    # Reset token configuration
    token_expiry_hours: int = 1
    token_single_use: bool = True
    token_ip_restriction: bool = False
    
    # Post-reset actions
    force_password_change: bool = False
    require_email_verification: bool = False
    suggest_2fa_setup: bool = True
    
    # Context
    reset_source: str = "forgot_password"  # forgot_password, security_incident, admin
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class Setup2FACommand:
    """
    Command to setup two-factor authentication in the Plant Care Application.
    Handles 2FA configuration and backup codes.
    """
    user_id: str
    tfa_method: str = "totp"  # totp, sms, email
    
    # TOTP setup
    totp_secret: Optional[str] = None
    totp_verification_code: Optional[str] = None
    authenticator_app: str = "google_authenticator"  # google_authenticator, authy, etc.
    
    # SMS setup
    phone_number: Optional[str] = None
    phone_verification_code: Optional[str] = None
    
    # Email setup
    backup_email: Optional[str] = None
    email_verification_code: Optional[str] = None
    
    # Backup codes
    generate_backup_codes: bool = True
    backup_codes_count: int = 10
    
    # 2FA configuration
    require_for_login: bool = True
    require_for_sensitive_actions: bool = True
    remember_device_days: int = 30
    
    # Plant Care specific
    require_for_plant_deletion: bool = True
    require_for_subscription_changes: bool = True
    require_for_expert_verification: bool = True
    
    # Security settings
    disable_password_login: bool = False  # Still allow password + 2FA
    enable_device_trust: bool = True
    log_2fa_events: bool = True
    
    # Recovery options
    setup_recovery_questions: bool = False
    recovery_email: Optional[str] = None
    trusted_contacts: List[str] = field(default_factory=list)
    
    # Context
    setup_reason: str = "user_initiated"  # user_initiated, security_requirement, admin
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class Verify2FACommand:
    """
    Command to verify two-factor authentication in the Plant Care Application.
    Handles 2FA code verification during sensitive operations.
    """
    user_id: str
    verification_code: str
    tfa_method: str = "totp"  # totp, sms, email, backup_code
    
    # Verification context
    operation_type: str = "login"  # login, password_change, subscription_change, etc.
    session_id: Optional[str] = None
    
    # Verification options
    remember_device: bool = False
    extend_session: bool = True
    bypass_subsequent_checks: bool = False  # For current session
    
    # Plant Care operations requiring 2FA
    plant_operation: Optional[str] = None  # delete_plant, share_garden, etc.
    subscription_operation: Optional[str] = None  # upgrade, cancel, etc.
    expert_operation: Optional[str] = None  # verification, consultation, etc.
    
    # Fallback options
    allow_backup_code: bool = True
    allow_recovery_method: bool = True
    emergency_bypass: bool = False  # Admin emergency access
    
    # Security monitoring
    track_verification_attempts: bool = True
    log_verification_result: bool = True
    check_unusual_activity: bool = True
    
    # Rate limiting
    max_attempts_per_session: int = 3
    lockout_duration_minutes: int = 15
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    device_fingerprint: Optional[str] = None


@dataclass
class DisconnectOAuthCommand:
    """
    Command to disconnect OAuth provider in the Plant Care Application.
    Handles removal of third-party authentication connections.
    """
    user_id: str
    provider: str  # google, apple, facebook
    
    # Disconnection options
    revoke_provider_tokens: bool = True
    remove_provider_data: bool = False  # Keep profile data imported from provider
    preserve_avatar: bool = True  # If avatar came from provider
    
    # Account security
    require_password_setup: bool = True  # If OAuth was only auth method
    require_email_verification: bool = False
    force_2fa_setup: bool = False
    
    # Plant Care data preservation
    preserve_plant_data: bool = True
    preserve_care_history: bool = True
    maintain_social_connections: bool = True
    keep_shared_content: bool = True
    
    # Provider-specific cleanup
    remove_provider_permissions: bool = True
    clear_provider_sync_data: bool = True
    disable_provider_notifications: bool = True
    
    # Communication
    send_disconnection_confirmation: bool = True
    explain_account_changes: bool = True
    provide_reconnection_option: bool = True
    
    # Security logging
    log_disconnection_event: bool = True
    audit_remaining_auth_methods: bool = True
    
    # Context
    disconnection_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class InvalidateSessionCommand:
    """
    Command to invalidate user sessions in the Plant Care Application.
    Handles session termination for security or administrative purposes.
    """
    user_id: str
    
    # Invalidation scope
    invalidation_scope: str = "all"  # all, current, specific, by_device
    session_ids: Optional[List[str]] = None
    device_type: Optional[str] = None
    
    # Invalidation reason
    invalidation_reason: str  # security_breach, admin_action, user_request, suspicious_activity
    forced_invalidation: bool = False  # Admin-forced vs user-initiated
    
    # Plant Care data handling
    save_session_state: bool = True
    preserve_offline_changes: bool = True
    backup_care_data: bool = True
    maintain_reminders: bool = True
    
    # Security measures
    blacklist_tokens: bool = True
    revoke_refresh_tokens: bool = True
    clear_authentication_cookies: bool = True
    log_security_event: bool = True
    
    # User notification
    notify_user: bool = True
    notification_method: str = "email"  # email, push, in_app
    explain_invalidation_reason: bool = True
    provide_relogin_instructions: bool = True
    
    # Business continuity
    maintain_critical_reminders: bool = True  # Plant care reminders
    preserve_scheduled_tasks: bool = True
    keep_subscription_active: bool = True
    
    # Administrative context
    admin_user_id: Optional[str] = None
    admin_notes: Optional[str] = None
    security_incident_id: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class ChangeEmailCommand:
    """
    Command to change user email address in the Plant Care Application.
    Handles email updates with verification and security checks.
    """
    user_id: str
    new_email: str
    current_password: str
    
    # Email change validation
    verify_new_email: bool = True
    check_email_availability: bool = True
    validate_email_format: bool = True
    prevent_disposable_emails: bool = True
    
    # Security measures
    require_current_password: bool = True
    require_2fa_if_enabled: bool = True
    two_factor_token: Optional[str] = None
    send_security_alert: bool = True
    
    # Plant Care account continuity
    preserve_subscription: bool = True
    maintain_plant_data: bool = True
    keep_social_connections: bool = True
    update_care_notifications: bool = True
    
    # Email verification process
    verification_token_expiry_hours: int = 24
    send_verification_to_new_email: bool = True
    send_notification_to_old_email: bool = True
    require_verification_completion: bool = True
    
    # Rollback options
    allow_rollback_period_hours: int = 48
    keep_old_email_temporarily: bool = True
    enable_emergency_access: bool = True
    
    # Communication preferences
    migrate_email_preferences: bool = True
    update_marketing_subscriptions: bool = True
    transfer_notification_settings: bool = True
    
    # Business logic
    update_billing_email: bool = True
    refresh_oauth_connections: bool = False
    notify_linked_services: bool = True
    
    # Context
    change_reason: Optional[str] = None
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class RevokeTokenCommand:
    """
    Command to revoke specific authentication tokens.
    Handles token revocation for security or cleanup purposes.
    """
    user_id: str
    
    # Token specification
    token_type: str = "all"  # all, access, refresh, specific
    token_value: Optional[str] = None
    token_ids: Optional[List[str]] = None
    
    # Revocation scope
    revoke_all_user_tokens: bool = False
    revoke_device_tokens: bool = False
    device_fingerprint: Optional[str] = None
    
    # Revocation reason
    revocation_reason: str  # security_breach, user_request, admin_action, cleanup
    security_incident: bool = False
    
    # Plant Care session handling
    preserve_active_sessions: bool = False
    save_session_data: bool = True
    maintain_care_reminders: bool = True
    
    # Token blacklisting
    add_to_blacklist: bool = True
    blacklist_duration_hours: Optional[int] = None  # None = permanent
    
    # User impact
    force_relogin: bool = True
    notify_user: bool = True
    explain_revocation: bool = True
    
    # Administrative
    admin_user_id: Optional[str] = None
    audit_log_entry: bool = True
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class LockAccountCommand:
    """
    Command to lock user account in the Plant Care Application.
    Handles account lockout for security or administrative reasons.
    """
    user_id: str
    lock_reason: str
    
    # Lock configuration
    lock_type: str = "security"  # security, administrative, suspicious_activity, violation
    lock_duration_hours: Optional[int] = None  # None = indefinite
    auto_unlock_date: Optional[datetime] = None
    
    # Lock scope
    prevent_login: bool = True
    prevent_api_access: bool = True
    prevent_oauth_login: bool = True
    disable_mobile_access: bool = True
    
    # Plant Care data access
    preserve_care_reminders: bool = True  # Critical plant care continues
    allow_emergency_access: bool = False
    maintain_subscription: bool = True
    preserve_plant_data: bool = True
    
    # Security measures
    revoke_all_tokens: bool = True
    invalidate_sessions: bool = True
    blacklist_tokens: bool = True
    log_security_event: bool = True
    
    # User communication
    send_lock_notification: bool = True
    explain_lock_reason: bool = True
    provide_unlock_instructions: bool = True
    include_appeal_process: bool = True
    
    # Administrative context
    locked_by: str  # admin_user_id or system
    admin_notes: Optional[str] = None
    security_incident_id: Optional[str] = None
    appeal_allowed: bool = True
    
    # Unlock conditions
    unlock_requirements: List[str] = field(default_factory=list)
    manual_review_required: bool = False
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class UnlockAccountCommand:
    """
    Command to unlock user account in the Plant Care Application.
    Handles account unlock with security validation.
    """
    user_id: str
    unlock_reason: str
    unlocked_by: str  # admin_user_id or system
    
    # Unlock validation
    verify_unlock_conditions: bool = True
    require_password_reset: bool = False
    require_2fa_setup: bool = False
    require_email_verification: bool = False
    
    # Security measures
    generate_new_tokens: bool = True
    clear_failed_attempts: bool = True
    reset_security_flags: bool = True
    audit_unlock_decision: bool = True
    
    # Plant Care restoration
    restore_full_access: bool = True
    sync_missed_care_data: bool = True
    restore_premium_features: bool = True
    reactivate_notifications: bool = True
    
    # Post-unlock actions
    force_terms_acceptance: bool = False
    require_profile_review: bool = False
    mandatory_security_training: bool = False
    
    # User communication
    send_unlock_notification: bool = True
    explain_unlock_conditions: bool = True
    provide_security_tips: bool = True
    welcome_back_message: bool = True
    
    # Monitoring
    enhanced_monitoring_days: int = 7
    flag_for_review: bool = False
    
    # Administrative
    admin_notes: Optional[str] = None
    unlock_approval_id: Optional[str] = None
    
    # Context
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None


@dataclass
class VerifyDeviceCommand:
    """
    Command to verify trusted device in the Plant Care Application.
    Handles device trust establishment for security.
    """
    user_id: str
    device_fingerprint: str
    device_name: str
    device_type: str  # web, ios, android, desktop
    
    # Device verification
    verification_method: str = "email"  # email, sms, 2fa
    verification_code: Optional[str] = None
    trust_device: bool = True
    trust_duration_days: int = 30
    
    # Device information
    device_details: Dict[str, Any] = field(default_factory=dict)
    browser_info: Optional[str] = None
    os_info: Optional[str] = None
    
    # Plant Care device features
    enable_push_notifications: bool = True
    allow_offline_mode: bool = True
    sync_care_reminders: bool = True
    cache_plant_data: bool = True
    
    # Security settings
    allow_password_saving: bool = True
    enable_biometric_auth: bool = False
    require_2fa_bypass: bool = False
    
    # Device management
    replace_existing_trust: bool = False
    max_trusted_devices: int = 5
    
    # Context
    verification_source: str = "new_device"  # new_device, login_attempt, user_request
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None
    geolocation: Optional[Dict[str, float]] = None


@dataclass
class RevokeDeviceTrustCommand:
    """
    Command to revoke device trust in the Plant Care Application.
    Handles removal of device trust for security.
    """
    user_id: str
    device_fingerprint: str
    
    # Revocation scope
    revoke_all_devices: bool = False
    revoke_device_type: Optional[str] = None
    
    # Revocation reason
    revocation_reason: str  # security_concern, device_lost, user_request
    security_incident: bool = False
    
    # Plant Care impact
    preserve_offline_data: bool = True
    maintain_care_reminders: bool = True
    clear_cached_data: bool = False
    
    # Security cleanup
    revoke_device_tokens: bool = True
    clear_device_sessions: bool = True
    remove_device_preferences: bool = False
    
    # User notification
    notify_user: bool = True
    explain_revocation: bool = True
    
    # Context
    revoked_by: Optional[str] = None  # admin_user_id if admin action
    ip_address: Optional[str] = None
    user_agent: Optional[str] = None