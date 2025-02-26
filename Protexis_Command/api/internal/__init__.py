"""Internal module for the API."""

from .app_init import create_app, init_routes
from .protexis_main import app

__all__ = ["create_app", "init_routes", "app"]
