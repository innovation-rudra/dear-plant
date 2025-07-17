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

# app/shared/infrastructure/external_apis/__init__.py
"""
Plant Care Application - External APIs Infrastructure

Manages all external API integrations for the Plant Care Application.
Includes plant identification APIs, weather APIs, and AI services.

Key Components:
- API client management
- API rotation and fallback logic
- Circuit breaker implementation
- Rate limiting and usage tracking

External APIs Integrated:
- Plant Identification: PlantNet, Trefle, Plant.id, Kindwise
- Weather: OpenWeatherMap, Tomorrow.io, Weatherstack, Visual Crossing
- AI Services: OpenAI, Google Gemini, Anthropic Claude
- Notifications: FCM, SendGrid, Telegram, Twilio
- Payments: Razorpay, Stripe
"""

# Will be imported when we create the actual API client files
# from .api_client import APIClient
# from .api_rotation import APIRotationManager
# from .circuit_breaker import CircuitBreaker

__all__ = []  # Will be populated when we create the actual files

# app/shared/events/__init__.py
"""
Plant Care Application - Event System

Internal event system for communication between modules in the Plant Care Application.
Follows Domain-Driven Design principles for decoupled module communication.

Key Components:
- Domain events for plant care actions
- Event handlers for cross-module communication
- Event publishing and subscription
- Event persistence for audit trails

Event Types:
- Plant Events: PlantAdded, PlantUpdated, PlantRemoved
- Care Events: CareTaskCompleted, CareScheduleUpdated, CareReminder
- Health Events: HealthAssessmentRecorded, HealthAlertTriggered
- Growth Events: GrowthMilestoneReached, PhotoAdded
- User Events: UserRegistered, SubscriptionChanged
- Community Events: PostCreated, CommentAdded, LikeAdded
"""

# Will be imported when we create the actual event files
# from .base import BaseEvent, EventHandler
# from .publisher import EventPublisher
# from .handlers import PlantEventHandler, CareEventHandler

__all__ = []  # Will be populated when we create the actual files

# app/modules/__init__.py
"""
Plant Care Application - Domain Modules

Contains all domain-specific modules following Domain-Driven Design (DDD) patterns.
Each module is self-contained with its own domain logic, infrastructure, and presentation layers.

Modules:
- user_management: User accounts, authentication, profiles, subscriptions
- plant_management: Plant library, personal collections, identification
- care_management: Care schedules, reminders, task tracking, history
- health_monitoring: Plant health assessment, diagnosis, treatment tracking
- growth_tracking: Growth journaling, photos, milestones, measurements
- community_social: Community feed, posts, interactions, expert advice
- ai_smart_features: AI chat, recommendations, automation rules
- weather_environmental: Weather integration, environmental monitoring
- analytics_insights: User analytics, plant analytics, insights
- notification_communication: Multi-channel notifications, templates
- payment_subscription: Payment processing, subscription management
- content_management: Educational content, knowledge base, moderation

Each module follows the same structure:
- domain/: Domain models, services, repositories, events
- infrastructure/: Database models, external integrations
- application/: Commands, queries, handlers, DTOs
- presentation/: API endpoints, schemas, dependencies
"""

__all__ = []
