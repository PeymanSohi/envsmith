"""Tests for the validation module."""

import os
import tempfile
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.validation import (
    validate_env, _cast_value, _validate_constraints, 
    _normalize_schema, _parse_type_annotation
)
from smart_envloader._types import ValidationError


class TestParseTypeAnnotation:
    """Test type annotation parsing."""
    
    def test_parse_basic_types(self):
        """Test parsing basic types."""
        assert _parse_type_annotation("str") == str
        assert _parse_type_annotation("int") == int
        assert _parse_type_annotation("float") == float
        assert _parse_type_annotation("bool") == bool
        assert _parse_type_annotation("list") == list
        assert _parse_type_annotation("dict") == dict
        assert _parse_type_annotation("tuple") == tuple
        assert _parse_type_annotation("set") == set
    
    def test_parse_generic_types(self):
        """Test parsing generic types."""
        from typing import List, Dict, Set, Tuple
        
        assert _parse_type_annotation("list[str]") == List[str]
        assert _parse_type_annotation("list[int]") == List[int]
        assert _parse_type_annotation("dict[str, int]") == Dict[str, int]
        assert _parse_type_annotation("set[str]") == Set[str]
        assert _parse_type_annotation("tuple[str]") == Tuple[str, ...]
    
    def test_parse_optional_types(self):
        """Test parsing Optional types."""
        from typing import Optional
        
        assert _parse_type_annotation("Optional[str]") == Optional[str]
        assert _parse_type_annotation("Optional[int]") == Optional[int]
    
    def test_parse_union_types(self):
        """Test parsing Union types."""
        from typing import Union
        
        assert _parse_type_annotation("Union[str, int]") == Union[str, int]
        assert _parse_type_annotation("Union[float, bool]") == Union[float, bool]
    
    def test_parse_literal_types(self):
        """Test parsing Literal types."""
        from typing_extensions import Literal
        
        assert _parse_type_annotation('Literal["a", "b"]') == Literal["a", "b"]
        assert _parse_type_annotation("Literal[1, 2, 3]") == Literal[1, 2, 3]
    
    def test_parse_invalid_types(self):
        """Test parsing invalid type annotations."""
        with pytest.raises(ValueError, match="Cannot parse type annotation"):
            _parse_type_annotation("invalid_type")
        
        with pytest.raises(ValueError, match="Cannot parse type annotation"):
            _parse_type_annotation("list[invalid]")


class TestCastValue:
    """Test value casting functionality."""
    
    def test_cast_basic_types(self):
        """Test casting to basic types."""
        assert _cast_value("hello", str) == "hello"
        assert _cast_value("42", int) == 42
        assert _cast_value("3.14", float) == 3.14
        assert _cast_value("true", bool) is True
        assert _cast_value("false", bool) is False
        assert _cast_value("on", bool) is True
        assert _cast_value("off", bool) is False
        assert _cast_value("yes", bool) is True
        assert _cast_value("no", bool) is False
        assert _cast_value("1", bool) is True
        assert _cast_value("0", bool) is False
    
    def test_cast_none_values(self):
        """Test casting None values."""
        assert _cast_value("none", str) == "none"  # String "none" is not None
        assert _cast_value("null", str) == "null"  # String "null" is not None
        assert _cast_value("", str) == ""
    
    def test_cast_list_types(self):
        """Test casting to list types."""
        from typing import List
        
        # Comma-separated values
        assert _cast_value("a,b,c", List[str]) == ["a", "b", "c"]
        assert _cast_value("1,2,3", List[int]) == [1, 2, 3]
        
        # JSON-like values
        assert _cast_value('["a", "b", "c"]', List[str]) == ["a", "b", "c"]
        assert _cast_value("[1, 2, 3]", List[int]) == [1, 2, 3]
    
    def test_cast_set_types(self):
        """Test casting to set types."""
        from typing import Set
        
        # Comma-separated values
        assert _cast_value("a,b,c", Set[str]) == {"a", "b", "c"}
        assert _cast_value("1,2,3", Set[int]) == {1, 2, 3}
        
        # JSON-like values
        assert _cast_value('["a", "b", "c"]', Set[str]) == {"a", "b", "c"}
        assert _cast_value("[1, 2, 3]", Set[int]) == {1, 2, 3}
    
    def test_cast_tuple_types(self):
        """Test casting to tuple types."""
        from typing import Tuple
        
        # Comma-separated values
        assert _cast_value("a,b,c", Tuple[str, ...]) == ("a", "b", "c")
        assert _cast_value("1,2,3", Tuple[int, ...]) == (1, 2, 3)
        
        # JSON-like values
        assert _cast_value('["a", "b", "c"]', Tuple[str, ...]) == ("a", "b", "c")
        assert _cast_value("[1, 2, 3]", Tuple[int, ...]) == (1, 2, 3)
    
    def test_cast_dict_types(self):
        """Test casting to dict types."""
        # JSON-like values only
        assert _cast_value('{"key": "value"}', dict) == {"key": "value"}
        assert _cast_value('{"a": 1, "b": 2}', dict) == {"a": 1, "b": 2}
        
        # Comma-separated values not supported for dicts
        with pytest.raises(ValueError, match="Dict values must be valid JSON"):
            _cast_value("key=value,other=thing", dict)
    
    def test_cast_optional_types(self):
        """Test casting to Optional types."""
        from typing import Optional
        
        assert _cast_value("hello", Optional[str]) == "hello"
        assert _cast_value("42", Optional[int]) == 42
        assert _cast_value("none", Optional[str]) == "none"
    
    def test_cast_union_types(self):
        """Test casting to Union types."""
        from typing import Union
        
        assert _cast_value("hello", Union[str, int]) == "hello"
        assert _cast_value("42", Union[str, int]) == 42
    
    def test_cast_invalid_values(self):
        """Test casting invalid values."""
        with pytest.raises(ValueError, match="Cannot convert"):
            _cast_value("not_a_number", int)
        
        with pytest.raises(ValueError, match="Cannot convert"):
            _cast_value("not_a_float", float)
        
        with pytest.raises(ValueError, match="Cannot convert"):
            _cast_value("maybe", bool)
        
        with pytest.raises(ValueError, match="Cannot parse"):
            _cast_value("invalid_json", dict)


class TestValidateConstraints:
    """Test constraint validation."""
    
    def test_validate_regex(self):
        """Test regex validation."""
        constraints = {"regex": r"^\d+$"}
        
        assert _validate_constraints("key", "123", constraints) is None
        assert _validate_constraints("key", "abc", constraints) is not None
    
    def test_validate_choices(self):
        """Test choices validation."""
        constraints = {"choices": ["a", "b", "c"]}
        
        assert _validate_constraints("key", "a", constraints) is None
        assert _validate_constraints("key", "d", constraints) is not None
    
    def test_validate_min_max_numbers(self):
        """Test min/max validation for numbers."""
        constraints = {"min": 1, "max": 10}
        
        assert _validate_constraints("key", 5, constraints) is None
        assert _validate_constraints("key", 0, constraints) is not None
        assert _validate_constraints("key", 15, constraints) is not None
    
    def test_validate_min_max_length(self):
        """Test min/max length validation."""
        constraints = {"min_len": 3, "max_len": 10}
        
        assert _validate_constraints("key", "hello", constraints) is None
        assert _validate_constraints("key", "hi", constraints) is not None
        assert _validate_constraints("key", "very_long_string", constraints) is not None
    
    def test_validate_custom_validator(self):
        """Test custom validator function."""
        def custom_validator(value):
            return len(value) > 5
        
        constraints = {"validator": custom_validator}
        
        assert _validate_constraints("key", "long_string", constraints) is None
        assert _validate_constraints("key", "short", constraints) is not None


class TestNormalizeSchema:
    """Test schema normalization."""
    
    def test_normalize_simple_schema(self):
        """Test normalizing simple schema format."""
        schema = {"PORT": int, "DEBUG": bool}
        normalized = _normalize_schema(schema)
        
        assert normalized["PORT"]["type"] == int
        assert normalized["DEBUG"]["type"] == bool
    
    def test_normalize_extended_schema(self):
        """Test normalizing extended schema format."""
        schema = {
            "PORT": {
                "type": int,
                "required": True,
                "min": 1,
                "max": 65535
            }
        }
        normalized = _normalize_schema(schema)
        
        assert normalized["PORT"]["type"] == int
        assert normalized["PORT"]["required"] is True
        assert normalized["PORT"]["min"] == 1
        assert normalized["PORT"]["max"] == 65535
    
    def test_normalize_string_types(self):
        """Test normalizing string type annotations."""
        schema = {"PORT": {"type": "int", "required": True}}
        normalized = _normalize_schema(schema)
        
        assert normalized["PORT"]["type"] == int
        assert normalized["PORT"]["required"] is True
    
    def test_normalize_invalid_schema(self):
        """Test normalizing invalid schema."""
        with pytest.raises(ValueError, match="missing 'type'"):
            _normalize_schema({"PORT": {}})
        
        with pytest.raises(ValueError, match="Invalid schema value"):
            _normalize_schema({"PORT": None})


class TestValidateEnv:
    """Test environment validation."""
    
    def test_validate_simple_schema(self):
        """Test validating with simple schema."""
        schema = {"PORT": int, "DEBUG": bool}
        
        # Set environment variables
        os.environ["PORT"] = "8080"
        os.environ["DEBUG"] = "true"
        
        try:
            result = validate_env(schema)
            assert result["PORT"] == 8080
            assert result["DEBUG"] is True
        finally:
            # Clean up
            del os.environ["PORT"]
            del os.environ["DEBUG"]
    
    def test_validate_with_defaults(self):
        """Test validating with default values."""
        schema = {
            "PORT": {"type": int, "default": 8000},
            "DEBUG": {"type": bool, "default": False}
        }
        
        result = validate_env(schema)
        assert result["PORT"] == 8000
        assert result["DEBUG"] is False
    
    def test_validate_with_required_vars(self):
        """Test validating with required variables."""
        schema = {
            "PORT": {"type": int, "required": True},
            "DEBUG": {"type": bool, "default": False}
        }
        
        # Set required variable
        os.environ["PORT"] = "8080"
        
        try:
            result = validate_env(schema)
            assert result["PORT"] == 8080
            assert result["DEBUG"] is False
        finally:
            # Clean up
            del os.environ["PORT"]
    
    def test_validate_missing_required(self):
        """Test validating with missing required variables."""
        schema = {
            "PORT": {"type": int, "required": True},
            "DEBUG": {"type": bool, "default": False}
        }
        
        with pytest.raises(ValidationError) as exc_info:
            validate_env(schema)
        
        assert "PORT" in exc_info.value.errors
        assert "Required environment variable is missing" in exc_info.value.errors["PORT"]
    
    def test_validate_with_constraints(self):
        """Test validating with constraints."""
        schema = {
            "PORT": {
                "type": int,
                "min": 1,
                "max": 65535
            },
            "HOST": {
                "type": str,
                "regex": r"^[a-zA-Z0-9.-]+$"
            }
        }
        
        # Set valid values
        os.environ["PORT"] = "8080"
        os.environ["HOST"] = "localhost"
        
        try:
            result = validate_env(schema)
            assert result["PORT"] == 8080
            assert result["HOST"] == "localhost"
        finally:
            # Clean up
            del os.environ["PORT"]
            del os.environ["HOST"]
    
    def test_validate_constraint_violation(self):
        """Test validating with constraint violations."""
        schema = {
            "PORT": {
                "type": int,
                "min": 1,
                "max": 65535
            }
        }
        
        # Set invalid value
        os.environ["PORT"] = "70000"
        
        try:
            with pytest.raises(ValidationError) as exc_info:
                validate_env(schema)
            
            assert "PORT" in exc_info.value.errors
            assert "greater than maximum" in exc_info.value.errors["PORT"]
        finally:
            # Clean up
            del os.environ["PORT"]
    
    def test_validate_type_conversion_error(self):
        """Test validating with type conversion errors."""
        schema = {"PORT": int}
        
        # Set invalid value
        os.environ["PORT"] = "not_a_number"
        
        try:
            with pytest.raises(ValidationError) as exc_info:
                validate_env(schema)
            
            assert "PORT" in exc_info.value.errors
            assert "Type conversion failed" in exc_info.value.errors["PORT"]
        finally:
            # Clean up
            del os.environ["PORT"]
    
    def test_validate_strict_mode(self):
        """Test validating in strict mode."""
        schema = {"PORT": int}
        
        # No environment variables set
        with pytest.raises(ValidationError) as exc_info:
            validate_env(schema, strict=True)
        
        assert "PORT" in exc_info.value.errors
        assert "missing and no default provided" in exc_info.value.errors["PORT"]
    
    def test_validate_non_strict_mode(self):
        """Test validating in non-strict mode."""
        schema = {"PORT": int}
        
        # No environment variables set, should not raise
        result = validate_env(schema, strict=False)
        assert result == {}
    
    def test_validate_with_transform(self):
        """Test validating with transform function."""
        def transform(value):
            return value.upper()
        
        schema = {
            "HOST": {
                "type": str,
                "transform": transform
            }
        }
        
        os.environ["HOST"] = "localhost"
        
        try:
            result = validate_env(schema)
            assert result["HOST"] == "LOCALHOST"
        finally:
            del os.environ["HOST"]
