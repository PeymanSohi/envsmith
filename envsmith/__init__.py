"""
Smart Environment Variable Loader

A production-ready Python package for loading, validating, and managing environment variables
with support for multi-file loading, schema validation, secrets resolution, and more.
"""

__version__ = "0.2.0"

from .core import load_env, watch_env
from .validation import validate_env
from .schema_loader import load_schema
from .secrets import resolve_secret_maybe, register_provider, SecretProvider

__all__ = [
    "load_env",
    "watch_env", 
    "validate_env",
    "load_schema",
    "resolve_secret_maybe",
    "register_provider",
    "SecretProvider",
]
