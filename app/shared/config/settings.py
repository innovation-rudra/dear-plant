"""
Plant Care Application - Configuration Settings
"""
import os
from functools import lru_cache
from typing import List, Optional

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
    APP_NAME: str = Field(default="Plant Care API")
    APP_VERSION: str = Field(default="1.0.0")
    APP_ENV: str = Field(default="development")
    DEBUG: bool = Field(default=False)
    API_V1_STR: str = Field(default="/api/v1")
    SECRET_KEY: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int = Field(default=30)
    REFRESH_TOKEN_EXPIRE_MINUTES: int = Field(default=10080)

    # Server Settings
    HOST: str = Field(default="0.0.0.0")
    PORT: int = Field(default=8000)
    RELOAD: bool = Field(default=False)
    LOG_LEVEL: str = Field(default="info")

    # Database Configuration
    DATABASE_URL: str
    DATABASE_TEST_URL: Optional[str] = None
    DATABASE_POOL_SIZE: int = 20
    DATABASE_MAX_OVERFLOW: int = 30
    DATABASE_POOL_TIMEOUT: int = 30
    DATABASE_POOL_RECYCLE: int = 3600

    # Supabase Configuration
    SUPABASE_URL: str
    SUPABASE_KEY: str
    SUPABASE_SERVICE_KEY: str
    SUPABASE_JWT_SECRET: str

    # Redis Configuration
    REDIS_URL: str = "redis://localhost:6379/0"
    REDIS_PASSWORD: Optional[str] = None
    REDIS_DB: int = 0
    REDIS_MAX_CONNECTIONS: int = 20
    REDIS_SOCKET_TIMEOUT: int = 30

    # Celery Configuration
    CELERY_BROKER_URL: str = "redis://localhost:6379/1"
    CELERY_RESULT_BACKEND: str = "redis://localhost:6379/2"
    CELERY_TASK_SERIALIZER: str = "json"
    CELERY_RESULT_SERIALIZER: str = "json"
    CELERY_TIMEZONE: str = "UTC"

    # API Rate Limiting
    RATE_LIMIT_REQUESTS: int = 1000
    RATE_LIMIT_PERIOD: int = 3600
    RATE_LIMIT_BURST: int = 10
    PREMIUM_RATE_LIMIT_MULTIPLIER: int = 5

    # File Storage
    STORAGE_BUCKET: str = "plant-care-storage"
    MAX_FILE_SIZE: int = 10485760
    ALLOWED_IMAGE_TYPES: str = "image/jpeg,image/png,image/webp"
    IMAGE_COMPRESSION_QUALITY: int = 80

    # External APIs - Plant Identification
    PLANTNET_API_KEY: str
    PLANTNET_API_URL: str = "https://my-api.plantnet.org/v2/identify"
    TREFLE_API_KEY: str
    TREFLE_API_URL: str = "https://trefle.io/api/v1"
    PLANT_ID_API_KEY: str
    PLANT_ID_API_URL: str = "https://api.plant.id/v2/identify"
    KINDWISE_API_KEY: str
    KINDWISE_API_URL: str = "https://api.kindwise.com/api/v1/identification"

    # External APIs - Weather
    OPENWEATHER_API_KEY: str
    OPENWEATHER_API_URL: str = "https://api.openweathermap.org/data/2.5"
    TOMORROW_IO_API_KEY: str
    TOMORROW_IO_API_URL: str = "https://api.tomorrow.io/v4/timelines"
    WEATHERSTACK_API_KEY: str
    WEATHERSTACK_API_URL: str = "http://api.weatherstack.com/current"
    VISUAL_CROSSING_API_KEY: str
    VISUAL_CROSSING_API_URL: str = "https://weather.visualcrossing.com/VisualCrossingWebServices/rest/services/timeline"

    # External APIs - AI Services
    OPENAI_API_KEY: str
    OPENAI_ORG_ID: Optional[str] = None
    OPENAI_MODEL: str = "gpt-4"
    GOOGLE_AI_API_KEY: str
    ANTHROPIC_API_KEY: str
    ANTHROPIC_MODEL: str = "claude-3-sonnet-20240229"

    # External APIs - Content Moderation
    PERSPECTIVE_API_KEY: str
    OPENAI_MODERATION_MODEL: str = "text-moderation-latest"

    # Notification Services
    FCM_SERVER_KEY: str
    FCM_SENDER_ID: str
    SENDGRID_API_KEY: str
    SENDGRID_FROM_EMAIL: str = "noreply@plantcare.com"
    TELEGRAM_BOT_TOKEN: str
    TWILIO_ACCOUNT_SID: str
    TWILIO_AUTH_TOKEN: str
    TWILIO_PHONE_NUMBER: str

    # Payment Processing
    RAZORPAY_KEY_ID: str
    RAZORPAY_KEY_SECRET: str
    STRIPE_PUBLIC_KEY: str
    STRIPE_SECRET_KEY: str
    STRIPE_WEBHOOK_SECRET: str

    # Analytics & Monitoring
    MIXPANEL_TOKEN: str
    GOOGLE_ANALYTICS_ID: str
    DATADOG_API_KEY: str
    SENTRY_DSN: str

    # CORS Settings
    CORS_ORIGINS: str = "*"
    CORS_ALLOW_CREDENTIALS: bool = True
    CORS_ALLOW_METHODS: str = "GET,POST,PUT,DELETE,OPTIONS"
    CORS_ALLOW_HEADERS: str = "*"

    # Security Settings
    PASSWORD_MIN_LENGTH: int = 8
    PASSWORD_REQUIRE_UPPERCASE: bool = True
    PASSWORD_REQUIRE_LOWERCASE: bool = True
    PASSWORD_REQUIRE_NUMBERS: bool = True
    PASSWORD_REQUIRE_SYMBOLS: bool = True
    JWT_ALGORITHM: str = "HS256"
    BCRYPT_ROUNDS: int = 12

    # Cache TTL Settings (in seconds)
    CACHE_TTL_PLANT_LIBRARY: int = 86400
    CACHE_TTL_WEATHER_DATA: int = 3600
    CACHE_TTL_API_RESPONSE: int = 1800
    CACHE_TTL_USER_DATA: int = 300
    CACHE_TTL_CARE_SCHEDULE: int = 3600

    # Background Job Settings
    CELERY_WORKER_CONCURRENCY: int = 4
    CELERY_WORKER_MAX_TASKS_PER_CHILD: int = 1000
    CELERY_TASK_SOFT_TIME_LIMIT: int = 300
    CELERY_TASK_TIME_LIMIT: int = 600

    # Health Check Settings
    HEALTH_CHECK_TIMEOUT: int = 30
    HEALTH_CHECK_INTERVAL: int = 60
    HEALTH_CHECK_FAILURE_THRESHOLD: int = 3

    # Logging Configuration
    LOG_FORMAT: str = "json"
    LOG_FILE_MAX_SIZE: int = 10485760
    LOG_FILE_BACKUP_COUNT: int = 5

    # Circuit Breaker Settings
    CIRCUIT_BREAKER_FAILURE_THRESHOLD: int = 5
    CIRCUIT_BREAKER_RECOVERY_TIMEOUT: int = 60
    CIRCUIT_BREAKER_EXPECTED_EXCEPTION: str = "HTTPException"

    # API Usage Limits
    FREE_TIER_PLANTS_LIMIT: int = 5
    FREE_TIER_IDENTIFICATIONS_LIMIT: int = 3
    FREE_TIER_PHOTOS_LIMIT: int = 10
    PREMIUM_TIER_PLANTS_LIMIT: int = 1000
    PREMIUM_TIER_IDENTIFICATIONS_LIMIT: int = 50
    PREMIUM_TIER_PHOTOS_LIMIT: int = 1000

    @validator("APP_ENV")
    def validate_app_env(cls, v: str) -> str:
        allowed_envs = ["development", "staging", "production", "testing"]
        if v not in allowed_envs:
            raise ValueError(f"APP_ENV must be one of {allowed_envs}")
        return v

    @validator("LOG_LEVEL")
    def validate_log_level(cls, v: str) -> str:
        allowed_levels = ["debug", "info", "warning", "error", "critical"]
        if v.lower() not in allowed_levels:
            raise ValueError(f"LOG_LEVEL must be one of {allowed_levels}")
        return v.lower()

    @validator("CORS_ORIGINS")
    def validate_cors_origins(cls, v: str) -> str:
        if v == "*":
            return v
        for origin in v.split(","):
            if not origin.startswith(("http://", "https://")):
                raise ValueError(f"Invalid CORS origin: {origin}")
        return v

    @validator("ALLOWED_IMAGE_TYPES")
    def validate_allowed_image_types(cls, v: str) -> str:
        allowed_types = ["image/jpeg", "image/png", "image/webp", "image/gif", "image/bmp"]
        for t in v.split(","):
            if t not in allowed_types:
                raise ValueError(f"Invalid image type: {t}")
        return v

    @property
    def is_development(self) -> bool:
        return self.APP_ENV == "development"

    @property
    def is_production(self) -> bool:
        return self.APP_ENV == "production"

    @property
    def is_testing(self) -> bool:
        return self.APP_ENV == "testing"

    @property
    def database_url_sync(self) -> str:
        return self.DATABASE_URL.replace("postgresql+asyncpg://", "postgresql://")

    @property
    def allowed_image_types_list(self) -> List[str]:
        return self.ALLOWED_IMAGE_TYPES.split(",")

    @property
    def cors_origins_list(self) -> List[str]:
        return ["*"] if self.CORS_ORIGINS == "*" else self.CORS_ORIGINS.split(",")


@lru_cache()
def get_settings() -> Settings:
    return Settings()


# Global instance
settings = get_settings()