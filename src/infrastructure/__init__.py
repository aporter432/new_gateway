"""
This module contains the infrastructure components for the application.
"""

from .redis import get_redis_client

__all__ = ["get_redis_client"]
