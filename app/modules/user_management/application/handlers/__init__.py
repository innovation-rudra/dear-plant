# app/modules/user_management/application/handlers/__init__.py
"""
Plant Care Application - User Management Command Handlers

Command handlers for user management operations in the Plant Care Application.
Implements the command side of CQRS pattern with domain service orchestration.
"""

from .user_command_handlers import (
    RegisterUserCommandHandler,
    ActivateUserCommandHandler,
    DeactivateUserCommandHandler,
    DeleteUserCommandHandler,
    ChangePasswordCommandHandler,
    VerifyEmailCommandHandler,
    UpdateUserStatusCommandHandler,
    UpdateUserRoleCommandHandler,
    MergeUserAccountsCommandHandler,
    ExportUserDataCommandHandler
)

from .profile_command_handlers import (
    CreateProfileCommandHandler,
    UpdateProfileCommandHandler,
    UpdateAvatarCommandHandler,
    UpdatePreferencesCommandHandler,
    RequestExpertVerificationCommandHandler,
    ApproveExpertVerificationCommandHandler,
    RejectExpertVerificationCommandHandler,
    FollowUserCommandHandler,
    UnfollowUserCommandHandler,
    BlockUserCommandHandler
)

from .subscription_command_handlers import (
    CreateSubscriptionCommandHandler,
    UpgradeSubscriptionCommandHandler,
    DowngradeSubscriptionCommandHandler,
    CancelSubscriptionCommandHandler,
    RenewSubscriptionCommandHandler,
    StartTrialCommandHandler,
    PauseSubscriptionCommandHandler,
    ResumeSubscriptionCommandHandler,
    UpdatePaymentMethodCommandHandler
)

from .auth_command_handlers import (
    LoginCommandHandler,
    LogoutCommandHandler,
    RefreshTokenCommandHandler,
    OAuthLoginCommandHandler,
    ResetPasswordCommandHandler,
    Setup2FACommandHandler,
    Verify2FACommandHandler,
    DisconnectOAuthCommandHandler,
    InvalidateSessionCommandHandler,
    ChangeEmailCommandHandler,
    RevokeTokenCommandHandler,
    LockAccountCommandHandler,
    UnlockAccountCommandHandler,
    VerifyDeviceCommandHandler,
    RevokeDeviceTrustCommandHandler
)

__all__ = [
    # User Command Handlers
    "RegisterUserCommandHandler",
    "ActivateUserCommandHandler",
    "DeactivateUserCommandHandler", 
    "DeleteUserCommandHandler",
    "ChangePasswordCommandHandler",
    "VerifyEmailCommandHandler",
    "UpdateUserStatusCommandHandler",
    "UpdateUserRoleCommandHandler",
    "MergeUserAccountsCommandHandler",
    "ExportUserDataCommandHandler",
    
    # Profile Command Handlers
    "CreateProfileCommandHandler",
    "UpdateProfileCommandHandler",
    "UpdateAvatarCommandHandler",
    "UpdatePreferencesCommandHandler", 
    "RequestExpertVerificationCommandHandler",
    "ApproveExpertVerificationCommandHandler",
    "RejectExpertVerificationCommandHandler",
    "FollowUserCommandHandler",
    "UnfollowUserCommandHandler",
    "BlockUserCommandHandler",
    
    # Subscription Command Handlers
    "CreateSubscriptionCommandHandler",
    "UpgradeSubscriptionCommandHandler",
    "DowngradeSubscriptionCommandHandler",
    "CancelSubscriptionCommandHandler", 
    "RenewSubscriptionCommandHandler",
    "StartTrialCommandHandler",
    "PauseSubscriptionCommandHandler",
    "ResumeSubscriptionCommandHandler",
    "UpdatePaymentMethodCommandHandler",
    
    # Authentication Command Handlers
    "LoginCommandHandler",
    "LogoutCommandHandler",
    "RefreshTokenCommandHandler",
    "OAuthLoginCommandHandler",
    "ResetPasswordCommandHandler",
    "Setup2FACommandHandler",
    "Verify2FACommandHandler",
    "DisconnectOAuthCommandHandler",
    "InvalidateSessionCommandHandler",
    "ChangeEmailCommandHandler",
    "RevokeTokenCommandHandler",
    "LockAccountCommandHandler",
    "UnlockAccountCommandHandler",
    "VerifyDeviceCommandHandler", 
    "RevokeDeviceTrustCommandHandler"
]