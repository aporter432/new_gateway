"""
This module contains the RBA (Role-Based Access Control) implementation for the Protexis system.

It includes:
- Role descriptions
- Role hierarchy
- Role-based access control utilities
"""

from .role_descriptions import RoleDescriptions
from .role_hierarchy import RoleHierarchy
from .roles import requires_roles

__all__ = ["RoleDescriptions", "RoleHierarchy", "requires_roles"]
