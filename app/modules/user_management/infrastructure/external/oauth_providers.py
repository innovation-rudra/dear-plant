# app/modules/user_management/infrastructure/external/oauth_providers.py
"""
Plant Care Application - OAuth Providers Integration

OAuth provider integrations for the Plant Care Application.
Handles Google, Apple, Facebook authentication and profile data extraction.
"""

import json
import httpx
from datetime import datetime
from typing import Optional, Dict, Any, List
from dataclasses import dataclass
from urllib.parse import urlencode

import structlog

from app.shared.config.settings import get_settings
from app.shared.core.exceptions import (
    AuthenticationError, ValidationError, ConfigurationError
)
from app.shared.utils.helpers import PlantCareHelpers

# Setup logger
logger = structlog.get_logger(__name__)


@dataclass
class OAuthUserData:
    """Standardized OAuth user data structure."""
    provider_id: str
    email: str
    email_verified: bool
    display_name: Optional[str]
    first_name: Optional[str]
    last_name: Optional[str]
    avatar_url: Optional[str]
    provider: str
    locale: Optional[str]
    raw_data: Dict[str, Any]


class BaseOAuthProvider:
    """Base class for OAuth providers."""
    
    def __init__(self, provider_name: str):
        """
        Initialize OAuth provider.
        
        Args:
            provider_name: Name of the OAuth provider
        """
        self.provider_name = provider_name
        self.settings = get_settings()
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange authorization code for access token.
        
        Args:
            code: Authorization code
            redirect_uri: Redirect URI used in auth request
            
        Returns:
            Dict[str, Any]: Token response
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        raise NotImplementedError("Subclasses must implement exchange_code_for_token")
    
    async def get_user_data(self, access_token: str) -> OAuthUserData:
        """
        Get user data using access token.
        
        Args:
            access_token: OAuth access token
            
        Returns:
            OAuthUserData: Standardized user data
            
        Raises:
            AuthenticationError: If getting user data fails
        """
        raise NotImplementedError("Subclasses must implement get_user_data")
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke OAuth token.
        
        Args:
            token: Token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        # Default implementation - override in subclasses if supported
        logger.warning(f"{self.provider_name} does not support token revocation")
        return False
    
    async def close(self):
        """Close HTTP client."""
        await self.http_client.aclose()


class GoogleOAuthProvider(BaseOAuthProvider):
    """
    Google OAuth provider for Plant Care Application.
    Handles Google Sign-In authentication and profile data.
    """
    
    def __init__(self):
        """Initialize Google OAuth provider."""
        super().__init__("google")
        self.client_id = self.settings.google_oauth_client_id
        self.client_secret = self.settings.google_oauth_client_secret
        self.token_url = "https://oauth2.googleapis.com/token"
        self.userinfo_url = "https://www.googleapis.com/oauth2/v2/userinfo"
        self.revoke_url = "https://oauth2.googleapis.com/revoke"
        
        if not self.client_id or not self.client_secret:
            raise ConfigurationError("Google OAuth credentials not configured")
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange Google authorization code for access token.
        
        Args:
            code: Google authorization code
            redirect_uri: Redirect URI used in auth request
            
        Returns:
            Dict[str, Any]: Google token response
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        try:
            logger.info("Exchanging Google auth code for token")
            
            token_data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = await self.http_client.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error("Google token exchange failed", 
                           status_code=response.status_code, 
                           response=response.text)
                raise AuthenticationError("Failed to exchange code for token")
            
            token_response = response.json()
            
            if "error" in token_response:
                logger.error("Google token exchange error", error=token_response["error"])
                raise AuthenticationError(f"Token exchange failed: {token_response['error']}")
            
            logger.info("Google token exchange successful")
            
            return token_response
            
        except httpx.HTTPError as e:
            logger.error("Google token exchange HTTP error", error=str(e))
            raise AuthenticationError("Network error during token exchange")
        except Exception as e:
            logger.error("Google token exchange failed", error=str(e))
            raise AuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def get_user_data(self, access_token: str) -> OAuthUserData:
        """
        Get Google user data using access token.
        
        Args:
            access_token: Google access token
            
        Returns:
            OAuthUserData: Standardized user data
            
        Raises:
            AuthenticationError: If getting user data fails
        """
        try:
            logger.info("Getting Google user data")
            
            headers = {"Authorization": f"Bearer {access_token}"}
            
            response = await self.http_client.get(self.userinfo_url, headers=headers)
            
            if response.status_code != 200:
                logger.error("Google user data request failed", 
                           status_code=response.status_code,
                           response=response.text)
                raise AuthenticationError("Failed to get user data")
            
            user_data = response.json()
            
            # Extract and standardize user information
            oauth_user_data = OAuthUserData(
                provider_id=user_data.get("id"),
                email=user_data.get("email"),
                email_verified=user_data.get("verified_email", False),
                display_name=user_data.get("name"),
                first_name=user_data.get("given_name"),
                last_name=user_data.get("family_name"),
                avatar_url=user_data.get("picture"),
                provider="google",
                locale=user_data.get("locale"),
                raw_data=user_data
            )
            
            logger.info("Google user data retrieved successfully", email=oauth_user_data.email)
            
            return oauth_user_data
            
        except httpx.HTTPError as e:
            logger.error("Google user data HTTP error", error=str(e))
            raise AuthenticationError("Network error getting user data")
        except Exception as e:
            logger.error("Google user data request failed", error=str(e))
            raise AuthenticationError(f"Failed to get user data: {str(e)}")
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke Google OAuth token.
        
        Args:
            token: Google access token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        try:
            logger.info("Revoking Google token")
            
            response = await self.http_client.post(
                self.revoke_url,
                data={"token": token},
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                logger.info("Google token revoked successfully")
                return True
            else:
                logger.warning("Google token revocation failed", 
                             status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Google token revocation error", error=str(e))
            return False


class AppleOAuthProvider(BaseOAuthProvider):
    """
    Apple OAuth provider for Plant Care Application.
    Handles Apple Sign-In authentication and profile data.
    """
    
    def __init__(self):
        """Initialize Apple OAuth provider."""
        super().__init__("apple")
        self.client_id = self.settings.apple_oauth_client_id
        self.client_secret = self.settings.apple_oauth_client_secret
        self.team_id = self.settings.apple_team_id
        self.key_id = self.settings.apple_key_id
        self.private_key = self.settings.apple_private_key
        self.token_url = "https://appleid.apple.com/auth/token"
        
        if not all([self.client_id, self.team_id, self.key_id, self.private_key]):
            raise ConfigurationError("Apple OAuth credentials not configured")
    
    async def _generate_client_secret(self) -> str:
        """Generate Apple client secret JWT."""
        try:
            import jwt
            from datetime import datetime, timedelta
            
            headers = {
                "alg": "ES256",
                "kid": self.key_id
            }
            
            payload = {
                "iss": self.team_id,
                "iat": datetime.utcnow(),
                "exp": datetime.utcnow() + timedelta(hours=1),
                "aud": "https://appleid.apple.com",
                "sub": self.client_id
            }
            
            client_secret = jwt.encode(
                payload, 
                self.private_key, 
                algorithm="ES256", 
                headers=headers
            )
            
            return client_secret
            
        except Exception as e:
            logger.error("Failed to generate Apple client secret", error=str(e))
            raise AuthenticationError("Failed to generate Apple client secret")
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange Apple authorization code for access token.
        
        Args:
            code: Apple authorization code
            redirect_uri: Redirect URI used in auth request
            
        Returns:
            Dict[str, Any]: Apple token response
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        try:
            logger.info("Exchanging Apple auth code for token")
            
            client_secret = await self._generate_client_secret()
            
            token_data = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": client_secret,
                "redirect_uri": redirect_uri,
                "grant_type": "authorization_code"
            }
            
            response = await self.http_client.post(
                self.token_url,
                data=token_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code != 200:
                logger.error("Apple token exchange failed", 
                           status_code=response.status_code, 
                           response=response.text)
                raise AuthenticationError("Failed to exchange code for token")
            
            token_response = response.json()
            
            if "error" in token_response:
                logger.error("Apple token exchange error", error=token_response["error"])
                raise AuthenticationError(f"Token exchange failed: {token_response['error']}")
            
            logger.info("Apple token exchange successful")
            
            return token_response
            
        except httpx.HTTPError as e:
            logger.error("Apple token exchange HTTP error", error=str(e))
            raise AuthenticationError("Network error during token exchange")
        except Exception as e:
            logger.error("Apple token exchange failed", error=str(e))
            raise AuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def get_user_data(self, access_token: str) -> OAuthUserData:
        """
        Get Apple user data from ID token.
        
        Note: Apple doesn't provide a userinfo endpoint, so we extract data from the ID token.
        
        Args:
            access_token: Apple access token (not used, we use ID token)
            
        Returns:
            OAuthUserData: Standardized user data
            
        Raises:
            AuthenticationError: If getting user data fails
        """
        try:
            logger.info("Getting Apple user data from ID token")
            
            # For Apple, user data comes from the ID token during the initial authentication
            # This method would typically be called with the ID token, not access token
            # We'll decode the ID token to extract user information
            
            import jwt
            
            # Decode ID token without verification (for demo purposes)
            # In production, you should verify the token signature
            decoded_token = jwt.decode(access_token, options={"verify_signature": False})
            
            # Extract user information from ID token
            oauth_user_data = OAuthUserData(
                provider_id=decoded_token.get("sub"),
                email=decoded_token.get("email"),
                email_verified=decoded_token.get("email_verified", False),
                display_name=None,  # Apple doesn't provide name in ID token by default
                first_name=None,
                last_name=None,
                avatar_url=None,  # Apple doesn't provide avatar
                provider="apple",
                locale=None,
                raw_data=decoded_token
            )
            
            logger.info("Apple user data retrieved successfully", email=oauth_user_data.email)
            
            return oauth_user_data
            
        except Exception as e:
            logger.error("Apple user data extraction failed", error=str(e))
            raise AuthenticationError(f"Failed to get user data: {str(e)}")
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke Apple OAuth token.
        
        Args:
            token: Apple refresh token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        try:
            logger.info("Revoking Apple token")
            
            client_secret = await self._generate_client_secret()
            
            revoke_data = {
                "token": token,
                "client_id": self.client_id,
                "client_secret": client_secret,
                "token_type_hint": "refresh_token"
            }
            
            response = await self.http_client.post(
                self.token_url.replace("/token", "/revoke"),
                data=revoke_data,
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            if response.status_code == 200:
                logger.info("Apple token revoked successfully")
                return True
            else:
                logger.warning("Apple token revocation failed", 
                             status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Apple token revocation error", error=str(e))
            return False


class FacebookOAuthProvider(BaseOAuthProvider):
    """
    Facebook OAuth provider for Plant Care Application.
    Handles Facebook Login authentication and profile data.
    """
    
    def __init__(self):
        """Initialize Facebook OAuth provider."""
        super().__init__("facebook")
        self.client_id = self.settings.facebook_oauth_client_id
        self.client_secret = self.settings.facebook_oauth_client_secret
        self.token_url = "https://graph.facebook.com/v18.0/oauth/access_token"
        self.userinfo_url = "https://graph.facebook.com/v18.0/me"
        self.revoke_url = "https://graph.facebook.com/v18.0/me/permissions"
        
        if not self.client_id or not self.client_secret:
            raise ConfigurationError("Facebook OAuth credentials not configured")
    
    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> Dict[str, Any]:
        """
        Exchange Facebook authorization code for access token.
        
        Args:
            code: Facebook authorization code
            redirect_uri: Redirect URI used in auth request
            
        Returns:
            Dict[str, Any]: Facebook token response
            
        Raises:
            AuthenticationError: If token exchange fails
        """
        try:
            logger.info("Exchanging Facebook auth code for token")
            
            params = {
                "code": code,
                "client_id": self.client_id,
                "client_secret": self.client_secret,
                "redirect_uri": redirect_uri
            }
            
            response = await self.http_client.get(
                self.token_url,
                params=params
            )
            
            if response.status_code != 200:
                logger.error("Facebook token exchange failed", 
                           status_code=response.status_code, 
                           response=response.text)
                raise AuthenticationError("Failed to exchange code for token")
            
            token_response = response.json()
            
            if "error" in token_response:
                logger.error("Facebook token exchange error", error=token_response["error"])
                raise AuthenticationError(f"Token exchange failed: {token_response['error']['message']}")
            
            logger.info("Facebook token exchange successful")
            
            return token_response
            
        except httpx.HTTPError as e:
            logger.error("Facebook token exchange HTTP error", error=str(e))
            raise AuthenticationError("Network error during token exchange")
        except Exception as e:
            logger.error("Facebook token exchange failed", error=str(e))
            raise AuthenticationError(f"Token exchange failed: {str(e)}")
    
    async def get_user_data(self, access_token: str) -> OAuthUserData:
        """
        Get Facebook user data using access token.
        
        Args:
            access_token: Facebook access token
            
        Returns:
            OAuthUserData: Standardized user data
            
        Raises:
            AuthenticationError: If getting user data fails
        """
        try:
            logger.info("Getting Facebook user data")
            
            # Request specific fields from Facebook
            fields = "id,email,first_name,last_name,name,picture.width(200).height(200),locale"
            
            params = {
                "access_token": access_token,
                "fields": fields
            }
            
            response = await self.http_client.get(self.userinfo_url, params=params)
            
            if response.status_code != 200:
                logger.error("Facebook user data request failed", 
                           status_code=response.status_code,
                           response=response.text)
                raise AuthenticationError("Failed to get user data")
            
            user_data = response.json()
            
            if "error" in user_data:
                logger.error("Facebook user data error", error=user_data["error"])
                raise AuthenticationError(f"Failed to get user data: {user_data['error']['message']}")
            
            # Extract avatar URL from picture object
            avatar_url = None
            if "picture" in user_data and "data" in user_data["picture"]:
                avatar_url = user_data["picture"]["data"].get("url")
            
            # Extract and standardize user information
            oauth_user_data = OAuthUserData(
                provider_id=user_data.get("id"),
                email=user_data.get("email"),
                email_verified=True,  # Facebook emails are verified
                display_name=user_data.get("name"),
                first_name=user_data.get("first_name"),
                last_name=user_data.get("last_name"),
                avatar_url=avatar_url,
                provider="facebook",
                locale=user_data.get("locale"),
                raw_data=user_data
            )
            
            logger.info("Facebook user data retrieved successfully", email=oauth_user_data.email)
            
            return oauth_user_data
            
        except httpx.HTTPError as e:
            logger.error("Facebook user data HTTP error", error=str(e))
            raise AuthenticationError("Network error getting user data")
        except Exception as e:
            logger.error("Facebook user data request failed", error=str(e))
            raise AuthenticationError(f"Failed to get user data: {str(e)}")
    
    async def revoke_token(self, token: str) -> bool:
        """
        Revoke Facebook OAuth token.
        
        Args:
            token: Facebook access token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        try:
            logger.info("Revoking Facebook token")
            
            params = {"access_token": token}
            
            response = await self.http_client.delete(
                self.revoke_url,
                params=params
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info("Facebook token revoked successfully")
                    return True
                else:
                    logger.warning("Facebook token revocation failed", result=result)
                    return False
            else:
                logger.warning("Facebook token revocation failed", 
                             status_code=response.status_code)
                return False
                
        except Exception as e:
            logger.error("Facebook token revocation error", error=str(e))
            return False


class OAuthProviderManager:
    """
    OAuth provider manager for Plant Care Application.
    Manages multiple OAuth providers and provides unified interface.
    """
    
    def __init__(self):
        """Initialize OAuth provider manager."""
        self.providers = {}
        self.settings = get_settings()
        
        # Initialize available providers
        self._initialize_providers()
    
    def _initialize_providers(self):
        """Initialize available OAuth providers."""
        try:
            # Initialize Google provider if configured
            if self.settings.google_oauth_client_id and self.settings.google_oauth_client_secret:
                self.providers["google"] = GoogleOAuthProvider()
                logger.info("Google OAuth provider initialized")
            
            # Initialize Apple provider if configured
            if (self.settings.apple_oauth_client_id and 
                self.settings.apple_team_id and 
                self.settings.apple_key_id and 
                self.settings.apple_private_key):
                self.providers["apple"] = AppleOAuthProvider()
                logger.info("Apple OAuth provider initialized")
            
            # Initialize Facebook provider if configured
            if self.settings.facebook_oauth_client_id and self.settings.facebook_oauth_client_secret:
                self.providers["facebook"] = FacebookOAuthProvider()
                logger.info("Facebook OAuth provider initialized")
            
            if not self.providers:
                logger.warning("No OAuth providers configured")
                
        except Exception as e:
            logger.error("Failed to initialize OAuth providers", error=str(e))
    
    def get_provider(self, provider_name: str) -> BaseOAuthProvider:
        """
        Get OAuth provider by name.
        
        Args:
            provider_name: Name of the OAuth provider
            
        Returns:
            BaseOAuthProvider: OAuth provider instance
            
        Raises:
            ValidationError: If provider not found or not configured
        """
        if provider_name not in self.providers:
            available_providers = list(self.providers.keys())
            raise ValidationError(
                f"OAuth provider '{provider_name}' not configured. "
                f"Available providers: {available_providers}"
            )
        
        return self.providers[provider_name]
    
    def get_available_providers(self) -> List[str]:
        """
        Get list of available OAuth providers.
        
        Returns:
            List[str]: List of provider names
        """
        return list(self.providers.keys())
    
    async def handle_oauth_flow(self, provider_name: str, code: str, 
                              redirect_uri: str) -> OAuthUserData:
        """
        Handle complete OAuth flow for a provider.
        
        Args:
            provider_name: Name of the OAuth provider
            code: Authorization code
            redirect_uri: Redirect URI used in auth request
            
        Returns:
            OAuthUserData: Standardized user data
            
        Raises:
            ValidationError: If provider not found
            AuthenticationError: If OAuth flow fails
        """
        try:
            logger.info("Handling OAuth flow", provider=provider_name)
            
            provider = self.get_provider(provider_name)
            
            # Exchange code for token
            token_response = await provider.exchange_code_for_token(code, redirect_uri)
            
            # Get user data
            access_token = token_response.get("access_token")
            id_token = token_response.get("id_token")
            
            # For Apple, use ID token; for others, use access token
            token_for_userinfo = id_token if provider_name == "apple" and id_token else access_token
            
            if not token_for_userinfo:
                raise AuthenticationError("No valid token received from provider")
            
            user_data = await provider.get_user_data(token_for_userinfo)
            
            logger.info("OAuth flow completed successfully", 
                       provider=provider_name, 
                       email=user_data.email)
            
            return user_data
            
        except (ValidationError, AuthenticationError):
            raise
        except Exception as e:
            logger.error("OAuth flow failed", provider=provider_name, error=str(e))
            raise AuthenticationError(f"OAuth flow failed: {str(e)}")
    
    async def revoke_provider_token(self, provider_name: str, token: str) -> bool:
        """
        Revoke OAuth token for a provider.
        
        Args:
            provider_name: Name of the OAuth provider
            token: Token to revoke
            
        Returns:
            bool: True if revocation successful
        """
        try:
            provider = self.get_provider(provider_name)
            return await provider.revoke_token(token)
            
        except Exception as e:
            logger.error("Token revocation failed", provider=provider_name, error=str(e))
            return False
    
    async def get_provider_health(self) -> Dict[str, Any]:
        """
        Get health status of all OAuth providers.
        
        Returns:
            Dict[str, Any]: Provider health status
        """
        health_status = {
            "providers": {},
            "total_providers": len(self.providers),
            "healthy_providers": 0,
            "timestamp": datetime.utcnow().isoformat()
        }
        
        for provider_name, provider in self.providers.items():
            try:
                # Simple health check - check if provider is configured
                health_status["providers"][provider_name] = {
                    "status": "healthy",
                    "configured": True,
                    "client_id_configured": bool(getattr(provider, 'client_id', None))
                }
                health_status["healthy_providers"] += 1
                
            except Exception as e:
                health_status["providers"][provider_name] = {
                    "status": "unhealthy",
                    "error": str(e)
                }
        
        return health_status
    
    async def close(self):
        """Close all OAuth providers."""
        for provider in self.providers.values():
            await provider.close()


# Global OAuth provider manager instance
oauth_manager = OAuthProviderManager()


# Factory functions for dependency injection
def get_oauth_manager() -> OAuthProviderManager:
    """Get OAuth provider manager instance."""
    return oauth_manager


def create_google_oauth_provider() -> GoogleOAuthProvider:
    """Create Google OAuth provider instance."""
    return GoogleOAuthProvider()


def create_apple_oauth_provider() -> AppleOAuthProvider:
    """Create Apple OAuth provider instance."""
    return AppleOAuthProvider()


def create_facebook_oauth_provider() -> FacebookOAuthProvider:
    """Create Facebook OAuth provider instance."""
    return FacebookOAuthProvider()