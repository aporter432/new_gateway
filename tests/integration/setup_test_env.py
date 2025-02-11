"""Test environment setup and initialization script."""

import asyncio
import os
import subprocess
import sys
from typing import Dict, Optional

import docker
import requests
from docker.errors import NotFound
from docker.models.containers import Container


class TestEnvironmentSetup:
    """Manages the setup and teardown of the test environment."""

    def __init__(self):
        self.docker_client = docker.from_env()
        self.containers: Dict[str, Container] = {}

    def start_localstack(self) -> Optional[str]:
        """Start LocalStack container for AWS service mocking."""
        try:
            container = self.docker_client.containers.run(
                "localstack/localstack:latest",
                name="test-localstack",
                ports={4566: 4566},
                detach=True,
                environment={
                    "SERVICES": "dynamodb,sqs,cloudwatch",
                    "DEFAULT_REGION": "us-east-1",
                },
            )
            self.containers["localstack"] = container
            self._wait_for_localstack()
            return container.id
        except Exception as e:
            print(f"Failed to start LocalStack: {e}")
            return None

    def start_redis(self) -> Optional[str]:
        """Start Redis container for test database."""
        try:
            container = self.docker_client.containers.run(
                "redis:latest",
                name="test-redis",
                ports={6379: 6379},
                detach=True,
            )
            self.containers["redis"] = container
            self._wait_for_redis()
            return container.id
        except Exception as e:
            print(f"Failed to start Redis: {e}")
            return None

    async def _wait_for_localstack(self, timeout: int = 30):
        """Wait for LocalStack to be ready."""
        for _ in range(timeout):
            try:
                response = requests.get("http://localhost:4566/_localstack/health")
                if response.status_code == 200:
                    print("LocalStack is ready")
                    return
            except requests.exceptions.ConnectionError:
                pass
            await asyncio.sleep(1)
        raise TimeoutError("LocalStack failed to start")

    async def _wait_for_redis(self, timeout: int = 30):
        """Wait for Redis to be ready."""
        for _ in range(timeout):
            try:
                result = subprocess.run(
                    ["redis-cli", "ping"],
                    capture_output=True,
                    text=True,
                )
                if "PONG" in result.stdout:
                    print("Redis is ready")
                    return
            except subprocess.CalledProcessError:
                pass
            await asyncio.sleep(1)
        raise TimeoutError("Redis failed to start")

    async def setup_environment(self):
        """Set up the complete test environment."""
        # Start infrastructure services
        if not self.start_localstack():
            sys.exit("Failed to start LocalStack")
        if not self.start_redis():
            sys.exit("Failed to start Redis")

        # Set environment variables
        os.environ.update(
            {
                "ENVIRONMENT": "test",
                "REDIS_HOST": "localhost",
                "REDIS_PORT": "6379",
                "REDIS_DB": "15",
                "AWS_ENDPOINT_URL": "http://localhost:4566",
                "AWS_REGION": "us-east-1",
                "AWS_ACCESS_KEY_ID": "test",
                "AWS_SECRET_ACCESS_KEY": "test",
                "OGWS_BASE_URL": "http://proxy:8080/api/v1.0",
            }
        )

        print("Test environment setup complete")

    def teardown(self):
        """Clean up the test environment."""
        for name, container in self.containers.items():
            try:
                container.stop()
                container.remove()
                print(f"Stopped and removed {name} container")
            except NotFound:
                pass
            except Exception as e:
                print(f"Error cleaning up {name} container: {e}")


if __name__ == "__main__":
    env = TestEnvironmentSetup()
    try:
        asyncio.run(env.setup_environment())
    except KeyboardInterrupt:
        print("\nShutting down test environment...")
        env.teardown()
