"""
FastAPI integration for envsmith.

Doctest:
>>> from envsmith.integrations.fastapi import get_settings
>>> callable(get_settings)
True
"""
from fastapi import Depends
from envsmith.core import EnvSmith

def get_settings(schema_path: str = "schema.yaml"):
    return EnvSmith(schema_path=schema_path)
