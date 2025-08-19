"""
Validation logic for envsmith.
Validates env dict against schema.

Doctest:
>>> from envsmith.validation import validate_env
>>> schema = {"FOO": {"type": "str", "required": True}}
>>> env = {"FOO": "bar"}
>>> validate_env(env, schema)["FOO"]
'bar'
"""
from typing import Any, Dict
import logging

logger = logging.getLogger("envsmith.validation")

def validate_env(env: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """Validate env dict against schema, apply defaults and type casting."""
    validated = {}
    errors = []
    for key, rules in schema.items():
        value = env.get(key, rules.get("default"))
        if rules.get("required", False) and value is None:
            errors.append(f"Missing required env var: {key}")
            continue
        if value is not None:
            try:
                validated[key] = _cast_type(value, rules.get("type", "str"))
            except Exception as e:
                errors.append(f"Invalid type for {key}: {e}")
    if errors:
        logger.error("Validation errors: %s", errors)
        raise ValueError("; ".join(errors))
    return validated

def _cast_type(value: Any, typ: str) -> Any:
    if typ == "str":
        return str(value)
    if typ == "int":
        return int(value)
    if typ == "float":
        return float(value)
    if typ == "bool":
        if isinstance(value, bool):
            return value
        if str(value).lower() in ("1", "true", "yes", "on"):
            return True
        if str(value).lower() in ("0", "false", "no", "off"):
            return False
        raise ValueError(f"Cannot cast {value} to bool")
    return value
