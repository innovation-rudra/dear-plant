"""
app/shared/infrastructure/external_apis/api_client.py
Plant Care Application - Generic API Client

Generic HTTP client for external APIs used in Plant Care Application.
Handles plant identification APIs, weather APIs, AI services, and other integrations.
"""
import asyncio
import time
from typing import Any, Dict, List, Optional, Union
from dataclasses import dataclass
from enum import Enum

import httpx
import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    ExternalAPIError,
    ExternalAPIRateLimitError,
    ExternalAPITimeoutError,
    ExternalAPIUnavailableError,
)
from app.shared.utils.logging import log_api_call
from app.shared.infrastructure.cache.redis_client import PlantCareCache

# Get application settings
settings = get_settings()

# Setup logger
logger = structlog.get_logger(__name__)


class APIProvider(Enum):
    """Enum for supported API providers in Plant Care Application."""
    
    # Plant Identification APIs
    PLANTNET = "plantnet"
    TREFLE = "trefle"
    PLANT_ID = "plant_id"
    KINDWISE = "kindwise"
    
    # Weather APIs
    OPENWEATHER = "openweather"
    TOMORROW_IO = "tomorrow_io"
    WEATHERSTACK = "weatherstack"
    VISUAL_CROSSING = "visual_crossing"
    
    # AI Services
    OPENAI = "openai"
    GOOGLE_AI = "google_ai"
    ANTHROPIC = "anthropic"
    
    # Notification Services
    FCM = "fcm"
    SENDGRID = "sendgrid"
    TWILIO = "twilio"
    TELEGRAM = "telegram"
    
    # Content Moderation
    PERSPECTIVE = "perspective"


@dataclass
class APIConfig:
    """Configuration for an external API."""
    
    name: str
    base_url: str
    api_key: str
    timeout: int = 30
    max_retries: int = 3
    rate_limit: int = 60  # requests per minute
    headers: Optional[Dict[str, str]] = None
    auth_type: str = "api_key"  # api_key, bearer, basic
    auth_header: str = "Authorization"


@dataclass
class APIResponse:
    """Response from an external API call."""
    
    status_code: int
    data: Optional[Dict[str, Any]]
    error: Optional[str]
    response_time: float
    provider: APIProvider
    success: bool
    cached: bool = False


class PlantCareAPIClient:
    """
    Generic API client for Plant Care Application external integrations.
    """
    
    def __init__(self):
        self.cache = PlantCareCache()
        self.session_timeout = httpx.Timeout(30.0, connect=10.0)
        
        # API configurations for Plant Care
        self.api_configs = {
            APIProvider.PLANTNET: APIConfig(
                name="PlantNet",
                base_url=settings.PLANTNET_API_URL,
                api_key=settings.PLANTNET_API_KEY,
                timeout=30,
                rate_limit=50,
                headers={"Content-Type": "application/json"}
            ),
            APIProvider.TREFLE: APIConfig(
                name="Trefle",
                base_url=settings.TREFLE_API_URL,
                api_key=settings.TREFLE_API_KEY,
                timeout=20,
                rate_limit=100,
                auth_header="Authorization",
                auth_type="bearer"
            ),
            APIProvider.PLANT_ID: APIConfig(
                name="Plant.id",
                base_url=settings.PLANT_ID_API_URL,
                api_key=settings.PLANT_ID_API_KEY,
                timeout=45,
                rate_limit=30,
                headers={"Content-Type": "application/json"}
            ),
            APIProvider.KINDWISE: APIConfig(
                name="Kindwise",
                base_url=settings.KINDWISE_API_URL,
                api_key=settings.KINDWISE_API_KEY,
                timeout=35,
                rate_limit=50
            ),
            APIProvider.OPENWEATHER: APIConfig(
                name="OpenWeatherMap",
                base_url=settings.OPENWEATHER_API_URL,
                api_key=settings.OPENWEATHER_API_KEY,
                timeout=15,
                rate_limit=1000,
                auth_type="query_param"
            ),
            APIProvider.TOMORROW_IO: APIConfig(
                name="Tomorrow.io",
                base_url=settings.TOMORROW_IO_API_URL,
                api_key=settings.TOMORROW_IO_API_KEY,
                timeout=20,
                rate_limit=100
            ),
            APIProvider.OPENAI: APIConfig(
                name="OpenAI",
                base_url="https://api.openai.com/v1",
                api_key=settings.OPENAI_API_KEY,
                timeout=60,
                rate_limit=60,
                auth_type="bearer",
                headers={"Content-Type": "application/json"}
            ),
        }
    
    async def make_request(
        self,
        provider: APIProvider,
        endpoint: str,
        method: str = "GET",
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        files: Optional[Dict[str, Any]] = None,
        cache_ttl: Optional[int] = None,
        user_id: Optional[str] = None
    ) -> APIResponse:
        """
        Make a request to an external API.
        
        Args:
            provider: API provider enum
            endpoint: API endpoint path
            method: HTTP method
            data: Request body data
            params: Query parameters
            files: Files to upload
            cache_ttl: Cache time-to-live in seconds
            user_id: User ID for rate limiting
            
        Returns:
            APIResponse: Response from the API
        """
        config = self.api_configs.get(provider)
        if not config:
            raise ExternalAPIError(
                api_name=provider.value,
                message="API provider not configured"
            )
        
        start_time = time.time()
        cache_key = None
        
        try:
            # Check cache for GET requests
            if method == "GET" and cache_ttl:
                cache_key = self._generate_cache_key(provider, endpoint, params)
                cached_response = await self.cache.get(cache_key)
                if cached_response:
                    logger.debug("API cache hit", provider=provider.value, endpoint=endpoint)
                    return APIResponse(
                        status_code=200,
                        data=cached_response,
                        error=None,
                        response_time=0.001,
                        provider=provider,
                        success=True,
                        cached=True
                    )
            
            # Check rate limits
            if user_id:
                await self._check_rate_limit(provider, user_id)
            
            # Build request
            url = f"{config.base_url.rstrip('/')}/{endpoint.lstrip('/')}"
            headers = self._build_headers(config)
            
            # Add authentication
            if config.auth_type == "query_param" and params:
                params["appid"] = config.api_key
            elif config.auth_type == "api_key":
                params = params or {}
                params["key"] = config.api_key
            
            # Make HTTP request
            timeout = httpx.Timeout(config.timeout)
            
            async with httpx.AsyncClient(timeout=timeout) as client:
                response = await client.request(
                    method=method,
                    url=url,
                    headers=headers,
                    params=params,
                    json=data if method in ["POST", "PUT", "PATCH"] and not files else None,
                    files=files
                )
            
            response_time = time.time() - start_time
            
            # Log API call
            log_api_call(
                api_name=config.name,
                endpoint=endpoint,
                response_time=response_time,
                status_code=response.status_code,
                user_id=user_id,
                method=method
            )
            
            # Handle response
            if response.status_code == 429:
                raise ExternalAPIRateLimitError(api_name=config.name)
            elif response.status_code >= 500:
                raise ExternalAPIUnavailableError(
                    api_name=config.name,
                    details={"status_code": response.status_code}
                )
            elif response.status_code >= 400:
                error_msg = f"HTTP {response.status_code}"
                try:
                    error_data = response.json()
                    error_msg = error_data.get("message", error_msg)
                except:
                    pass
                
                raise ExternalAPIError(
                    api_name=config.name,
                    message=error_msg,
                    details={"status_code": response.status_code}
                )
            
            # Parse response data
            try:
                response_data = response.json()
            except:
                response_data = {"raw_response": response.text}
            
            # Cache successful responses
            if cache_key and cache_ttl and response.status_code == 200:
                await self.cache.set(cache_key, response_data, ttl=cache_ttl)
            
            return APIResponse(
                status_code=response.status_code,
                data=response_data,
                error=None,
                response_time=response_time,
                provider=provider,
                success=True
            )
            
        except httpx.TimeoutException:
            response_time = time.time() - start_time
            logger.error(
                "API request timeout",
                provider=provider.value,
                endpoint=endpoint,
                timeout=config.timeout
            )
            raise ExternalAPITimeoutError(
                api_name=config.name,
                timeout=config.timeout
            )
            
        except (ExternalAPIError, ExternalAPIRateLimitError, ExternalAPITimeoutError, ExternalAPIUnavailableError):
            # Re-raise our custom exceptions
            raise
            
        except Exception as e:
            response_time = time.time() - start_time
            logger.error(
                "API request failed",
                provider=provider.value,
                endpoint=endpoint,
                error=str(e),
                response_time=response_time
            )
            
            return APIResponse(
                status_code=0,
                data=None,
                error=str(e),
                response_time=response_time,
                provider=provider,
                success=False
            )
    
    async def identify_plant(
        self,
        image_data: bytes,
        user_id: str,
        preferred_provider: Optional[APIProvider] = None
    ) -> APIResponse:
        """
        Identify plant using available plant identification APIs.
        
        Args:
            image_data: Plant image binary data
            user_id: User ID for rate limiting
            preferred_provider: Preferred API provider
            
        Returns:
            APIResponse: Plant identification result
        """
        providers = [APIProvider.PLANTNET, APIProvider.PLANT_ID, APIProvider.KINDWISE]
        
        if preferred_provider and preferred_provider in providers:
            providers.insert(0, preferred_provider)
            providers = list(dict.fromkeys(providers))  # Remove duplicates
        
        last_error = None
        
        for provider in providers:
            try:
                if provider == APIProvider.PLANTNET:
                    return await self._identify_with_plantnet(image_data, user_id)
                elif provider == APIProvider.PLANT_ID:
                    return await self._identify_with_plant_id(image_data, user_id)
                elif provider == APIProvider.KINDWISE:
                    return await self._identify_with_kindwise(image_data, user_id)
                    
            except (ExternalAPIRateLimitError, ExternalAPIUnavailableError) as e:
                last_error = e
                logger.warning(
                    "Plant identification API unavailable, trying next",
                    provider=provider.value,
                    error=str(e)
                )
                continue
            except Exception as e:
                last_error = e
                logger.error(
                    "Plant identification failed",
                    provider=provider.value,
                    error=str(e)
                )
                continue
        
        # If all providers failed, raise the last error
        if last_error:
            raise last_error
        else:
            raise ExternalAPIError(
                api_name="plant_identification",
                message="All plant identification APIs failed"
            )
    
    async def get_weather_data(
        self,
        location: str,
        user_id: str,
        preferred_provider: Optional[APIProvider] = None
    ) -> APIResponse:
        """
        Get weather data using available weather APIs.
        
        Args:
            location: Location string (city, coordinates)
            user_id: User ID for rate limiting
            preferred_provider: Preferred weather API provider
            
        Returns:
            APIResponse: Weather data
        """
        providers = [APIProvider.OPENWEATHER, APIProvider.TOMORROW_IO, APIProvider.WEATHERSTACK]
        
        if preferred_provider and preferred_provider in providers:
            providers.insert(0, preferred_provider)
            providers = list(dict.fromkeys(providers))
        
        # Check cache first
        cache_key = f"weather:{location.lower().replace(' ', '_')}"
        cached_weather = await self.cache.get_weather_data(location)
        if cached_weather:
            return APIResponse(
                status_code=200,
                data=cached_weather,
                error=None,
                response_time=0.001,
                provider=APIProvider.OPENWEATHER,  # Default for cached
                success=True,
                cached=True
            )
        
        last_error = None
        
        for provider in providers:
            try:
                if provider == APIProvider.OPENWEATHER:
                    response = await self.make_request(
                        provider=provider,
                        endpoint="weather",
                        params={"q": location, "units": "metric"},
                        cache_ttl=settings.CACHE_TTL_WEATHER_DATA,
                        user_id=user_id
                    )
                elif provider == APIProvider.TOMORROW_IO:
                    response = await self.make_request(
                        provider=provider,
                        endpoint="timelines",
                        params={
                            "location": location,
                            "fields": "temperature,humidity,weatherCode",
                            "timesteps": "current"
                        },
                        cache_ttl=settings.CACHE_TTL_WEATHER_DATA,
                        user_id=user_id
                    )
                else:
                    continue
                
                if response.success:
                    # Cache weather data
                    if response.data:
                        await self.cache.cache_weather_data(location, response.data)
                    return response
                    
            except (ExternalAPIRateLimitError, ExternalAPIUnavailableError) as e:
                last_error = e
                continue
            except Exception as e:
                last_error = e
                continue
        
        if last_error:
            raise last_error
        else:
            raise ExternalAPIError(
                api_name="weather",
                message="All weather APIs failed"
            )
    
    async def chat_with_ai(
        self,
        message: str,
        context: Dict[str, Any],
        user_id: str,
        preferred_provider: Optional[APIProvider] = None
    ) -> APIResponse:
        """
        Chat with AI services for plant care advice.
        
        Args:
            message: User message
            context: Plant care context
            user_id: User ID for rate limiting
            preferred_provider: Preferred AI provider
            
        Returns:
            APIResponse: AI response
        """
        providers = [APIProvider.OPENAI, APIProvider.GOOGLE_AI, APIProvider.ANTHROPIC]
        
        if preferred_provider and preferred_provider in providers:
            providers.insert(0, preferred_provider)
            providers = list(dict.fromkeys(providers))
        
        plant_care_prompt = self._build_plant_care_prompt(message, context)
        
        for provider in providers:
            try:
                if provider == APIProvider.OPENAI:
                    return await self._chat_with_openai(plant_care_prompt, user_id)
                # Add other AI providers as needed
                
            except (ExternalAPIRateLimitError, ExternalAPIUnavailableError):
                continue
            except Exception as e:
                logger.error(f"AI chat failed with {provider.value}", error=str(e))
                continue
        
        raise ExternalAPIError(
            api_name="ai_chat",
            message="All AI services unavailable"
        )
    
    async def _identify_with_plantnet(self, image_data: bytes, user_id: str) -> APIResponse:
        """Identify plant using PlantNet API."""
        import base64
        
        # Convert image to base64
        image_b64 = base64.b64encode(image_data).decode()
        
        data = {
            "images": [image_b64],
            "modifiers": ["crops", "simple"],
            "plant-details": ["common_names", "url"]
        }
        
        return await self.make_request(
            provider=APIProvider.PLANTNET,
            endpoint="identify",
            method="POST",
            data=data,
            user_id=user_id
        )
    
    async def _identify_with_plant_id(self, image_data: bytes, user_id: str) -> APIResponse:
        """Identify plant using Plant.id API."""
        import base64
        
        image_b64 = base64.b64encode(image_data).decode()
        
        data = {
            "images": [image_b64],
            "modifiers": ["crops", "similar_images"],
            "plant_details": ["common_names", "url", "description", "taxonomy"]
        }
        
        return await self.make_request(
            provider=APIProvider.PLANT_ID,
            endpoint="identification",
            method="POST",
            data=data,
            user_id=user_id
        )
    
    async def _identify_with_kindwise(self, image_data: bytes, user_id: str) -> APIResponse:
        """Identify plant using Kindwise API."""
        files = {"image": ("plant.jpg", image_data, "image/jpeg")}
        
        return await self.make_request(
            provider=APIProvider.KINDWISE,
            endpoint="identify",
            method="POST",
            files=files,
            user_id=user_id
        )
    
    async def _chat_with_openai(self, prompt: str, user_id: str) -> APIResponse:
        """Chat with OpenAI for plant care advice."""
        data = {
            "model": settings.OPENAI_MODEL,
            "messages": [
                {
                    "role": "system",
                    "content": "You are a helpful plant care expert. Provide accurate, practical advice for plant care."
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 500,
            "temperature": 0.7
        }
        
        return await self.make_request(
            provider=APIProvider.OPENAI,
            endpoint="chat/completions",
            method="POST",
            data=data,
            user_id=user_id
        )
    
    def _build_headers(self, config: APIConfig) -> Dict[str, str]:
        """Build headers for API request."""
        headers = config.headers.copy() if config.headers else {}
        
        if config.auth_type == "bearer":
            headers[config.auth_header] = f"Bearer {config.api_key}"
        elif config.auth_type == "api_key" and config.auth_header != "Authorization":
            headers[config.auth_header] = config.api_key
        
        headers["User-Agent"] = f"PlantCare/{settings.APP_VERSION}"
        
        return headers
    
    def _generate_cache_key(
        self,
        provider: APIProvider,
        endpoint: str,
        params: Optional[Dict[str, Any]]
    ) -> str:
        """Generate cache key for API request."""
        import hashlib
        import json
        
        cache_data = {
            "provider": provider.value,
            "endpoint": endpoint,
            "params": params or {}
        }
        
        cache_string = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_string.encode()).hexdigest()
        
        return f"api_cache:{provider.value}:{cache_hash}"
    
    def _build_plant_care_prompt(self, message: str, context: Dict[str, Any]) -> str:
        """Build plant care specific prompt for AI."""
        plant_info = context.get("plant", {})
        care_history = context.get("care_history", [])
        
        prompt = f"Plant Care Question: {message}\n\n"
        
        if plant_info:
            prompt += f"Plant Details:\n"
            prompt += f"- Species: {plant_info.get('species', 'Unknown')}\n"
            prompt += f"- Current Health: {plant_info.get('health_status', 'Unknown')}\n"
            prompt += f"- Location: {plant_info.get('location', 'Unknown')}\n"
            prompt += f"- Age: {plant_info.get('age', 'Unknown')}\n\n"
        
        if care_history:
            prompt += f"Recent Care History:\n"
            for care in care_history[-3:]:  # Last 3 care activities
                prompt += f"- {care.get('type')}: {care.get('date')} - {care.get('notes', 'No notes')}\n"
            prompt += "\n"
        
        prompt += "Please provide specific, actionable advice for this plant care situation."
        
        return prompt
    
    async def _check_rate_limit(self, provider: APIProvider, user_id: str) -> None:
        """Check rate limits for API usage."""
        config = self.api_configs.get(provider)
        if not config:
            return
        
        # Track API usage for rate limiting
        usage_count = await self.cache.track_api_usage(user_id, provider.value)
        
        # Check if user exceeded rate limit
        if usage_count > config.rate_limit:
            raise ExternalAPIRateLimitError(
                api_name=config.name,
                details={"usage": usage_count, "limit": config.rate_limit}
            )


# Global API client instance
_api_client: Optional[PlantCareAPIClient] = None


def get_api_client() -> PlantCareAPIClient:
    """
    Get the global API client instance.
    
    Returns:
        PlantCareAPIClient: API client instance
    """
    global _api_client
    if _api_client is None:
        _api_client = PlantCareAPIClient()
    return _api_client


# Export API client utilities
__all__ = [
    "PlantCareAPIClient",
    "APIProvider",
    "APIConfig",
    "APIResponse",
    "get_api_client",
]