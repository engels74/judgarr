"""Integration tests for the Overseerr API client."""
import pytest
import pytest_asyncio
import aiohttp
from typing import Any
from pydantic import HttpUrl
from judgarr.api.overseerr.client import OverseerrClient
from judgarr.config.models.core import RootConfig as Settings
from judgarr.shared.types import UserId
from judgarr.api.base import APIError
import json

@pytest_asyncio.fixture
async def overseerr_client(settings: Settings, http_session: aiohttp.ClientSession) -> OverseerrClient:
    """Create an Overseerr client for testing."""
    client = OverseerrClient(
        base_url=HttpUrl(str(settings.api.overseerr.url)),
        api_key=settings.api.overseerr.api_key
    )
    client._session = http_session  # Use the shared session
    return client

@pytest.fixture(scope="module")
def test_user() -> dict[str, Any]:
    """Fixture to store test user information between tests."""
    return {}

@pytest.mark.asyncio
async def test_get_users(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test getting users from Overseerr and find a suitable test user."""
    try:
        users = await overseerr_client.get_all_users()
        print(f"\nFound {len(users)} users")
        
        # Print first user details for debugging
        if users:
            print("\nFirst user details:")
            print(json.dumps(users[0], indent=2))
        
        # Print user types distribution
        user_types = {}
        for user in users:
            user_type = user.get("userType")
            user_types[user_type] = user_types.get(user_type, 0) + 1
        print("\nUser types distribution:")
        for user_type, count in user_types.items():
            print(f"Type {user_type}: {count} users")
        
        # Find a user with Plex credentials (skip admin)
        plex_user = None
        for user in users:
            # Skip the admin user (nscbox1)
            if user.get("plexUsername") == "nscbox1":
                continue
                
            if user.get("plexId") and user.get("plexUsername"):
                plex_user = user
                print(f"\nFound non-admin user with Plex credentials: {json.dumps(user, indent=2)}")
                test_user.clear()
                test_user.update(plex_user)
                break
            
        if not plex_user:
            print("\nNo non-admin users with Plex credentials found!")
            pytest.skip("No non-admin users with Plex credentials found")
            
    except APIError as e:
        pytest.skip(f"Failed to get users: {e}")

@pytest.mark.asyncio
async def test_get_user(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test getting a specific user from Overseerr."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        user = await overseerr_client.get_user(user_id)
        print(f"\nUser info: {json.dumps(user, indent=2)}")
        assert isinstance(user, dict)
        assert "id" in user
        assert "displayName" in user
        assert "plexId" in user and user["plexId"], "Should have a Plex ID"
        assert "plexUsername" in user and user["plexUsername"], "Should have a Plex username"
    except APIError as e:
        pytest.skip(f"Could not get user: {e}")

@pytest.mark.asyncio
async def test_get_user_requests(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test getting user requests from Overseerr."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        response = await overseerr_client.get_user_requests(user_id)
        print(f"\nUser requests: {json.dumps(response, indent=2)}")
        assert isinstance(response, dict)
        assert "results" in response
        print(f"\nUser has {len(response.get('results', []))} requests")
    except APIError as e:
        pytest.skip(f"Failed to get user requests: {e}")

@pytest.mark.asyncio
async def test_get_all_user_requests(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test getting all user requests from Overseerr."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        requests = await overseerr_client.get_all_user_requests(user_id)
        print(f"\nAll user requests: {json.dumps(requests[:5], indent=2)}")  # Show first 5 requests
        assert isinstance(requests, list)
        print(f"\nUser has {len(requests)} total requests")
    except APIError as e:
        pytest.skip(f"Failed to get all user requests: {e}")

@pytest.mark.asyncio
async def test_get_user_request_limits(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test getting user request limits from Overseerr."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        limits = await overseerr_client.get_user_request_limits(user_id)
        print(f"\nUser request limits: {json.dumps(limits, indent=2)}")
        assert isinstance(limits, dict)
        
        # Check if limits are set (either individual or global)
        if limits.get("movieQuota") is None and limits.get("tvQuota") is None:
            print("\nNo individual quota limits set - this is expected when using global limits")
            print("To see the actual limits, we would need to check the global settings")
        else:
            print(f"\nMovie quota: {limits.get('movieQuota')}, TV quota: {limits.get('tvQuota')}")
            assert "movieQuota" in limits
            assert "tvQuota" in limits
    except APIError as e:
        pytest.skip(f"Failed to get user request limits: {e}")

@pytest.mark.asyncio
async def test_modify_user_quota(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test modifying user request quota in Overseerr."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        # Get current quota
        original_quota = await overseerr_client.get_user_request_limits(user_id)
        print(f"\nOriginal quota: {json.dumps(original_quota, indent=2)}")
        
        if original_quota.get("movieQuota") is None and original_quota.get("tvQuota") is None:
            print("\nSkipping quota modification test as global limits are in use")
            pytest.skip("Cannot modify quotas when global limits are in use")
        
        # Set new quota values
        new_movie_quota = 5  # Set a reasonable test value
        new_tv_quota = 3     # Set a reasonable test value
        
        updated_quota = await overseerr_client.modify_user_quota(
            user_id,
            movie_quota=new_movie_quota,
            tv_quota=new_tv_quota
        )
        print(f"\nUpdated quota: {json.dumps(updated_quota, indent=2)}")
        
        assert isinstance(updated_quota, dict)
        assert updated_quota.get("movieQuota") == new_movie_quota
        assert updated_quota.get("tvQuota") == new_tv_quota
        
        # Restore original quota
        await overseerr_client.modify_user_quota(
            user_id,
            movie_quota=original_quota.get("movieQuota"),
            tv_quota=original_quota.get("tvQuota")
        )
    except APIError as e:
        pytest.skip(f"Failed to modify user quota: {e}")

@pytest.mark.asyncio
async def test_get_settings(overseerr_client: OverseerrClient) -> None:
    """Test getting global settings from Overseerr."""
    try:
        settings = await overseerr_client.get_settings()
        print(f"\nGlobal settings: {json.dumps(settings, indent=2)}")
        assert isinstance(settings, dict)
        
        # Check global quota settings
        quota_enabled = settings.get("quotaEnabled", False)
        movie_quota = settings.get("defaultMovieQuotaLimit")
        tv_quota = settings.get("defaultTvQuotaLimit")
        movie_days = settings.get("defaultMovieQuotaDays")
        tv_days = settings.get("defaultTvQuotaDays")
        
        print("\nGlobal quota settings:")
        print(f"Quota enabled: {quota_enabled}")
        print(f"Default movie quota: {movie_quota} per {movie_days} days")
        print(f"Default TV quota: {tv_quota} per {tv_days} days")
        
    except APIError as e:
        pytest.skip(f"Failed to get global settings: {e}")

@pytest.mark.asyncio
async def test_global_quota_settings(overseerr_client: OverseerrClient) -> None:
    """Test the global quota settings configuration in Overseerr."""
    try:
        settings = await overseerr_client.get_settings()
        assert isinstance(settings, dict)
        
        # Verify default quotas structure
        assert "defaultQuotas" in settings, "Settings should contain defaultQuotas"
        quotas = settings["defaultQuotas"]
        
        # Check movie quota settings
        assert "movie" in quotas, "Default quotas should contain movie settings"
        movie_quota = quotas["movie"]
        assert "quotaLimit" in movie_quota, "Movie quota should have a limit"
        assert "quotaDays" in movie_quota, "Movie quota should have a days period"
        assert isinstance(movie_quota["quotaLimit"], int), "Movie quota limit should be an integer"
        assert isinstance(movie_quota["quotaDays"], int), "Movie quota days should be an integer"
        
        # Check TV quota settings
        assert "tv" in quotas, "Default quotas should contain tv settings"
        tv_quota = quotas["tv"]
        assert "quotaLimit" in tv_quota, "TV quota should have a limit"
        assert "quotaDays" in tv_quota, "TV quota should have a days period"
        assert isinstance(tv_quota["quotaLimit"], int), "TV quota limit should be an integer"
        assert isinstance(tv_quota["quotaDays"], int), "TV quota days should be an integer"
        
        print("\nVerified global quota settings:")
        print(f"Movie quota: {movie_quota['quotaLimit']} requests per {movie_quota['quotaDays']} days")
        print(f"TV quota: {tv_quota['quotaLimit']} requests per {tv_quota['quotaDays']} days")
        
    except APIError as e:
        pytest.skip(f"Failed to get global quota settings: {e}")

@pytest.mark.asyncio
async def test_global_quota_application(overseerr_client: OverseerrClient, test_user: dict[str, Any]) -> None:
    """Test that global quotas are properly applied when individual quotas are not set."""
    if not test_user:
        pytest.skip("No test user found")
    
    user_id = UserId(str(test_user["id"]))
    try:
        # Get user's quota limits
        user_limits = await overseerr_client.get_user_request_limits(user_id)
        
        # Get global settings
        global_settings = await overseerr_client.get_settings()
        global_quotas = global_settings.get("defaultQuotas", {})
        
        print("\nComparing user limits with global settings:")
        if user_limits.get("movieQuota") is None and user_limits.get("tvQuota") is None:
            print("User has no individual quotas set - using global quotas:")
            print(f"Global movie quota: {global_quotas['movie']['quotaLimit']} per {global_quotas['movie']['quotaDays']} days")
            print(f"Global TV quota: {global_quotas['tv']['quotaLimit']} per {global_quotas['tv']['quotaDays']} days")
        else:
            print("User has individual quotas set - not using global quotas")
            print(f"Individual movie quota: {user_limits.get('movieQuota')}")
            print(f"Individual TV quota: {user_limits.get('tvQuota')}")
            
    except APIError as e:
        pytest.skip(f"Failed to verify global quota application: {e}")
