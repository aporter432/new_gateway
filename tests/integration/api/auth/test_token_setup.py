"""Integration tests for token setup and management."""

import asyncio
import logging
import time
from datetime import datetime
from unittest.mock import patch

import pytest
from redis.asyncio import Redis

from Protexis_Command.core.settings.app_settings import Settings
from Protexis_Command.protocol.ogx.auth.manager import OGxAuthManager, TokenMetadata
from tests.integration.fixtures.mock_responses import OGxMockResponses

# Set up basic logging for tests
logger = logging.getLogger("test_token_setup")
logger.setLevel(logging.INFO)
handler = logging.StreamHandler()
handler.setFormatter(logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s"))
logger.addHandler(handler)


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_redis
class TestTokenManagement:
    """Test token management functionality."""

    @pytest.fixture
    async def auth_manager(self, settings: Settings, redis_client: Redis) -> OGxAuthManager:
        """Create auth manager for tests."""
        manager = OGxAuthManager(settings, redis_client)
        logger.info("Created auth manager for test", extra={"test_id": id(manager)})
        return manager

    async def test_token_expiry_handling(self, auth_manager: OGxAuthManager):
        """Test handling of token expiration."""
        # Store an expired token
        now = datetime.now().timestamp()
        expired_metadata = TokenMetadata(
            token="expired_token",
            created_at=now - 7200,  # 2 hours ago
            expires_at=now - 3600,  # 1 hour ago
            last_used=now - 3600,
            validation_count=0,
        )
        await auth_manager._store_token_metadata(expired_metadata)
        logger.info(
            "Stored expired token metadata",
            extra={
                "test_id": id(auth_manager),
                "token": expired_metadata.token,
                "expires_at": expired_metadata.expires_at,
            },
        )

        # Get new token since current is expired
        with patch(
            "httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("new_token")
        ):
            token = await auth_manager.get_valid_token()
            logger.info(
                "Got token after expiry",
                extra={
                    "test_id": id(auth_manager),
                    "token": token,
                },
            )
            assert token != "expired_token"
            assert token == "new_token"

            # Verify metadata was updated
            metadata = await auth_manager._get_token_metadata()
            assert metadata is not None
            assert metadata.token != "expired_token"
            assert metadata.expires_at > now

    async def test_token_refresh_conditions(self, auth_manager: OGxAuthManager):
        """Test different token refresh conditions."""
        # Get initial token
        with patch(
            "httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("initial_token")
        ):
            token = await auth_manager.get_valid_token()
            assert token == "initial_token"

            # Force refresh should get new token
            with patch(
                "httpx.AsyncClient.post",
                return_value=OGxMockResponses.token_success("refreshed_token"),
            ):
                new_token = await auth_manager.get_valid_token(force_refresh=True)
                assert new_token != token
                assert new_token == "refreshed_token"

                # Get token info and verify refresh
                info = await auth_manager.get_token_info()
                assert info is not None
                assert float(info["created_at"]) > time.time() - 5  # Created within last 5 seconds

    async def test_concurrent_token_access(self, auth_manager: OGxAuthManager):
        """Test concurrent access to token."""
        # Create multiple concurrent token requests
        with patch(
            "httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("shared_token")
        ):
            token = await auth_manager.get_valid_token()
            assert token == "shared_token"

            # Create concurrent validation requests
            with patch("httpx.AsyncClient.get", return_value=OGxMockResponses.validation_success()):
                validation_tasks = [
                    auth_manager.validate_token({"Authorization": f"Bearer {token}"})
                    for _ in range(5)
                ]
                results = await asyncio.gather(*validation_tasks)

                # All validations should succeed
                assert all(results)

                # Verify metadata shows multiple uses
                info = await auth_manager.get_token_info()
                assert info is not None
                assert info["validation_count"] >= 5

    async def test_token_metadata_updates(self, auth_manager: OGxAuthManager):
        """Test token metadata is properly updated."""
        # Get initial token
        with patch(
            "httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("test_token")
        ):
            token = await auth_manager.get_valid_token()
            initial_info = await auth_manager.get_token_info()
            assert initial_info is not None

            # Wait briefly
            await asyncio.sleep(0.1)

            # Use token multiple times
            with patch("httpx.AsyncClient.get", return_value=OGxMockResponses.validation_success()):
                for i in range(3):
                    await auth_manager.validate_token({"Authorization": f"Bearer {token}"})
                    await asyncio.sleep(0.1)

                # Check metadata updates
                final_info = await auth_manager.get_token_info()
                assert final_info is not None
                assert final_info["validation_count"] >= initial_info["validation_count"] + 3
                assert float(final_info["last_used"]) > float(initial_info["last_used"])
                assert float(final_info["last_validated"]) > float(initial_info["last_used"])


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.requires_redis
async def test_token_lifecycle(settings: Settings, redis_client: Redis):
    """Test complete token lifecycle including storage and metadata."""
    auth_manager = OGxAuthManager(settings, redis_client)

    # === Initial Token Acquisition ===
    with patch(
        "httpx.AsyncClient.post", return_value=OGxMockResponses.token_success("lifecycle_token")
    ):
        token = await auth_manager.get_valid_token()
        assert token is not None
        assert token == "lifecycle_token"

        # Get initial metadata and verify structure
        initial_info = await auth_manager.get_token_info()
        assert initial_info is not None
        assert "token" in initial_info
        assert "created_at" in initial_info
        assert "expires_at" in initial_info
        assert "last_used" in initial_info
        assert "validation_count" in initial_info

        # === Token Validation ===
        with patch("httpx.AsyncClient.get", return_value=OGxMockResponses.validation_success()):
            auth_header = await auth_manager.get_auth_header()
            is_valid = await auth_manager.validate_token(auth_header)
            assert is_valid

            # Verify validation metadata updates
            validation_info = await auth_manager.get_token_info()
            assert validation_info is not None
            assert validation_info["validation_count"] > initial_info["validation_count"]
            assert validation_info["last_validated"] is not None
            assert float(validation_info["last_validated"]) >= float(initial_info["last_used"])

            # === Token Reuse ===
            # Sleep briefly to ensure timestamp difference
            await asyncio.sleep(0.1)
            reused_token = await auth_manager.get_valid_token()
            assert reused_token == token

            # Verify usage metadata updates
            usage_info = await auth_manager.get_token_info()
            assert usage_info is not None
            assert float(usage_info["last_used"]) > float(initial_info["last_used"])

            # === Token Refresh ===
            with patch(
                "httpx.AsyncClient.post",
                return_value=OGxMockResponses.token_success("refreshed_token"),
            ):
                new_token = await auth_manager.get_valid_token(force_refresh=True)
                assert new_token is not None
                assert new_token != token
                assert new_token == "refreshed_token"

                # Verify token remains valid
                with patch(
                    "httpx.AsyncClient.get", return_value=OGxMockResponses.validation_success()
                ):
                    auth_header = await auth_manager.get_auth_header()
                    is_valid = await auth_manager.validate_token(auth_header)
                    assert is_valid

                # === Token Invalidation ===
                await auth_manager.invalidate_token()
                metadata = await auth_manager._get_token_metadata()
                assert metadata is None


if __name__ == "__main__":
    asyncio.run(test_token_lifecycle())
