"""
Schema loader for envsmith.
Supports YAML and JSON schema files.

Doctest:
>>> from envsmith.schema_loader import load_schema
>>> s = load_schema('examples/schema.yaml')  # doctest: +SKIP
>>> isinstance(s, dict)
True
"""
import yaml
import json
from typing import Any, Dict, Optional

def load_schema(path: Optional[str]) -> Dict[str, Any]:
    """Load schema from YAML or JSON file."""
    if not path:
        return {}
    if path.endswith('.yaml') or path.endswith('.yml'):
        with open(path, 'r') as f:
            return yaml.safe_load(f)
    elif path.endswith('.json'):
        with open(path, 'r') as f:
            return json.load(f)
    else:
        raise ValueError("Schema file must be .yaml, .yml, or .json")
