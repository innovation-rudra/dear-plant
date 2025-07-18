"""
Plant Care Application - Configuration Settings
"""
import os
from functools import lru_cache
from typing import List, Optional, Union

from pydantic import Field, validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Application settings configuration.
    """
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=True,
        extra="ignore"
    )
    
    # Application Settings
    APP_NAME: str = Field(default="Plant Care API", description="Application name")
    APP_VERSION: str = Field(default="1.0.0", description="Application version")
    APP_ENV: str = Field(default="development", description="Application environment")
    DEBUG: bool = Field(default=False, description="Debug mode")
    API_V1_STR: str = Field(default="/api/v1", description="API v1 prefix")
    SECRET_KEY: str = Field(..., description="Secret key for JWT tokens")
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30, description="Access token expiration")
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=10080, description="Refresh token expiration")
    
    # Server Settings
    HOST: str = Field(default="0.0.0.0", description="Server host")
    PORT: int = Field(default=8000, description="Server port")
    RELOAD: bool = Field(default=False, description="Auto-reload on changes")
    LOG_LEVEL: str = Field(default="info", description="Logging level")
    
    # Database Configuration
    DATABASE_URL: str = Field(..., description="Database connection URL")
    DATABASE_TEST_URL: Optional[str] = Field(default=None, description="Test database URL")
    DATABASE_POOL_SIZE: int = Field(default=20, description="Database connection pool size")
    DATABASE_MAX_OVERFLOW: int = Field(default=30, description="Database max overflow")
    DATABASE_POOL_TIMEOUT: int = Field(default=30, description="Database pool timeout")
    DATABASE_POOL_RECYCLE: int = Field(default=3600, description="Database pool recycle time")
    
    # Supabase Configuration
    SUPABASE_URL: str = Field(..., description="Supabase project URL")
    SUPABASE_KEY: str = Field(..., description="Supabase anon key")
    SUPABASE_SERVICE_KEY: str = Field(..., description="Supabase service key")
    SUPABASE_JWT_SECRET: str = Field(..., description="Supabase JWT secret")
    
    # Redis Configuration
    REDIS_URL: str = Field(default="redis://localhost:6379/0", description="Redis connection URL")
    REDIS_PASSWORD: Optional[str] = Field(default=None, description="Redis password")
    REDIS_DB: int = Field(default=0, description="Redis database number")
    REDIS_MAX_CONNECTIONS: int = Field(default=20, description="Redis max connections")
    REDIS_SOCKET_TIMEOUT: int = Field(default=30, description="Redis socket timeout")
    
    # Celery Configuration
    CELERY_BROKER_URL: str = Field(default="redis://localhost:6379/1", description="Celery broker URL")
    CELERY_RESULT_BACKEND: str = Field(default="redis://localhost:6379/2", description="Celery result backend")
    CELERY_TASK_SERIALIZER: str = Field(default="json", description="Celery task serializer")
    CELERY_RESULT_SERIALIZER: str = Field(default="json", description="Celery result serializer")
    CELERY_TIMEZONE: str = Field(default="UTC", description="Celery timezone")
    
    # API Rate Limiting
    RATE_LIMIT_REQUESTS: int = Field(default=1000, description="Rate limit requests per period")
    RATE_LIMIT_PERIOD: int = Field(default=3600, description="Rate limit period in seconds")
    RATE_LIMIT_BURST: int = Field(default=10, description="Rate limit burst allowance")
    PREMIUM_RATE_LIMIT_MULTIPLIER: int = Field(default=5, description="Premium rate limit multiplier")
    
    # File Storage
    STORAGE_BUCKET: str = Field(default="plant-care-storage", description="Storage bucket name")
    MAX_FILE_SIZE: int = Field(default=10485760, description="Maximum file size in bytes")
    ALLOWED_IMAGE_TYPES: str = Field(default="image/jpeg,image/png,image/webp", description="Allowed image MIME types")
    IMAGE_COMPRESSION_QUALITY: int = Field(default=80, description="Image compression quality")
    
    # External APIs - Plant Identification
    PLANTNET_API_KEY: str = Field(..., description="PlantNet API key")
    PLANTNET_API_URL: str = Field(default="https://my-api.plantnet.org/v2/identify", description="PlantNet API URL")
    TREFLE_API_KEY: str = Field(..., description="Trefle API key")
    TREFLE_API_URL: str = Field(default="https://trefle.io/api/v1", description="Trefle API URL")
    PLANT_ID_API_KEY: str = Field(..., description="Plant.id API key")
    PLANT_ID_API_URL: str = Field(default="https://api.plant.id/v2/identify", description="Plant.id API URL")
    KINDWISE_API_KEY: str = Field(..., description="Kindwise API key")
    KINDWISE_API_URL: str = Field(default="https://api.kindwise.com/api/v1/identification", description="Kindwise API URL")
    
    # External APIs - Weather
    OPENWEATHER_API_KEY: str = Field(..., description="OpenWeatherMap API key")
    OPENWEATHER_API_URL: str = Field(default="https://api.openweathermap.org/data/2.5", description="OpenWeatherMap API URL")
    TOMORROW_IO_API_KEY: str = Field(..., description="Tomorrow.io API key")
    TOMORROW_IO_API_URL: str = Field(default="https://api.tomorrow.io/v4/timelines", description="Tomorrow.io API URL")
    WEATHERSTACK_API_KEY: str = Field(..., description="Weatherstack API key")
    WEATHERSTACK_API_URL: str = Field(default="http://api.weatherstack.com/current", description="Weatherstack API URL")
    VISUAL_CROSSING_API_KEY: str = Field(..., description="Visual Crossing API key")
    VISUAL_CROSSING_API_URL: str = Field(default="https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline", description="Visual Crossing API URL")
    
    # External APIs - AI Services
    OPENAI_API_KEY: str = Field(..., description="OpenAI API key")
    OPENAI_ORG_ID: Optional[str] = Field(default=None, description="OpenAI organization ID")
    OPENAI_MODEL: str = Field(default="gpt-4", description="OpenAI model")
    GOOGLE_AI_API_KEY: str = Field(..., description="Google AI API key")
    ANTHROPIC_API_KEY: str = Field(..., description="Anthropic API key")
    ANTHROPIC_MODEL: str = Field(default="claude-3-sonnet-20240229", description="Anthropic model")
    
    # External APIs - Content Moderation
    PERSPECTIVE_API_KEY: str = Field(..., description="Perspective API key")
    OPENAI_MODERATION_MODEL: str = Field(default="text-moderation-latest", description="OpenAI moderation model")
    
    # Notification Services
    FCM_SERVER_KEY: str = Field(..., description="Firebase Cloud Messaging server key")
    FCM_SENDER_ID: str = Field(..., description="FCM sender ID")
    SENDGRID_API_KEY: str = Field(..., description="SendGrid API key")
    SENDGRID_FROM_EMAIL: str = Field(default="noreply@plantcare.com", description="SendGrid from email")
    TELEGRAM_BOT_TOKEN: str = Field(..., description="Telegram bot token")
    TWILIO_ACCOUNT_SID: str = Field(..., description="Twilio account SID")
    TWILIO_AUTH_TOKEN: str = Field(..., description="Twilio auth token")
    TWILIO_PHONE_NUMBER: str = Field(..., description="Twilio phone number")
    
    # Payment Processing
    RAZORPAY_KEY_ID: str = Field(..., description="Razorpay key ID")
    RAZORPAY_KEY_SECRET: str = Field(..., description="Razorpay key secret")
    STRIPE_PUBLIC_KEY: str = Field(..., description="Stripe public key")
    STRIPE_SECRET_KEY: str = Field(..., description="Stripe secret key")
    STRIPE_WEBHOOK_SECRET: str = Field(..., description="Stripe webhook secret")
    
    # Analytics & Monitoring
    MIXPANEL_TOKEN: str = Field(..., description="Mixpanel token")
    GOOGLE_ANALYTICS_ID: str = Field(..., description="Google Analytics ID")
    DATADOG_API_KEY: str = Field(..., description="Datadog API key")
    SENTRY_DSN: str = Field(..., description="Sentry DSN")
    
    # CORS Settings
    CORS_ORIGINS: str = Field(default="*", description="CORS allowed origins")
    CORS_ALLOW_CREDENTIALS: bool = Field(default=True, description="CORS allow credentials")
    CORS_ALLOW_METHODS: str = Field(default="GET,POST,PUT,DELETE,OPTIONS", description="CORS allowed methods")
    CORS_ALLOW_HEADERS: str = Field(default="*", description="CORS allowed headers")
    
    # Security Settings
    PASSWORD_MIN_LENGTH: int = Field(default=8, description="Minimum password length")
    PASSWORD_REQUIRE_UPPERCASE: bool = Field(default=True, description="Require uppercase in password")
    PASSWORD_REQUIRE_LOWERCASE: bool = Field(default=True, description="Require lowercase in password")
    PASSWORD_REQUIRE_NUMBERS: bool = Field(default=True, description="Require numbers in password")
    PASSWORD_REQUIRE_SYMBOLS: bool = Field(default=True, description="Require symbols in password")
    JWT_ALGORITHM: str = Field(default="HS256", description="JWT algorithm")
    BCRYPT_ROUNDS: int = Field(default=12, description="Bcrypt rounds")
    
    # Cache TTL Settings (in seconds)
    CACHE_TTL_PLANT_LIBRARY: int = Field(default=86400, description="Plant library cache TTL")
    CACHE_TTL_WEATHER_DATA: int = Field(default=3600, description="Weather data cache TTL")
    CACHE_TTL_API_RESPONSE: int = Field(default=1800, description="API response cache TTL")
    CACHE_TTL_USER_DATA: int = Field(default=300, description="User data cache TTL")
    CACHE_TTL_CARE_SCHEDULE: int = Field(default=3600, description="Care schedule cache TTL")
    
    # Background Job Settings
    CELERY_WORKER_CONCURRENCY: int = Field(default=4, description="Celery worker concurrency")
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = Field(default=1000, description="Max tasks per child")
    CELERY_TASK_SOFT_TIME_LIMIT: int = Field(default=300, description="Task soft time limit")
    CELERY_TASK_TIME_LIMIT: int = Field(default=600, description="Task time limit")
    
    # Health Check Settings
    HEALTH_CHECK_TIMEOUT: int = Field(default=30, description="Health check timeout")
    HEALTH_CHECK_INTERVAL: int = Field(default=60, description="Health check interval")
    HEALTH_CHECK_FAILURE_THRESHOLD: int = Field(default=3, description="Health check failure threshold")
    
    # Logging Configuration
    LOG_FORMAT: str = Field(default="json", description="Log format")
    LOG_FILE_MAX_SIZE: int = Field(default=10485760, description="Log file max size")
    LOG_FILE_BACKUP_COUNT: int = Field(default=5, description="Log file backup count")
    
    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = Field(default=5, description="Circuit breaker failure threshold")
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = Field(default=60, description="Circuit breaker recovery timeout")
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = Field(default="HTTPException", description="Expected exception type")
    
    # API Usage Limits
    FREE_TIER_PLANTS_LIMIT: int = Field(default=5, description="Free tier plants limit")
    FREE_TIER_IDENTIFICATIONS_LIMIT: int = Field(default=3, description="Free tier identifications limit")
    FREE_TIER_PHOTOS_LIMIT: int = Field(default=10, description="Free tier photos limit")
    PREMIUM_TIER_PLANTS_LIMIT: int = Field(default=1000, description="Premium tier plants limit")
    PREMIUM_TIER_IDENTIFICATIONS_LIMIT: int = Field(default=50, description="Premium tier identifications limit")
    PREMIUM_TIER_PHOTOS_LIMIT: int = Field(default=1000, description="Premium tier photos limit")
    
    @validator("APP_ENV")
    def validate_app_env(cls, v: str) -> str:
        """Validate application environment."""
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of {allowed_envs}")
        return v
    
    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        """Validate log level."""
        allowed_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v.lower()
    
    @validator("CORS_ORIGINS")
    def validate_cors_origins(cls, v: str) -> str:
        """Validate CORS origins."""
        if v == "*":
            return v
        # Validate that each origin is a valid URL
        origins = v.split(",")
        for origin in origins:
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v
    
    @validator("ALLOWED_IMAGE_TYPES")
    def validate_allowed_image_types(cls, v: str) -> str:
        """Validate allowed image types."""
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"]
        types = v.split(",")
        for image_type in types:
            if image_type not in allowed_types:
                raise ValueError(f"Invalid image type: {image_type}")
        return v
    
    @property
    def is_development(self) -> bool:
        """Check if running in development environment."""
        return self.APP_ENV == "development"
    
    @property
    def is_production(self) -> bool:
        """Check if running in production environment."""
        return self.APP_ENV == "production"
    
    @property
    def is_testing(self) -> bool:
        """Check if running in testing environment."""
        return self.APP_ENV == "testing"
    
    @property
    def database_url_sync(self) -> str:
        """Get synchronous database URL."""
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")
    
    @property
    def allowed_image_types_list(self) -> List[str]:
        """Get allowed image types as a list."""
        return self.ALLOWED_IMAGE_TYPES.split(",")
    
    @property
    def cors_origins_list(self) -> List[str]:
        """Get CORS origins as a list."""
        if self.CORS_ORIGINS == "*":
            return ["*"]
        return self.CORS_ORIGINS.split(",")
    
@lru_cache()
def get_settings() -> Settings:
    """
    Get cached settings instance.
    """
    return Settings()


# Global settings instance
settings = get_settings()