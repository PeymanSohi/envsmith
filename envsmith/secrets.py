"""Secret resolution functionality."""

import os
import logging
from pathlib import Path
from typing import Dict, Optional

from ._types import SecretProvider, SecretResolutionError

logger = logging.getLogger(__name__)

# Registry for secret providers
PROVIDERS: Dict[str, SecretProvider] = {}

class EnvSecretProvider:
    """Provider for resolving secrets from environment variables."""
    
    scheme = "env"
    
    def resolve(self, uri: str) -> str:
        """
        Resolve a secret from an environment variable.
        
        Args:
            uri: URI in format "env://VAR_NAME" or "secret://env/VAR_NAME"
            
        Returns:
            The resolved secret value
            
        Raises:
            SecretResolutionError: If the environment variable is not set
        """
        # Extract variable name from URI
        if uri.startswith("env://"):
            var_name = uri[6:]
        elif uri.startswith("secret://env/"):
            var_name = uri[13:]
        else:
            raise SecretResolutionError(f"Invalid env URI format: {uri}")
        
        if not var_name:
            raise SecretResolutionError("Empty environment variable name in URI")
        
        # Get value from environment
        value = os.environ.get(var_name)
        if value is None:
            raise SecretResolutionError(f"Environment variable '{var_name}' is not set")
        
        logger.debug(f"Resolved secret from environment variable: {var_name}")
        return value

class FileSecretProvider:
    """Provider for resolving secrets from files."""
    
    scheme = "file"
    
    def resolve(self, uri: str) -> str:
        """
        Resolve a secret from a file.
        
        Args:
            uri: URI in format "file:///path/to/file" or "secret://file/path/to/file"
            
        Returns:
            The file contents
            
        Raises:
            SecretResolutionError: If the file cannot be read
        """
        # Extract file path from URI
        if uri.startswith("file://"):
            file_path = uri[7:]
        elif uri.startswith("secret://file/"):
            file_path = uri[14:]
        else:
            raise SecretResolutionError(f"Invalid file URI format: {uri}")
        
        if not file_path:
            raise SecretResolutionError("Empty file path in URI")
        
        # Resolve the file path
        try:
            path = Path(file_path)
            if not path.exists():
                raise SecretResolutionError(f"Secret file does not exist: {path}")
            
            # Read file contents
            with open(path, 'r', encoding='utf-8') as f:
                content = f.read().strip()
            
            logger.debug(f"Resolved secret from file: {path}")
            return content
            
        except Exception as e:
            if isinstance(e, SecretResolutionError):
                raise
            raise SecretResolutionError(f"Error reading secret file {file_path}: {e}")

def register_provider(provider: SecretProvider) -> None:
    """
    Register a custom secret provider.
    
    Args:
        provider: Provider instance implementing the SecretProvider protocol
    """
    if not hasattr(provider, 'scheme'):
        raise ValueError("Provider must have a 'scheme' attribute")
    
    if not callable(getattr(provider, 'resolve', None)):
        raise ValueError("Provider must have a 'resolve' method")
    
    PROVIDERS[provider.scheme] = provider
    logger.debug(f"Registered secret provider: {provider.scheme}")

def resolve_secret_maybe(value: str) -> str:
    """
    Resolve a secret if the value looks like a secret URI.
    
    Args:
        value: The value to potentially resolve
        
    Returns:
        The resolved secret value or the original value if not a secret URI
    """
    # Check if this looks like a secret URI
    if not (value.startswith("secret://") or value.startswith("env://") or value.startswith("file://")):
        return value
    
    # Extract scheme from URI
    if value.startswith("secret://"):
        # Format: secret://scheme/path
        parts = value[9:].split("/", 1)
        if len(parts) != 2:
            raise SecretResolutionError(f"Invalid secret URI format: {value}")
        scheme, path = parts
        uri = f"{scheme}://{path}"
    else:
        # Format: scheme://path
        scheme = value.split("://")[0]
        uri = value
    
    # Find and use the appropriate provider
    if scheme in PROVIDERS:
        try:
            return PROVIDERS[scheme].resolve(uri)
        except Exception as e:
            if isinstance(e, SecretResolutionError):
                raise
            raise SecretResolutionError(f"Error resolving secret {uri}: {e}")
    else:
        raise SecretResolutionError(f"No provider registered for scheme: {scheme}")

# Register built-in providers
def _register_builtin_providers():
    """Register the built-in secret providers."""
    register_provider(EnvSecretProvider())
    register_provider(FileSecretProvider())

# Auto-register built-in providers when module is imported
_register_builtin_providers()
