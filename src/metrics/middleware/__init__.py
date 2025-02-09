"""Middleware for metrics collection."""

from .fastapi import add_metrics_middleware

__all__ = ["add_metrics_middleware"]
