"""Tests for the schema loader module."""

import json
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.schema_loader import load_schema, _load_yaml_schema, _load_json_schema
from smart_envloader._types import SchemaError


class TestLoadSchema:
    """Test schema loading functionality."""
    
    def test_load_yaml_schema(self):
        """Test loading YAML schema."""
        yaml_content = """
        PORT:
          type: int
          required: true
        DEBUG:
          type: bool
          default: false
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                schema = load_schema(f.name)
                assert "PORT" in schema
                assert "DEBUG" in schema
                assert schema["PORT"]["type"] == "int"
                assert schema["DEBUG"]["type"] == "bool"
            finally:
                Path(f.name).unlink()
    
    def test_load_json_schema(self):
        """Test loading JSON schema."""
        json_content = {
            "PORT": {
                "type": "int",
                "required": True
            },
            "DEBUG": {
                "type": "bool",
                "default": False
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            
            try:
                schema = load_schema(f.name)
                assert "PORT" in schema
                assert "DEBUG" in schema
                assert schema["PORT"]["type"] == "int"
                assert schema["DEBUG"]["type"] == "bool"
            finally:
                Path(f.name).unlink()
    
    def test_load_unsupported_format(self):
        """Test loading unsupported file format."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write("some content")
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="Unsupported schema file format"):
                    load_schema(f.name)
            finally:
                Path(f.name).unlink()
    
    def test_load_nonexistent_file(self):
        """Test loading non-existent file."""
        with pytest.raises(SchemaError, match="Schema file not found"):
            load_schema("nonexistent.yaml")


class TestLoadYamlSchema:
    """Test YAML schema loading."""
    
    def test_load_valid_yaml(self):
        """Test loading valid YAML."""
        yaml_content = """
        PORT: int
        DEBUG: bool
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                schema = _load_yaml_schema(Path(f.name))
                assert "PORT" in schema
                assert "DEBUG" in schema
            finally:
                Path(f.name).unlink()
    
    def test_load_invalid_yaml(self):
        """Test loading invalid YAML."""
        invalid_yaml = """
        PORT:
          type: int
          required: true
        DEBUG:
          type: bool
          default: false
        - invalid: yaml
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(invalid_yaml)
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="Invalid YAML"):
                    _load_yaml_schema(Path(f.name))
            finally:
                Path(f.name).unlink()
    
    def test_load_yaml_not_dict(self):
        """Test loading YAML that's not a dictionary."""
        yaml_content = "not a dict"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="Schema must be a dictionary"):
                    _load_yaml_schema(Path(f.name))
            finally:
                Path(f.name).unlink()
    
    @patch('smart_envloader.schema_loader.yaml')
    def test_load_yaml_import_error(self, mock_yaml):
        """Test loading YAML when PyYAML is not available."""
        mock_yaml.safe_load.side_effect = ImportError("No module named 'yaml'")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write("PORT: int")
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="PyYAML is required"):
                    _load_yaml_schema(Path(f.name))
            finally:
                Path(f.name).unlink()


class TestLoadJsonSchema:
    """Test JSON schema loading."""
    
    def test_load_valid_json(self):
        """Test loading valid JSON."""
        json_content = {
            "PORT": {
                "type": "int",
                "required": True
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_content, f)
            f.flush()
            
            try:
                schema = _load_json_schema(Path(f.name))
                assert "PORT" in schema
                assert schema["PORT"]["type"] == "int"
            finally:
                Path(f.name).unlink()
    
    def test_load_invalid_json(self):
        """Test loading invalid JSON."""
        invalid_json = """
        {
            "PORT": {
                "type": "int",
                "required": true
            },
            "DEBUG": {
                "type": "bool",
                "default": false
            }
            "missing": "comma"
        }
        """
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(invalid_json)
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="Invalid JSON"):
                    _load_json_schema(Path(f.name))
            finally:
                Path(f.name).unlink()
    
    def test_load_json_not_dict(self):
        """Test loading JSON that's not a dictionary."""
        json_content = "not a dict"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            f.flush()
            
            try:
                with pytest.raises(SchemaError, match="Schema must be a dictionary"):
                    _load_json_schema(Path(f.name))
            finally:
                Path(f.name).unlink()


class TestNormalizeSchemaDict:
    """Test schema dictionary normalization."""
    
    def test_normalize_simple_schema(self):
        """Test normalizing simple schema format."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": int,
            "DEBUG": bool
        }
        
        normalized = _normalize_schema_dict(schema, "test.yaml")
        assert normalized["PORT"]["type"] == int
        assert normalized["DEBUG"]["type"] == bool
    
    def test_normalize_extended_schema(self):
        """Test normalizing extended schema format."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": int,
                "required": True,
                "min": 1,
                "max": 65535
            }
        }
        
        normalized = _normalize_schema_dict(schema, "test.yaml")
        assert normalized["PORT"]["type"] == int
        assert normalized["PORT"]["required"] is True
        assert normalized["PORT"]["min"] == 1
        assert normalized["PORT"]["max"] == 65535
    
    def test_normalize_string_types(self):
        """Test normalizing string type annotations."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": "int",
                "required": True
            }
        }
        
        normalized = _normalize_schema_dict(schema, "test.yaml")
        assert normalized["PORT"]["type"] == "int"  # Will be parsed later
        assert normalized["PORT"]["required"] is True
    
    def test_normalize_missing_type(self):
        """Test normalizing schema with missing type field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "required": True
            }
        }
        
        with pytest.raises(SchemaError, match="missing 'type'"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_schema_value(self):
        """Test normalizing invalid schema values."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": None
        }
        
        with pytest.raises(SchemaError, match="Invalid schema value"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_key_type(self):
        """Test normalizing schema with invalid key types."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            123: "int"  # Invalid key type
        }
        
        with pytest.raises(SchemaError, match="Schema keys must be strings"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_type_field(self):
        """Test normalizing schema with invalid type field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": 123,  # Invalid type value
                "required": True
            }
        }
        
        with pytest.raises(SchemaError, match="type must be string or type"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_boolean_field(self):
        """Test normalizing schema with invalid boolean field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": int,
                "required": "not a boolean"
            }
        }
        
        with pytest.raises(SchemaError, match="must be boolean"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_numeric_field(self):
        """Test normalizing schema with invalid numeric field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": int,
                "min": "not a number"
            }
        }
        
        with pytest.raises(SchemaError, match="must be numeric"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_choices_field(self):
        """Test normalizing schema with invalid choices field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "MODE": {
                "type": str,
                "choices": "not a list"
            }
        }
        
        with pytest.raises(SchemaError, match="must be list or tuple"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_empty_choices(self):
        """Test normalizing schema with empty choices."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "MODE": {
                "type": str,
                "choices": []
            }
        }
        
        with pytest.raises(SchemaError, match="cannot be empty"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_validator_field(self):
        """Test normalizing schema with invalid validator field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": int,
                "validator": "not callable"
            }
        }
        
        with pytest.raises(SchemaError, match="must be callable"):
            _normalize_schema_dict(schema, "test.yaml")
    
    def test_normalize_invalid_transform_field(self):
        """Test normalizing schema with invalid transform field."""
        from smart_envloader.schema_loader import _normalize_schema_dict
        
        schema = {
            "PORT": {
                "type": int,
                "transform": "not callable"
            }
        }
        
        with pytest.raises(SchemaError, match="must be callable"):
            _normalize_schema_dict(schema, "test.yaml")
