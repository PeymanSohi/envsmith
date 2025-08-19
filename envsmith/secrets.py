"""
Secrets manager for envsmith.
Mock interface for external secret providers.

Doctest:
>>> from envsmith.secrets import SecretProvider
>>> s = SecretProvider()
>>> s.get_secret('foo')
'secret-value-for-foo'
"""
import logging
from typing import Any

logger = logging.getLogger("envsmith.secrets")

class SecretProvider:
    """Mock secret provider interface."""
    def get_secret(self, key: str) -> Any:
        logger.info(f"Fetching secret for {key}")
        # In production, integrate with AWS, Vault, etc.
        return f"secret-value-for-{key}"

    def get_local_secret(self, key: str) -> Any:
        logger.info(f"Fetching local secret for {key}")
        return f"local-secret-value-for-{key}"
