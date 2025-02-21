"""Middleware for the OGx API."""

from .ogx_auth import add_ogx_auth_middleware

__all__ = ["add_ogx_auth_middleware"]
