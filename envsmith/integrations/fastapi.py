"""FastAPI integration for smart-envloader."""

import logging
from typing import Any, Dict, List, Optional, Union
from pathlib import Path

from fastapi import Depends
from pydantic import BaseSettings, Field

from ..core import load_env
from ..validation import validate_env
from ..schema_loader import load_schema
from .._types import SchemaDict

logger = logging.getLogger(__name__)

class Settings(BaseSettings):
    """
    FastAPI settings class that automatically loads and validates environment variables.
    
    This class extends Pydantic's BaseSettings and integrates with smart-envloader
    to provide automatic environment loading, validation, and type conversion.
    """
    
    def __init__(
        self,
        *,
        files: Optional[Union[str, List[str]]] = None,
        schema_path: Optional[str] = None,
        schema: Optional[SchemaDict] = None,
        required: Optional[List[str]] = None,
        override: bool = False,
        expand: bool = True,
        cache: bool = True,
        strict: bool = True,
        **kwargs
    ):
        """
        Initialize settings with environment loading and validation.
        
        Args:
            files: Environment file(s) to load
            schema_path: Path to schema file (YAML/JSON)
            schema: Schema dictionary for validation
            required: List of required environment variables
            override: Whether to override existing environment variables
            expand: Whether to expand variable references
            cache: Whether to use file caching
            strict: Whether to use strict validation
            **kwargs: Additional arguments passed to BaseSettings
        """
        # Load environment files first
        if files:
            try:
                loaded_env = load_env(
                    paths=files,
                    required=required,
                    override=override,
                    expand=expand,
                    cache=cache
                )
                logger.info(f"Loaded {len(loaded_env)} environment variables from {files}")
            except Exception as e:
                logger.error(f"Failed to load environment files: {e}")
                raise
        
        # Load and apply schema validation if provided
        if schema_path or schema:
            try:
                if schema_path:
                    schema = load_schema(schema_path)
                
                if schema:
                    validated_env = validate_env(schema, strict=strict)
                    logger.info(f"Validated {len(validated_env)} environment variables against schema")
            except Exception as e:
                logger.error(f"Failed to validate environment against schema: {e}")
                raise
        
        # Initialize BaseSettings
        super().__init__(**kwargs)
    
    class Config:
        """Pydantic configuration."""
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False

def get_settings(settings_class: type = Settings) -> Settings:
    """
    Dependency factory for FastAPI dependency injection.
    
    Args:
        settings_class: Settings class to use (defaults to Settings)
        
    Returns:
        Dependency function that returns a settings instance
    """
    def _get_settings() -> Settings:
        return settings_class()
    
    return _get_settings

# Example usage:
# app = FastAPI(dependencies=[Depends(get_settings())])
# 
# @app.get("/config")
# def get_config(settings: Settings = Depends(get_settings())):
#     return {"debug": settings.debug, "port": settings.port}
