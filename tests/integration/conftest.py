"""Integration test fixtures and configuration.

This module provides fixtures specifically for integration tests that require:
- Docker container services
- Real service connections
- Integration-specific environment setup

Note on Redis cleanup:
We use client.aclose() with type ignore comments because:
1. aclose() is the recommended method in Redis async client
2. close() is deprecated since version 5.0.1
3. Type hints don't yet include aclose() - this may be fixed in future Redis versions
"""

# Standard library imports
import os
import socket
from dataclasses import dataclass
from typing import AsyncGenerator, Optional

# Third-party imports
import boto3
import prometheus_client
import pytest
import pytest_asyncio
import redis.asyncio as aioredis
from httpx import AsyncClient
from prometheus_client import CollectorRegistry
from redis.asyncio.client import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

# Local imports
from Protexis_Command.core.app_settings import Settings, get_settings
from Protexis_Command.infrastructure.database.models.base import Base
from Protexis_Command.infrastructure.database.session import database_url


@dataclass
class TestEnvironment:
    """Test environment configuration and detection."""

    docker_available: bool
    redis_available: bool
    postgres_available: bool
    aws_mock_available: bool
    redis_url: str
    postgres_url: str
    aws_endpoint: Optional[str]

    @classmethod
    def detect(cls) -> "TestEnvironment":
        """Detect available testing infrastructure."""
        docker = is_running_in_docker()

        # Check Redis availability
        redis_host = os.getenv("REDIS_HOST", "ogx_gateway_redis")
        redis_available = is_service_available(redis_host, 6379)

        # Check Postgres availability
        db_host = os.getenv("POSTGRES_HOST", "ogx_gateway_db")
        postgres_available = is_service_available(db_host, 5432)

        # Check AWS mock availability
        aws_host = os.getenv("AWS_MOCK_HOST", "ogx_gateway_aws_mock")
        aws_available = is_service_available(aws_host, 4566)

        return cls(
            docker_available=docker,
            redis_available=redis_available,
            postgres_available=postgres_available,
            aws_mock_available=aws_available,
            redis_url=f"redis://{redis_host}:6379",
            postgres_url=f"postgresql://{db_host}:5432",
            aws_endpoint=f"http://{aws_host}:4566" if aws_available else None,
        )


def is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    return os.path.exists("/.dockerenv") or "docker" in open("/proc/1/cgroup").read()


def is_service_available(host: str, port: int) -> bool:
    """Check if a service is available at host:port."""
    try:
        with socket.create_connection((host, port), timeout=1):
            return True
    except (socket.timeout, socket.error):
        return False


def pytest_configure(config):
    """Configure pytest for integration testing."""
    # Register test markers
    markers = [
        ("integration", "mark test as integration test"),
        ("requires_docker", "mark test as requiring docker"),
        ("requires_redis", "mark test as requiring Redis"),
        ("requires_db", "mark test as requiring database"),
        ("requires_aws", "mark test as requiring AWS services"),
        ("live_api", "mark test as requiring live API access"),
    ]
    for marker, help_text in markers:
        config.addinivalue_line("markers", f"{marker}: {help_text}")

    # Ensure we're in test mode
    os.environ["TESTING"] = "true"


def pytest_runtest_setup(item):
    """Skip tests based on available infrastructure."""
    env = TestEnvironment.detect()

    # Check Docker requirement
    if "requires_docker" in item.keywords and not env.docker_available:
        pytest.skip("Test requires Docker")

    # Check Redis requirement
    if "requires_redis" in item.keywords and not env.redis_available:
        pytest.skip("Test requires Redis")

    # Check Database requirement
    if "requires_db" in item.keywords and not env.postgres_available:
        pytest.skip("Test requires PostgreSQL")

    # Check AWS mock requirement
    if "requires_aws" in item.keywords and not env.aws_mock_available:
        pytest.skip("Test requires AWS mock services")


@pytest.fixture(scope="session")
def test_environment() -> TestEnvironment:
    """Provide test environment information to tests."""
    return TestEnvironment.detect()


@pytest.fixture(scope="session")
def settings() -> Settings:
    """Provide application settings."""
    return get_settings()


@pytest_asyncio.fixture
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Provide an HTTP client configured for integration tests."""
    async with AsyncClient(
        verify=True,  # Enable SSL verification for HTTPS
        timeout=30.0,  # Longer timeout for integration tests
        follow_redirects=True,  # Follow redirects automatically
    ) as client:
        yield client


@pytest.fixture(scope="function")
async def db_engine(test_environment: TestEnvironment):
    """Create a new engine for each test function."""
    if not test_environment.postgres_available:
        pytest.skip("Database not available")

    engine = create_async_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_connection(db_engine) -> AsyncGenerator[AsyncConnection, None]:
    """Create a database connection for each test."""
    async with db_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for test isolation."""
    async with AsyncSession(bind=db_connection, expire_on_commit=False) as session:
        # Start with a clean slate
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()
        yield session
        # Clean up
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


@pytest_asyncio.fixture(scope="function")
async def redis_client(test_environment: TestEnvironment) -> AsyncGenerator[AsyncRedis, None]:
    """Provide Redis client for the test session."""
    if not test_environment.redis_available:
        pytest.skip("Redis not available")

    redis = aioredis.Redis.from_url(
        test_environment.redis_url,
        decode_responses=True,
        db=int(os.getenv("REDIS_DB", "15")),  # Use DB 15 for testing
    )

    try:
        await redis.ping()  # Verify connection
        yield redis
    finally:
        await redis.aclose()  # type: ignore # Redis type hints don't include aclose


@pytest_asyncio.fixture(autouse=True)
async def cleanup_redis(redis_client: AsyncRedis):
    """Clean up Redis test database before and after each test."""
    patterns = [
        "OGx:auth:token*",  # Auth tokens and metadata
        "OGx:session:*",  # Session data
        "test:*",  # Test-specific keys
        "mock:*",  # Mock data keys
    ]

    try:
        # Clean up before test
        for pattern in patterns:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
        yield
        # Clean up after test
        for pattern in patterns:
            keys = await redis_client.keys(pattern)
            if keys:
                await redis_client.delete(*keys)
    except Exception as e:
        pytest.fail(f"Redis cleanup failed: {str(e)}")


@pytest.fixture(scope="session")
def aws_clients(test_environment: TestEnvironment):
    """Provide AWS service clients."""
    if not test_environment.aws_mock_available:
        pytest.skip("AWS mock services not available")

    return {
        "dynamodb": boto3.client(
            "dynamodb",
            endpoint_url=test_environment.aws_endpoint,
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        ),
        "sqs": boto3.client(
            "sqs",
            endpoint_url=test_environment.aws_endpoint,
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        ),
        "cloudwatch": boto3.client(
            "cloudwatch",
            endpoint_url=test_environment.aws_endpoint,
            region_name="us-east-1",
            aws_access_key_id="test",
            aws_secret_access_key="test",
        ),
    }


@pytest.fixture
def metrics_registry():
    """Create a clean metrics registry for each test."""
    registry = CollectorRegistry()
    yield registry
    for collector in list(registry._collector_to_names.keys()):  # pylint: disable=protected-access
        registry.unregister(collector)


@pytest.fixture
def mock_metrics(monkeypatch):
    """Mock the metrics registry for integration tests."""
    test_registry = CollectorRegistry()
    original_registry = prometheus_client.REGISTRY
    monkeypatch.setattr(prometheus_client, "REGISTRY", test_registry)
    yield test_registry
    monkeypatch.setattr(prometheus_client, "REGISTRY", original_registry)
    for collector in list(
        test_registry._collector_to_names.keys()
    ):  # pylint: disable=protected-access
        test_registry.unregister(collector)
