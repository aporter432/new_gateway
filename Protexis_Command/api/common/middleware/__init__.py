"""Middleware for the OGx API."""

from .ogx_auth import add_ogx_auth_middleware
from .protexis_auth import add_protexis_auth_middleware

__all__ = ["add_protexis_auth_middleware", "add_ogx_auth_middleware"]
