"""Django integration for smart-envloader."""

import logging
import os
from typing import List, Optional, Union
from pathlib import Path

from django.apps import AppConfig
from django.conf import settings as django_settings

from ..core import load_env
from ..validation import validate_env
from ..schema_loader import load_schema
from .._types import SchemaDict

logger = logging.getLogger(__name__)

class EnvAppConfig(AppConfig):
    """
    Django AppConfig that automatically loads and validates environment variables.
    
    Add this to your Django project's INSTALLED_APPS to automatically load
    environment variables when Django starts.
    """
    
    name = "smart_envloader.django"
    verbose_name = "Smart Environment Loader"
    
    def __init__(self, app_name, import_path):
        super().__init__(app_name, import_path)
        self.env_files = getattr(django_settings, 'ENV_FILES', ['.env'])
        self.schema_path = getattr(django_settings, 'ENV_SCHEMA_PATH', None)
        self.schema = getattr(django_settings, 'ENV_SCHEMA', None)
        self.required_vars = getattr(django_settings, 'ENV_REQUIRED_VARS', None)
        self.override = getattr(django_settings, 'ENV_OVERRIDE', False)
        self.expand = getattr(django_settings, 'ENV_EXPAND', True)
        self.cache = getattr(django_settings, 'ENV_CACHE', True)
        self.strict = getattr(django_settings, 'ENV_STRICT', True)
    
    def ready(self):
        """
        Called when Django is ready to start.
        
        This method loads environment variables and validates them against
        the schema if provided.
        """
        if os.environ.get('RUN_MAIN') == 'true':
            # Only run once in development
            return
        
        try:
            # Load environment files
            if self.env_files:
                loaded_env = load_env(
                    paths=self.env_files,
                    required=self.required_vars,
                    override=self.override,
                    expand=self.expand,
                    cache=self.cache
                )
                logger.info(f"Loaded {len(loaded_env)} environment variables from {self.env_files}")
            
            # Load and apply schema validation if provided
            if self.schema_path or self.schema:
                try:
                    if self.schema_path:
                        schema = load_schema(self.schema_path)
                    else:
                        schema = self.schema
                    
                    if schema:
                        validated_env = validate_env(schema, strict=self.strict)
                        logger.info(f"Validated {len(validated_env)} environment variables against schema")
                except Exception as e:
                    logger.error(f"Failed to validate environment against schema: {e}")
                    # In Django, we might want to continue even if validation fails
                    # depending on the environment (dev vs prod)
                    if getattr(django_settings, 'ENV_VALIDATION_STRICT', False):
                        raise
            
        except Exception as e:
            logger.error(f"Failed to load environment variables: {e}")
            # In Django, we might want to continue even if env loading fails
            # depending on the environment (dev vs prod)
            if getattr(django_settings, 'ENV_LOADING_STRICT', False):
                raise

def load_django_env(
    files: Optional[Union[str, List[str]]] = None,
    schema_path: Optional[str] = None,
    schema: Optional[SchemaDict] = None,
    required: Optional[List[str]] = None,
    override: bool = False,
    expand: bool = True,
    cache: bool = True,
    strict: bool = True,
) -> dict:
    """
    Manually load environment variables for Django.
    
    This function can be called from Django settings.py or other Django code
    to manually load environment variables.
    
    Args:
        files: Environment file(s) to load
        schema_path: Path to schema file (YAML/JSON)
        schema: Schema dictionary for validation
        required: List of required environment variables
        override: Whether to override existing environment variables
        expand: Whether to expand variable references
        cache: Whether to use file caching
        strict: Whether to use strict validation
        
    Returns:
        Dictionary of loaded environment variables
        
    Example usage in settings.py:
        from smart_envloader.integrations.django import load_django_env
        
        # Load environment variables
        env_vars = load_django_env(
            files=['.env', '.env.local'],
            schema_path='schema.yaml',
            required=['DEBUG', 'SECRET_KEY', 'DATABASE_URL']
        )
        
        # Use in Django settings
        DEBUG = env_vars.get('DEBUG', False)
        SECRET_KEY = env_vars['SECRET_KEY']
        DATABASE_URL = env_vars['DATABASE_URL']
    """
    try:
        # Load environment files
        if files:
            loaded_env = load_env(
                paths=files,
                required=required,
                override=override,
                expand=expand,
                cache=cache
            )
            logger.info(f"Loaded {len(loaded_env)} environment variables from {files}")
        else:
            loaded_env = {}
        
        # Load and apply schema validation if provided
        if schema_path or schema:
            try:
                if schema_path:
                    schema = load_schema(schema_path)
                else:
                    schema = schema
                
                if schema:
                    validated_env = validate_env(schema, strict=strict)
                    logger.info(f"Validated {len(validated_env)} environment variables against schema")
                    # Merge validated env with loaded env
                    loaded_env.update(validated_env)
            except Exception as e:
                logger.error(f"Failed to validate environment against schema: {e}")
                if strict:
                    raise
        
        return loaded_env
        
    except Exception as e:
        logger.error(f"Failed to load environment variables: {e}")
        raise

# Django settings configuration example:
"""
# In your Django settings.py, add:

INSTALLED_APPS = [
    # ... other apps ...
    'smart_envloader.integrations.django.EnvAppConfig',
]

# Optional: Configure environment loading behavior
ENV_FILES = ['.env', '.env.local', '.env.production']
ENV_SCHEMA_PATH = 'schema.yaml'
ENV_REQUIRED_VARS = ['DEBUG', 'SECRET_KEY', 'DATABASE_URL']
ENV_OVERRIDE = False
ENV_EXPAND = True
ENV_CACHE = True
ENV_STRICT = True
ENV_VALIDATION_STRICT = False  # Continue even if validation fails
ENV_LOADING_STRICT = False     # Continue even if loading fails
"""
