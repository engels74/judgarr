"""
Base API client implementation.
"""
import logging
from typing import Any, Optional
import aiohttp
from pydantic import HttpUrl

logger = logging.getLogger(__name__)

class APIError(Exception):
    """Base API error."""
    def __init__(self, message: str, status_code: Optional[int] = None, response_text: Optional[str] = None):
        self.status_code = status_code
        self.response_text = response_text
        super().__init__(message)

class RateLimitError(APIError):
    """Rate limit exceeded error."""
    pass

class AuthenticationError(APIError):
    """Authentication failed error."""
    pass

class BaseAPIClient:
    """Base class for API clients."""
    
    def __init__(self, base_url: HttpUrl, api_key: str):
        """Initialize the API client.
        
        Args:
            base_url: Base URL for the API
            api_key: API key for authentication
        """
        self.base_url = str(base_url).rstrip('/')
        self.api_key = api_key
        self._session: Optional[aiohttp.ClientSession] = None
    
    async def _ensure_session(self) -> aiohttp.ClientSession:
        """Ensure an aiohttp session exists."""
        if self._session is None or self._session.closed:
            self._session = aiohttp.ClientSession()
        return self._session
    
    async def close(self) -> None:
        """Close the API client session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    def _get_headers(self) -> dict[str, str]:
        """Get headers for API requests."""
        return {
            "X-Api-Key": self.api_key,
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
    
    async def _request(
        self,
        method: str,
        endpoint: str,
        params: Optional[dict[str, Any]] = None,
        json_data: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make an API request.
        
        Args:
            method: HTTP method
            endpoint: API endpoint
            params: Query parameters
            json_data: JSON request body
            
        Returns:
            API response data
            
        Raises:
            APIError: If the API request fails
            RateLimitError: If rate limit is exceeded
            AuthenticationError: If authentication fails
        """
        session = await self._ensure_session()
        url = f"{self.base_url}{endpoint}"
        
        logger.debug(f"Making {method} request to {url}")
        logger.debug(f"Params: {params}")
        logger.debug(f"Headers: {self._get_headers()}")
        
        try:
            async with session.request(
                method,
                url,
                params=params,
                json=json_data,
                headers=self._get_headers(),
            ) as response:
                if response.status == 429:
                    raise RateLimitError("Rate limit exceeded")
                elif response.status == 401:
                    raise AuthenticationError("Invalid API key")
                elif response.status >= 400:
                    response_text = await response.text()
                    logger.error(f"API request failed with status {response.status}: {response_text}")
                    raise APIError(
                        f"API request failed: {response.status} - {response_text}",
                        status_code=response.status,
                        response_text=response_text
                    )
                
                return await response.json()
                
        except aiohttp.ClientError as e:
            raise APIError(f"Request failed: {str(e)}")
    
    async def get(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Make a GET request."""
        return await self._request("GET", endpoint, params=params)
    
    async def post(
        self,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make a POST request."""
        return await self._request("POST", endpoint, params=params, json_data=json_data)
    
    async def put(
        self,
        endpoint: str,
        json_data: Optional[dict[str, Any]] = None,
        params: Optional[dict[str, Any]] = None,
    ) -> Any:
        """Make a PUT request."""
        return await self._request("PUT", endpoint, params=params, json_data=json_data)
    
    async def delete(self, endpoint: str, params: Optional[dict[str, Any]] = None) -> Any:
        """Make a DELETE request."""
        return await self._request("DELETE", endpoint, params=params)
