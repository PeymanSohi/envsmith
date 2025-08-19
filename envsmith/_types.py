"""
Type hints for envsmith.
"""
from typing import Dict, Any, Callable, Optional

SchemaType = Dict[str, Any]
EnvType = Dict[str, Any]
ValidatorType = Callable[[EnvType, SchemaType], EnvType]
