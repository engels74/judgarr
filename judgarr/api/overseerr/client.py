"""
Overseerr API client implementation.
"""
from datetime import datetime, timezone
from typing import Any, Optional

from ..base import BaseAPIClient
from ...shared.types import UserId
from ...shared.constants import (
    OVERSEERR_USER_ENDPOINT,
)

class OverseerrClient(BaseAPIClient):
    """Client for interacting with the Overseerr API."""
    
    async def get_user_requests(
        self,
        user_id: UserId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[int] = None,
        page: int = 1,
        page_size: int = 20,
    ) -> dict[str, Any]:
        """Get requests for a specific user.
        
        Args:
            user_id: User ID to get requests for
            start_date: Filter requests after this date
            end_date: Filter requests before this date
            status: Filter by request status (integer)
            page: Page number for pagination
            page_size: Number of items per page
            
        Returns:
            Dict containing request data and pagination info
        """
        params = {
            "take": page_size,
            "skip": (page - 1) * page_size,
        }
        
        if status:
            params["status"] = status
            
        # Remove None values to avoid API errors
        params = {k: v for k, v in params.items() if v is not None}
        
        response = await self.get(f"{OVERSEERR_USER_ENDPOINT}/{user_id}/requests", params)
        
        # Filter results by date if needed
        if start_date or end_date:
            filtered_results = []
            for request in response.get("results", []):
                request_date = datetime.fromisoformat(request["createdAt"].replace("Z", "+00:00"))
                
                # Convert naive datetimes to UTC
                if start_date and start_date.tzinfo is None:
                    start_date = start_date.replace(tzinfo=timezone.utc)
                if end_date and end_date.tzinfo is None:
                    end_date = end_date.replace(tzinfo=timezone.utc)
                
                if start_date and request_date < start_date:
                    continue
                if end_date and request_date > end_date:
                    continue
                    
                filtered_results.append(request)
                
            response["results"] = filtered_results
            
        return response
    
    async def get_all_user_requests(
        self,
        user_id: UserId,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
        status: Optional[int] = None,
    ) -> list[dict[str, Any]]:
        """Get all requests for a user, handling pagination automatically.
        
        Args:
            user_id: User ID to get requests for
            start_date: Filter requests after this date
            end_date: Filter requests before this date
            status: Filter by request status (integer)
            
        Returns:
            List of all request data
        """
        page = 1
        all_requests = []
        
        while True:
            response = await self.get_user_requests(
                user_id,
                start_date,
                end_date,
                status,
                page=page,
            )
            
            requests = response.get("results", [])
            if not requests:
                break
                
            all_requests.extend(requests)
            
            # Check if we've reached the last page
            if len(requests) < response.get("pageSize", 20):
                break
                
            page += 1
            
        return all_requests
    
    async def get_request_details(self, request_id: int) -> dict[str, Any]:
        """Get detailed information about a specific request.
        
        Args:
            request_id: ID of the request to get details for
            
        Returns:
            Dict containing request details
        """
        return await self.get(f"{OVERSEERR_USER_ENDPOINT}/request/{request_id}")
    
    async def modify_user_quota(
        self,
        user_id: UserId,
        movie_quota: Optional[int] = None,
        tv_quota: Optional[int] = None,
    ) -> dict[str, Any]:
        """Modify a user's request quota.
        
        Args:
            user_id: User ID to modify quota for
            movie_quota: New movie request quota
            tv_quota: New TV show request quota
            
        Returns:
            Dict containing updated user quota information
        """
        data = {}
        if movie_quota is not None:
            data["movieQuota"] = movie_quota
        if tv_quota is not None:
            data["tvQuota"] = tv_quota
            
        return await self.put(f"{OVERSEERR_USER_ENDPOINT}/{user_id}/settings/quota", json_data=data)
    
    async def get_user(self, user_id: UserId) -> dict[str, Any]:
        """Get user information from Overseerr.
        
        Args:
            user_id: User ID to get information for
            
        Returns:
            Dict containing user information
        """
        return await self.get(f"{OVERSEERR_USER_ENDPOINT}/{user_id}")
    
    async def get_users(
        self,
        take: int = 20,
        skip: int = 0,
    ) -> dict[str, Any]:
        """Get list of users from Overseerr.
        
        Args:
            take: Number of users to get (page size)
            skip: Number of users to skip (for pagination)
            
        Returns:
            Dict containing list of users and pagination info
        """
        params = {
            "take": take,
            "skip": skip,
        }
        return await self.get(f"{OVERSEERR_USER_ENDPOINT}", params)
    
    async def get_all_users(self) -> list[dict[str, Any]]:
        """Get all users from Overseerr, handling pagination automatically.
        
        Returns:
            List of all users
        """
        all_users = []
        skip = 0
        take = 20
        
        while True:
            response = await self.get_users(take=take, skip=skip)
            users = response.get("results", [])
            if not users:
                break
                
            all_users.extend(users)
            
            # Check if we've reached the last page
            if len(users) < take:
                break
                
            skip += take
            
        return all_users
    
    async def get_user_request_limits(self, user_id: UserId) -> dict[str, Any]:
        """Get user request limits from Overseerr.
        
        Args:
            user_id: User ID to get request limits for
            
        Returns:
            Dict containing user request limits
        """
        return await self.get(f"{OVERSEERR_USER_ENDPOINT}/{user_id}/quotas")
    
    async def get_settings(self) -> dict[str, Any]:
        """Get global settings from Overseerr.
        
        Returns:
            Dict containing global settings
        """
        return await self.get("/api/v1/settings/main")
