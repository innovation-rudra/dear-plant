"""
app/api/websockets/__init__.py
Plant Care Application - WebSocket Package

Real-time communication features for Plant Care Application:
- Live chat with AI assistant
- Real-time notifications and alerts
- Plant care reminders
- Community interactions
- Live plant monitoring updates
"""

from app.api.websockets.connection_manager import PlantCareConnectionManager
from app.api.websockets.chat_handler import ChatHandler
from app.api.websockets.notification_handler import NotificationHandler

__all__ = [
    "PlantCareConnectionManager",
    "ChatHandler", 
    "NotificationHandler"
]

# WebSocket configuration for Plant Care Application
WEBSOCKET_CONFIG = {
    "path": "/ws",
    "max_connections": 1000,
    "heartbeat_interval": 30,  # seconds
    "connection_timeout": 300,  # seconds
    "message_size_limit": 1024 * 1024,  # 1MB
    "allowed_origins": [
        "https://plantcare.app",
        "https://app.plantcare.app",
        "http://localhost:3000",
        "http://localhost:8080"
    ]
}

# WebSocket message types for Plant Care
MESSAGE_TYPES = {
    # Authentication
    "auth": "authenticate",
    "auth_success": "authentication_success",
    "auth_failed": "authentication_failed",
    
    # AI Chat
    "chat_message": "chat_message",
    "chat_response": "chat_response",
    "chat_typing": "chat_typing",
    "chat_error": "chat_error",
    
    # Notifications
    "notification": "notification",
    "notification_read": "notification_read",
    "notification_dismissed": "notification_dismissed",
    
    # Care Reminders
    "care_reminder": "care_reminder",
    "care_task_completed": "care_task_completed",
    "care_schedule_updated": "care_schedule_updated",
    
    # Plant Updates
    "plant_health_alert": "plant_health_alert",
    "plant_milestone": "plant_milestone",
    "plant_photo_processed": "plant_photo_processed",
    
    # Community
    "community_post": "community_post",
    "community_comment": "community_comment",
    "community_like": "community_like",
    "expert_advice": "expert_advice",
    
    # System
    "heartbeat": "heartbeat",
    "error": "error",
    "disconnect": "disconnect"
}

# Channel types for organizing connections
CHANNEL_TYPES = {
    "user": "user_channel",          # Personal notifications and updates
    "ai_chat": "ai_chat_channel",    # AI assistant conversations
    "community": "community_channel", # Community updates
    "plants": "plants_channel",      # Plant-specific updates
    "care": "care_channel",          # Care reminders and tasks
    "system": "system_channel"       # System announcements
}

# WebSocket authentication configuration
WEBSOCKET_AUTH = {
    "required": True,
    "jwt_validation": True,
    "api_key_support": True,
    "anonymous_channels": ["system"],  # Channels that don't require auth
    "session_timeout": 3600  # 1 hour
}

# Real-time features configuration
REALTIME_FEATURES = {
    "ai_chat": {
        "enabled": True,
        "typing_indicators": True,
        "message_history": 50,
        "response_timeout": 30
    },
    "notifications": {
        "enabled": True,
        "instant_delivery": True,
        "badge_updates": True,
        "sound_notifications": True
    },
    "care_reminders": {
        "enabled": True,
        "snooze_options": [5, 15, 30, 60],  # minutes
        "escalation": True
    },
    "plant_monitoring": {
        "enabled": True,
        "health_alerts": True,
        "growth_updates": True,
        "photo_processing": True
    },
    "community": {
        "enabled": True,
        "live_comments": True,
        "typing_indicators": True,
        "expert_notifications": True
    }
}

def get_websocket_config():
    """Get WebSocket configuration."""
    return WEBSOCKET_CONFIG

def get_message_types():
    """Get available message types."""
    return MESSAGE_TYPES

def get_channel_types():
    """Get available channel types."""
    return CHANNEL_TYPES

def get_realtime_features():
    """Get real-time features configuration."""
    return REALTIME_FEATURES