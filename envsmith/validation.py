"""Environment variable validation and type casting."""

import json
import re
import logging
from typing import Any, Dict, List, Optional, Set, Tuple, Union, get_origin, get_args
from typing_extensions import Literal

from ._types import (
    ValidationError, SchemaDict, ValidationResult, 
    ValidatorFunc, TransformFunc, ExtendedSchemaValue
)

logger = logging.getLogger(__name__)

def _parse_type_annotation(type_annotation: str) -> type:
    """
    Parse a string type annotation into a Python type.
    
    Args:
        type_annotation: String representation of type (e.g., "list[str]", "Optional[int]")
        
    Returns:
        Python type object
        
    Raises:
        ValueError: If type annotation cannot be parsed
    """
    # Handle basic types
    basic_types = {
        'str': str, 'int': int, 'float': float, 'bool': bool,
        'list': list, 'dict': dict, 'tuple': tuple, 'set': set
    }
    
    if type_annotation in basic_types:
        return basic_types[type_annotation]
    
    # Handle generic types
    if '[' in type_annotation and type_annotation.endswith(']'):
        base_type = type_annotation[:type_annotation.index('[')]
        if base_type not in basic_types:
            raise ValueError(f"Unknown base type: {base_type}")
        
        # Extract type arguments
        args_str = type_annotation[type_annotation.index('[') + 1:-1]
        
        if base_type == 'list':
            if args_str == 'str':
                return List[str]
            elif args_str == 'int':
                return List[int]
            elif args_str == 'float':
                return List[float]
            elif args_str == 'bool':
                return List[bool]
            else:
                return List[Any]
        
        elif base_type == 'dict':
            if ',' in args_str:
                key_type, value_type = args_str.split(',', 1)
                if key_type.strip() == 'str':
                    if value_type.strip() == 'int':
                        return Dict[str, int]
                    elif value_type.strip() == 'str':
                        return Dict[str, str]
                    elif value_type.strip() == 'float':
                        return Dict[str, float]
                    elif value_type.strip() == 'bool':
                        return Dict[str, bool]
                    else:
                        return Dict[str, Any]
                else:
                    return Dict[str, Any]
            else:
                return Dict[str, Any]
        
        elif base_type == 'set':
            if args_str == 'str':
                return Set[str]
            elif args_str == 'int':
                return Set[int]
            elif args_str == 'float':
                return Set[float]
            elif args_str == 'bool':
                return Set[bool]
            else:
                return Set[Any]
        
        elif base_type == 'tuple':
            if args_str == 'str':
                return Tuple[str, ...]
            elif args_str == 'int':
                return Tuple[int, ...]
            elif args_str == 'float':
                return Tuple[float, ...]
            elif args_str == 'bool':
                return Tuple[bool, ...]
            else:
                return Tuple[Any, ...]
    
    # Handle Optional types
    if type_annotation.startswith('Optional[') and type_annotation.endswith(']'):
        inner_type = type_annotation[9:-1]  # Remove 'Optional[' and ']'
        try:
            return Optional[_parse_type_annotation(inner_type)]
        except ValueError:
            return Optional[Any]
    
    # Handle Union types
    if type_annotation.startswith('Union[') and type_annotation.endswith(']'):
        inner_types = type_annotation[6:-1]  # Remove 'Union[' and ']'
        type_args = [t.strip() for t in inner_types.split(',')]
        try:
            parsed_types = [_parse_type_annotation(t) for t in type_args]
            return Union[tuple(parsed_types)]
        except ValueError:
            return Union[Any, ...]
    
    # Handle Literal types
    if type_annotation.startswith('Literal[') and type_annotation.endswith(']'):
        inner_values = type_annotation[9:-1]  # Remove 'Literal[' and ']'
        # This is a simplified parser - in practice you'd want more robust parsing
        try:
            # Try to evaluate as Python literals
            values = []
            for val in inner_values.split(','):
                val = val.strip().strip('"\'')
                if val.lower() in ('true', 'false'):
                    values.append(val.lower() == 'true')
                elif val.isdigit():
                    values.append(int(val))
                elif val.replace('.', '').replace('-', '').isdigit():
                    values.append(float(val))
                else:
                    values.append(val)
            return Literal[tuple(values)]
        except:
            return Any
    
    raise ValueError(f"Cannot parse type annotation: {type_annotation}")

def _cast_value(value: str, target_type: type) -> Any:
    """
    Cast a string value to the target type.
    
    Args:
        value: String value to cast
        target_type: Target type to cast to
        
    Returns:
        Casted value
        
    Raises:
        ValueError: If casting fails
    """
    # Handle None values
    if value.lower() in ('none', 'null', ''):
        return None
    
    # Handle basic types
    if target_type == str:
        return value
    
    elif target_type == int:
        return int(value)
    
    elif target_type == float:
        return float(value)
    
    elif target_type == bool:
        # Handle various boolean representations
        if value.lower() in ('true', '1', 'on', 'yes'):
            return True
        elif value.lower() in ('false', '0', 'off', 'no'):
            return False
        else:
            raise ValueError(f"Cannot convert '{value}' to bool")
    
    # Handle generic types
    origin = get_origin(target_type)
    args = get_args(target_type)
    
    if origin == list:
        # Handle comma-separated values
        if value.startswith('[') and value.endswith(']'):
            try:
                # Try to parse as JSON
                return json.loads(value)
            except json.JSONDecodeError:
                # Fall back to comma-separated
                pass
        
        # Split by comma and strip whitespace
        items = [item.strip() for item in value.split(',') if item.strip()]
        if args and args[0] != Any:
            # Cast each item to the specified type
            return [_cast_value(item, args[0]) for item in items]
        else:
            return items
    
    elif origin == set:
        # Similar to list but convert to set
        if value.startswith('{') and value.endswith('}'):
            try:
                return set(json.loads(value))
            except json.JSONDecodeError:
                pass
        
        items = [item.strip() for item in value.split(',') if item.strip()]
        if args and args[0] != Any:
            return {_cast_value(item, args[0]) for item in items}
        else:
            return set(items)
    
    elif origin == tuple:
        # Similar to list but convert to tuple
        if value.startswith('(') and value.endswith(')') or (value.startswith('[') and value.endswith(']')):
            try:
                return tuple(json.loads(value))
            except json.JSONDecodeError:
                pass
        
        items = [item.strip() for item in value.split(',') if item.strip()]
        if args and args[0] != Any:
            return tuple(_cast_value(item, args[0]) for item in items)
        else:
            return tuple(items)
    
    elif origin == dict:
        # Try to parse as JSON
        if value.startswith('{') and value.endswith('}'):
            try:
                return json.loads(value)
            except json.JSONDecodeError:
                raise ValueError(f"Cannot parse '{value}' as JSON dict")
        else:
            raise ValueError(f"Dict values must be valid JSON: {value}")
    
    elif target_type == Optional[Any] or (hasattr(target_type, '__origin__') and target_type.__origin__ == Union):
        # Handle Optional/Union types
        if args:
            # Try each possible type
            for arg in args:
                if arg == type(None):  # None type
                    continue
                try:
                    return _cast_value(value, arg)
                except ValueError:
                    continue
            # If we get here, none of the types worked
            raise ValueError(f"Cannot convert '{value}' to any of {args}")
        else:
            return value
    
    else:
        raise ValueError(f"Unsupported type: {target_type}")

def _validate_constraints(
    key: str, 
    value: Any, 
    constraints: Dict[str, Any]
) -> Optional[str]:
    """
    Validate a value against constraints.
    
    Args:
        key: Environment variable name
        value: Value to validate
        constraints: Constraints to apply
        
    Returns:
        Error message if validation fails, None if successful
    """
    # Regex validation
    if 'regex' in constraints:
        pattern = constraints['regex']
        if not re.match(pattern, str(value)):
            return f"Value '{value}' does not match pattern '{pattern}'"
    
    # Choices validation
    if 'choices' in constraints:
        choices = constraints['choices']
        if value not in choices:
            return f"Value '{value}' is not one of {choices}"
    
    # Min/Max validation for numbers
    if isinstance(value, (int, float)):
        if 'min' in constraints and value < constraints['min']:
            return f"Value {value} is less than minimum {constraints['min']}"
        if 'max' in constraints and value > constraints['max']:
            return f"Value {value} is greater than maximum {constraints['max']}"
    
    # Min/Max length validation for strings and collections
    if hasattr(value, '__len__'):
        if 'min_len' in constraints and len(value) < constraints['min_len']:
            return f"Length {len(value)} is less than minimum {constraints['min_len']}"
        if 'max_len' in constraints and len(value) > constraints['max_len']:
            return f"Length {len(value)} is greater than maximum {constraints['max_len']}"
    
    # Custom validator
    if 'validator' in constraints:
        validator = constraints['validator']
        if callable(validator) and not validator(value):
            return f"Custom validation failed for value '{value}'"
    
    return None

def _normalize_schema(schema: SchemaDict) -> Dict[str, Dict[str, Any]]:
    """
    Normalize schema to extended format.
    
    Args:
        schema: Schema in either simple or extended format
        
    Returns:
        Normalized schema in extended format
    """
    normalized = {}
    
    for key, value in schema.items():
        if isinstance(value, type):
            # Simple format: {"PORT": int}
            normalized[key] = {"type": value}
        elif isinstance(value, dict):
            # Extended format: {"PORT": {"type": int, "required": True}}
            if "type" not in value:
                raise ValueError(f"Schema for '{key}' missing 'type' field")
            
            # Parse string type annotations
            if isinstance(value["type"], str):
                try:
                    value["type"] = _parse_type_annotation(value["type"])
                except ValueError as e:
                    raise ValueError(f"Invalid type annotation for '{key}': {e}")
            
            normalized[key] = value.copy()
        else:
            raise ValueError(f"Invalid schema value for '{key}': {value}")
    
    return normalized

def validate_env(schema: SchemaDict, *, strict: bool = True) -> ValidationResult:
    """
    Validate environment variables against a schema.
    
    Args:
        schema: Schema defining expected environment variables
        strict: Whether to raise errors for missing non-required variables
        
    Returns:
        Dictionary of validated and casted values
        
    Raises:
        ValidationError: If validation fails
    """
    import os
    
    normalized_schema = _normalize_schema(schema)
    result: ValidationResult = {}
    errors: Dict[str, str] = {}
    
    # Process each schema field
    for key, field_schema in normalized_schema.items():
        target_type = field_schema["type"]
        required = field_schema.get("required", False)
        default = field_schema.get("default", None)
        
        # Get value from environment
        env_value = os.environ.get(key)
        
        if env_value is None:
            if required:
                errors[key] = "Required environment variable is missing"
                continue
            elif default is not None:
                result[key] = default
                continue
            elif strict:
                errors[key] = "Environment variable is missing and no default provided"
                continue
            else:
                continue
        
        try:
            # Cast the value
            casted_value = _cast_value(env_value, target_type)
            
            # Apply transform if specified
            if "transform" in field_schema:
                transform = field_schema["transform"]
                if callable(transform):
                    casted_value = transform(casted_value)
            
            # Validate constraints
            constraint_error = _validate_constraints(key, casted_value, field_schema)
            if constraint_error:
                errors[key] = constraint_error
                continue
            
            result[key] = casted_value
            
        except ValueError as e:
            errors[key] = f"Type conversion failed: {e}"
        except Exception as e:
            errors[key] = f"Validation error: {e}"
    
    # Raise ValidationError if there are any errors
    if errors:
        raise ValidationError(errors)
    
    logger.info(f"Successfully validated {len(result)} environment variables")
    return result
