"""Schema loading from YAML and JSON files."""

import json
import logging
from pathlib import Path
from typing import Any, Dict, Union

from ._types import SchemaDict, SchemaError

logger = logging.getLogger(__name__)

def load_schema(path: Union[str, Path]) -> SchemaDict:
    """
    Load a schema from a YAML or JSON file.
    
    Args:
        path: Path to the schema file
        
    Returns:
        Loaded schema dictionary
        
    Raises:
        SchemaError: If the schema cannot be loaded or parsed
    """
    path = Path(path)
    
    if not path.exists():
        raise SchemaError(f"Schema file not found: {path}")
    
    logger.debug(f"Loading schema from: {path}")
    
    try:
        if path.suffix.lower() in ('.yml', '.yaml'):
            return _load_yaml_schema(path)
        elif path.suffix.lower() == '.json':
            return _load_json_schema(path)
        else:
            raise SchemaError(f"Unsupported schema file format: {path.suffix}")
    
    except Exception as e:
        if isinstance(e, SchemaError):
            raise
        raise SchemaError(f"Error loading schema from {path}: {e}")

def _load_yaml_schema(path: Path) -> SchemaDict:
    """
    Load schema from YAML file.
    
    Args:
        path: Path to YAML file
        
    Returns:
        Loaded schema dictionary
        
    Raises:
        SchemaError: If YAML parsing fails
    """
    try:
        import yaml
        with open(path, 'r', encoding='utf-8') as f:
            schema = yaml.safe_load(f)
    except ImportError:
        raise SchemaError("PyYAML is required to load YAML schemas. Install with: pip install pyyaml")
    except yaml.YAMLError as e:
        raise SchemaError(f"Invalid YAML in {path}: {e}")
    except Exception as e:
        raise SchemaError(f"Error reading YAML file {path}: {e}")
    
    if not isinstance(schema, dict):
        raise SchemaError(f"Schema must be a dictionary, got {type(schema)}")
    
    # Validate and normalize the schema
    return _normalize_schema_dict(schema, str(path))

def _load_json_schema(path: Path) -> SchemaDict:
    """
    Load schema from JSON file.
    
    Args:
        path: Path to JSON file
        
    Returns:
        Loaded schema dictionary
        
    Raises:
        SchemaError: If JSON parsing fails
    """
    try:
        with open(path, 'r', encoding='utf-8') as f:
            schema = json.load(f)
    except json.JSONDecodeError as e:
        raise SchemaError(f"Invalid JSON in {path}: {e}")
    except Exception as e:
        raise SchemaError(f"Error reading JSON file {path}: {e}")
    
    if not isinstance(schema, dict):
        raise SchemaError(f"Schema must be a dictionary, got {type(schema)}")
    
    # Validate and normalize the schema
    return _normalize_schema_dict(schema, str(path))

def _normalize_schema_dict(schema: Dict[str, Any], source: str) -> SchemaDict:
    """
    Normalize and validate a schema dictionary.
    
    Args:
        schema: Raw schema dictionary
        source: Source file path for error messages
        
    Returns:
        Normalized schema dictionary
        
    Raises:
        SchemaError: If schema is invalid
    """
    normalized: SchemaDict = {}
    
    for key, value in schema.items():
        if not isinstance(key, str):
            raise SchemaError(f"Schema keys must be strings, got {type(key)} for key '{key}' in {source}")
        
        if isinstance(value, dict):
            # Extended format
            if 'type' not in value:
                raise SchemaError(f"Schema field '{key}' missing 'type' in {source}")
            
            # Validate type field
            type_value = value['type']
            if not isinstance(type_value, (str, type)):
                raise SchemaError(f"Schema field '{key}' type must be string or type, got {type(type_value)} in {source}")
            
            # Validate other fields
            valid_fields = {
                'type', 'required', 'default', 'description', 'regex', 
                'choices', 'min', 'max', 'min_len', 'max_len', 'validator', 'transform'
            }
            
            for field in value:
                if field not in valid_fields:
                    logger.warning(f"Unknown schema field '{field}' for '{key}' in {source}")
            
            # Validate boolean fields
            for bool_field in ('required',):
                if bool_field in value and not isinstance(value[bool_field], bool):
                    raise SchemaError(f"Schema field '{key}' {bool_field} must be boolean in {source}")
            
            # Validate numeric fields
            for num_field in ('min', 'max', 'min_len', 'max_len'):
                if num_field in value and not isinstance(value[num_field], (int, float)):
                    raise SchemaError(f"Schema field '{key}' {num_field} must be numeric in {source}")
            
            # Validate regex field
            if 'regex' in value and not isinstance(value['regex'], str):
                raise SchemaError(f"Schema field '{key}' regex must be string in {source}")
            
            # Validate choices field
            if 'choices' in value:
                if not isinstance(value['choices'], (list, tuple)):
                    raise SchemaError(f"Schema field '{key}' choices must be list or tuple in {source}")
                if not value['choices']:
                    raise SchemaError(f"Schema field '{key}' choices cannot be empty in {source}")
            
            # Validate validator field
            if 'validator' in value and not callable(value['validator']):
                raise SchemaError(f"Schema field '{key}' validator must be callable in {source}")
            
            # Validate transform field
            if 'transform' in value and not callable(value['transform']):
                raise SchemaError(f"Schema field '{key}' transform must be callable in {source}")
            
            normalized[key] = value
            
        elif isinstance(value, str):
            # Simple format with string type annotation
            normalized[key] = {'type': value}
            
        elif isinstance(value, type):
            # Simple format with Python type
            normalized[key] = {'type': value}
            
        else:
            raise SchemaError(f"Invalid schema value for '{key}' in {source}: {type(value)}")
    
    logger.info(f"Successfully loaded schema with {len(normalized)} fields from {source}")
    return normalized
