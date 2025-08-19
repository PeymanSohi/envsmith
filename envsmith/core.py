"""
Core loader for envsmith.

Loads environment variables from .env, system, or dict, with schema validation and type casting.

Doctest:
>>> import os
>>> os.environ['FOO'] = 'bar'
>>> from envsmith.core import EnvSmith
>>> s = EnvSmith(schema={"FOO": {"type": "str"}})
>>> s["FOO"]
'bar'
"""
import os
import logging
from typing import Any, Dict, Optional, Union
from .schema_loader import load_schema
from .validation import validate_env
from dotenv import load_dotenv

logger = logging.getLogger("envsmith.core")

class EnvSmith(dict):
    def __init__(self, schema_path: Optional[str] = None, schema: Optional[dict] = None, env_file: str = ".env", env: Optional[dict] = None):
        """
        Initialize EnvSmith loader.
        Args:
            schema_path: Path to YAML/JSON schema file.
            schema: Schema dict (overrides schema_path).
            env_file: Path to .env file.
            env: Optional dict to use as environment.
        """
        super().__init__()
        load_dotenv(env_file)
        self.schema = schema or (load_schema(schema_path) if schema_path else {})
        self.env = env or dict(os.environ)
        validated = validate_env(self.env, self.schema)
        self.update(validated)
        logger.info("Loaded environment with schema: %s", self.schema)

    def get(self, key: str, default: Any = None) -> Any:
        return super().get(key, default)

    def __getitem__(self, key: str) -> Any:
        return super().__getitem__(key)

    def export(self, as_format: str = "json") -> str:
        """Export validated env as JSON or YAML string."""
        import json
        import yaml
        if as_format == "json":
            return json.dumps(self, indent=2)
        elif as_format == "yaml":
            return yaml.dump(dict(self))
        else:
            raise ValueError("Format must be 'json' or 'yaml'")
