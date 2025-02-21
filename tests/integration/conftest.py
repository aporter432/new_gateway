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
import warnings
from typing import AsyncGenerator

# Third-party imports
import boto3
import prometheus_client
import pytest
import redis.asyncio as redis
from httpx import AsyncClient, HTTPError

# Local imports
from infrastructure.database.models.base import Base
from infrastructure.database.session import database_url
from prometheus_client import CollectorRegistry
from redis.asyncio.client import Redis as AsyncRedis
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

# Environment Configuration
REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "15"))
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localstack:4566")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")


# Docker Environment Checks
def is_running_in_docker() -> bool:
    """Check if we're running inside a Docker container."""
    # Try .dockerenv first, then cgroup
    if os.path.exists("/.dockerenv"):
        return True

    try:
        with open("/proc/1/cgroup", "r", encoding="utf-8") as f:
            return "docker" in f.read()
    except (OSError, IOError):
        return False


@pytest.fixture(autouse=True)
def verify_docker_environment():
    """Verify tests are running in Docker environment."""
    if not is_running_in_docker():
        pytest.fail(
            "\n"
            "🐳 Docker Environment Required 🐳\n"
            "These integration tests must run inside Docker containers.\n"
            "Please run tests using:\n"
            "  docker-compose run test pytest tests/integration\n"
            "\n"
            "For more information, see:\n"
            "  src/DOCS/ENVIRONMENT/testing/test_setup.md"
        )


# Database Fixtures
@pytest.fixture(scope="function")
async def db_engine():
    """Create a new engine for each test function."""
    engine = create_async_engine(database_url)
    yield engine
    await engine.dispose()


@pytest.fixture(scope="function")
async def db_connection(db_engine) -> AsyncGenerator[AsyncConnection, None]:
    """Create a database connection for each test.

    Creates all tables before tests and drops them after.
    """
    async with db_engine.connect() as conn:
        await conn.run_sync(Base.metadata.create_all)
        yield conn
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture()
async def db_session(db_connection: AsyncConnection) -> AsyncGenerator[AsyncSession, None]:
    """Provide a database session for test isolation.

    Args:
        db_connection: Database connection from the function-scoped fixture

    Yields:
        AsyncSession: Database session that's cleaned up after each test
    """
    async with AsyncSession(bind=db_connection, expire_on_commit=False) as session:
        # Start with a clean slate for each test
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()

        yield session

        # Clean up after the test
        await session.rollback()
        for table in reversed(Base.metadata.sorted_tables):
            await session.execute(table.delete())
        await session.commit()


# Redis Fixtures
@pytest.fixture(scope="function")
async def redis_client() -> AsyncGenerator[AsyncRedis, None]:
    """Create a Redis client for testing."""
    client = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )

    try:
        await client.ping()
    except redis.ConnectionError as e:
        pytest.fail(f"Redis connection failed: {e}")

    yield client

    # Cleanup
    try:
        await client.aclose()  # type: ignore # Redis type hints don't include aclose
    except redis.RedisError as e:
        warnings.warn(f"Error during Redis cleanup: {e}")


@pytest.fixture(autouse=True)
async def clean_redis(redis_client: redis.Redis):
    """Clean Redis test database before each test."""
    await redis_client.flushdb()


# AWS Service Fixtures
@pytest.fixture(scope="session")
def dynamodb_client():
    """Create a DynamoDB client for testing using LocalStack."""
    return boto3.client(
        "dynamodb",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


@pytest.fixture(scope="session")
def sqs_client():
    """Create an SQS client for testing using LocalStack."""
    return boto3.client(
        "sqs",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


@pytest.fixture(scope="session")
def cloudwatch_client():
    """Create a CloudWatch client for testing using LocalStack."""
    return boto3.client(
        "cloudwatch",
        endpoint_url=AWS_ENDPOINT_URL,
        region_name=AWS_REGION,
        aws_access_key_id=AWS_ACCESS_KEY,
        aws_secret_access_key=AWS_SECRET_KEY,
    )


# Metrics Fixtures
@pytest.fixture
def metrics_registry():
    """Create a clean metrics registry for each test."""
    registry = CollectorRegistry()
    yield registry
    # Intentionally access protected member for test cleanup
    for collector in list(registry._collector_to_names.keys()):  # pylint: disable=protected-access
        registry.unregister(collector)


@pytest.fixture
def mock_metrics(monkeypatch):
    """Mock the metrics registry for integration tests."""
    # Store the original registry
    original_registry = prometheus_client.REGISTRY

    # Create a new registry for the test and patch it
    test_registry = CollectorRegistry()
    monkeypatch.setattr(prometheus_client, "REGISTRY", test_registry)
    yield test_registry

    # Restore the original registry after test
    monkeypatch.setattr(prometheus_client, "REGISTRY", original_registry)

    # Intentionally access protected member for test cleanup
    for collector in list(
        test_registry._collector_to_names.keys()
    ):  # pylint: disable=protected-access
        test_registry.unregister(collector)


# Health Check Fixtures
@pytest.fixture(autouse=True)
async def verify_service_health(http_client: AsyncClient, request: pytest.FixtureRequest):
    """Verify all required services are healthy before running tests."""
    # Check Redis - always needed
    redis_client: AsyncRedis = redis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
    )
    try:
        await redis_client.ping()
    except redis.ConnectionError as e:
        pytest.fail(f"Redis health check failed: {e}")
    finally:
        await redis_client.aclose()  # type: ignore # Redis type hints don't include aclose

    # Only check LocalStack if test needs it
    if "localstack" in request.keywords:
        try:
            response = await http_client.get(f"{AWS_ENDPOINT_URL}/_localstack/health")
            if response.status_code != 200:
                pytest.skip("LocalStack not available - skipping test")
        except HTTPError as e:
            pytest.skip(f"LocalStack not available - skipping test: {e}")
