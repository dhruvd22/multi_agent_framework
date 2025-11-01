"""
Configuration module for the multi-agent framework.

This module provides centralized configuration management using Pydantic settings.
All environment variables are loaded and validated here.
"""

from .settings import Settings, get_settings

__all__ = ["Settings", "get_settings"]

