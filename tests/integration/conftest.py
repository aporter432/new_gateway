"""Root level fixtures for integration testing.

This module provides fixtures for managing test environment services including:
- Redis connection and state management
- PostgreSQL test database
- LocalStack AWS services
- Metrics collection
"""

# pylint: disable=protected-access
# Accessing protected members is expected in test fixtures for cleanup

# MOVE TO: /tests/integration/conftest.py - Integration test docstring

# MOVE TO: /tests/integration/conftest.py - Integration-specific imports
import os
from typing import AsyncGenerator

import aioredis
import boto3
import httpx
import prometheus_client
import pytest
from httpx import AsyncClient
from prometheus_client import CollectorRegistry
from sqlalchemy.ext.asyncio import AsyncConnection, AsyncSession, create_async_engine

from infrastructure.database.models.base import Base
from infrastructure.database.session import database_url

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))
REDIS_DB = int(os.getenv("REDIS_DB", "15"))  # Use DB 15 for testing
REDIS_PASSWORD = os.getenv("REDIS_PASSWORD", "")

AWS_ENDPOINT_URL = os.getenv("AWS_ENDPOINT_URL", "http://localhost:4566")
AWS_REGION = os.getenv("AWS_REGION", "us-east-1")
AWS_ACCESS_KEY = os.getenv("AWS_ACCESS_KEY_ID", "test")
AWS_SECRET_KEY = os.getenv("AWS_SECRET_ACCESS_KEY", "test")


# MOVE TO: /tests/integration/conftest.py - Redis integration test fixture
@pytest.fixture(scope="session")
async def redis_client() -> AsyncGenerator[aioredis.Redis, None]:
    """Create a Redis client for testing.

    This fixture provides a Redis connection that:
    - Uses a dedicated test database
    - Cleans up after each test
    - Handles connection management
    """
    client = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
        decode_responses=True,
    )

    # Verify connection
    try:
        await client.ping()
    except aioredis.ConnectionError as e:
        pytest.fail(f"Redis connection failed: {e}")

    yield client

    # Cleanup
    await client.flushdb()  # Clean test database
    await client.close()


# MOVE TO: /tests/integration/conftest.py - AWS service fixtures
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


# MOVE TO: /tests/integration/conftest.py - Redis cleanup fixture
@pytest.fixture(autouse=True)
async def clean_redis(redis_client: aioredis.Redis):
    """Clean Redis test database before each test."""
    await redis_client.flushdb()


# MOVE TO: /tests/integration/conftest.py - Metrics fixtures
@pytest.fixture
def metrics_registry():
    """Create a clean metrics registry for each test.

    This prevents metrics from bleeding between tests and allows
    verification of specific metric collection.
    """
    registry = CollectorRegistry()
    yield registry
    # Clear all collectors from the registry after the test
    for collector in list(registry._collector_to_names.keys()):  # pylint: disable=protected-access
        registry.unregister(collector)


# MOVE TO: /tests/conftest.py (ROOT) - HTTP client could be needed by any test type
@pytest.fixture(scope="session")
async def http_client() -> AsyncGenerator[AsyncClient, None]:
    """Create an async HTTP client for testing.

    This client can be used for making requests to the OGWS proxy
    or other HTTP endpoints during testing.
    """
    async with AsyncClient() as client:
        yield client


# MOVE TO: /tests/conftest.py (ROOT) - Environment variables needed by all test types
@pytest.fixture(autouse=True)
def mock_env_vars(monkeypatch):
    """Set up environment variables for testing.

    This ensures consistent environment configuration across all tests.
    """
    test_env = {
        "ENVIRONMENT": "test",
        "REDIS_HOST": REDIS_HOST,
        "REDIS_PORT": str(REDIS_PORT),
        "REDIS_DB": str(REDIS_DB),
        "AWS_ENDPOINT_URL": AWS_ENDPOINT_URL,
        "AWS_REGION": AWS_REGION,
        "AWS_ACCESS_KEY_ID": AWS_ACCESS_KEY,
        "AWS_SECRET_ACCESS_KEY": AWS_SECRET_KEY,
        "OGWS_BASE_URL": "http://proxy:8080/api/v1.0",
        "OGWS_CLIENT_ID": "70000934",
        "OGWS_CLIENT_SECRET": "password",
    }

    for key, value in test_env.items():
        monkeypatch.setenv(key, value)


# MOVE TO: /tests/integration/conftest.py - Metrics mock specific to integration tests
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

    # Clear all collectors from the test registry
    for collector in list(test_registry._collector_to_names.keys()):  # pylint: disable=protected-access
        test_registry.unregister(collector)


# MOVE TO: /tests/integration/conftest.py - Integration service health checks
@pytest.fixture(autouse=True)
async def verify_service_health(http_client: AsyncClient):
    """Verify all required services are healthy before running tests.

    This helps catch configuration or connection issues early.
    """
    # Check Redis
    redis = aioredis.Redis(
        host=REDIS_HOST,
        port=REDIS_PORT,
        db=REDIS_DB,
        password=REDIS_PASSWORD,
    )
    try:
        await redis.ping()
    except aioredis.ConnectionError as e:
        pytest.fail(f"Redis health check failed: {e}")
    finally:
        await redis.close()

    # Check LocalStack services
    try:
        response = await http_client.get(f"{AWS_ENDPOINT_URL}/_localstack/health")
        if response.status_code != 200:
            pytest.fail("LocalStack health check failed")
    except httpx.HTTPStatusError as e:  # Be more specific with the exception
        pytest.fail(f"LocalStack connection failed: {e}")


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
