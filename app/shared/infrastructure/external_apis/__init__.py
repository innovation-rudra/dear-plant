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

