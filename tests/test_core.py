"""Tests for the core module."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.core import load_env, watch_env, _parse_line, _expand_variables
from smart_envloader._types import EnvFileNotFound, InvalidEnvLine, MissingRequiredVars


class TestParseLine:
    """Test line parsing functionality."""
    
    def test_parse_basic_key_value(self):
        """Test parsing basic key=value pairs."""
        result = _parse_line("KEY=value")
        assert result == ("KEY", "value")
    
    def test_parse_with_spaces(self):
        """Test parsing with spaces around equals sign."""
        result = _parse_line(" KEY = value ")
        assert result == ("KEY", "value")
    
    def test_parse_quoted_value(self):
        """Test parsing quoted values."""
        result = _parse_line('KEY="quoted value"')
        assert result == ("KEY", "quoted value")
        
        result = _parse_line("KEY='single quoted'")
        assert result == ("KEY", "single quoted")
    
    def test_parse_escaped_quotes(self):
        """Test parsing escaped quotes."""
        result = _parse_line('KEY="He said \"Hello\""')
        assert result == ("KEY", 'He said "Hello"')
        
        result = _parse_line("KEY='He said \\'Hello\\''")
        assert result == ("KEY", "He said 'Hello'")
    
    def test_parse_escaped_chars(self):
        """Test parsing escaped characters."""
        result = _parse_line('KEY="Line 1\\nLine 2"')
        assert result == ("KEY", "Line 1\nLine 2")
        
        result = _parse_line('KEY="Tab\\tseparated"')
        assert result == ("KEY", "Tab\tseparated")
    
    def test_parse_comment(self):
        """Test parsing comment lines."""
        result = _parse_line("# This is a comment")
        assert result is None
    
    def test_parse_blank_line(self):
        """Test parsing blank lines."""
        result = _parse_line("")
        assert result is None
        
        result = _parse_line("   ")
        assert result is None
    
    def test_parse_invalid_format(self):
        """Test parsing invalid line formats."""
        with pytest.raises(InvalidEnvLine, match="missing '='"):
            _parse_line("INVALID_LINE")
        
        with pytest.raises(InvalidEnvLine, match="Empty key"):
            _parse_line("=value")


class TestExpandVariables:
    """Test variable expansion functionality."""
    
    def test_expand_simple_variable(self):
        """Test expanding a simple variable reference."""
        env_dict = {"OTHER_KEY": "other_value"}
        os_environ = {"EXISTING_VAR": "existing_value"}
        
        result = _expand_variables("${OTHER_KEY}", env_dict, os_environ)
        assert result == "other_value"
    
    def test_expand_from_os_environ(self):
        """Test expanding from os.environ."""
        env_dict = {}
        os_environ = {"EXISTING_VAR": "existing_value"}
        
        result = _expand_variables("${EXISTING_VAR}", env_dict, os_environ)
        assert result == "existing_value"
    
    def test_expand_nested_variables(self):
        """Test expanding nested variable references."""
        env_dict = {"BASE_URL": "http://localhost:8080", "PORT": "8080"}
        os_environ = {}
        
        result = _expand_variables("${BASE_URL}/api", env_dict, os_environ)
        assert result == "http://localhost:8080/api"
    
    def test_expand_undefined_variable(self):
        """Test expanding undefined variables."""
        env_dict = {}
        os_environ = {}
        
        result = _expand_variables("${UNDEFINED_VAR}", env_dict, os_environ)
        assert result == ""
    
    def test_expand_no_variables(self):
        """Test expanding strings with no variables."""
        env_dict = {}
        os_environ = {}
        
        result = _expand_variables("plain text", env_dict, os_environ)
        assert result == "plain text"


class TestLoadEnv:
    """Test environment loading functionality."""
    
    def test_load_single_file(self):
        """Test loading from a single file."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\n")
            f.flush()
            
            result = load_env(f.name)
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"
            
        os.unlink(f.name)
    
    def test_load_multiple_files(self):
        """Test loading from multiple files with precedence."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f1:
            f1.write("KEY1=value1\nKEY2=value2\n")
            f1.flush()
            
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as f2:
                f2.write("KEY2=override\nKEY3=value3\n")
                f2.flush()
                
                result = load_env([f1.name, f2.name])
                assert result["KEY1"] == "value1"
                assert result["KEY2"] == "override"  # Later file wins
                assert result["KEY3"] == "value3"
                
            os.unlink(f2.name)
        os.unlink(f1.name)
    
    def test_load_with_comments_and_blanks(self):
        """Test loading with comments and blank lines."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("# Comment line\n\nKEY1=value1\n  # Inline comment\nKEY2=value2\n")
            f.flush()
            
            result = load_env(f.name)
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"
            assert len(result) == 2
            
        os.unlink(f.name)
    
    def test_load_with_variable_expansion(self):
        """Test loading with variable expansion."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("BASE_URL=http://localhost\nAPI_URL=${BASE_URL}/api\n")
            f.flush()
            
            result = load_env(f.name, expand=True)
            assert result["BASE_URL"] == "http://localhost"
            assert result["API_URL"] == "http://localhost/api"
            
        os.unlink(f.name)
    
    def test_load_without_expansion(self):
        """Test loading without variable expansion."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("BASE_URL=http://localhost\nAPI_URL=${BASE_URL}/api\n")
            f.flush()
            
            result = load_env(f.name, expand=False)
            assert result["BASE_URL"] == "http://localhost"
            assert result["API_URL"] == "${BASE_URL}/api"
            
        os.unlink(f.name)
    
    def test_load_with_required_vars(self):
        """Test loading with required variables."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\n")
            f.flush()
            
            result = load_env(f.name, required=["KEY1", "KEY2"])
            assert result["KEY1"] == "value1"
            assert result["KEY2"] == "value2"
            
        os.unlink(f.name)
    
    def test_load_missing_required_vars(self):
        """Test loading with missing required variables."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            with pytest.raises(MissingRequiredVars) as exc_info:
                load_env(f.name, required=["KEY1", "MISSING_KEY"])
            
            assert "MISSING_KEY" in exc_info.value.missing_vars
            
        os.unlink(f.name)
    
    def test_load_file_not_found(self):
        """Test loading non-existent file."""
        with pytest.raises(EnvFileNotFound):
            load_env("nonexistent.env")
    
    def test_load_with_override(self):
        """Test loading with override enabled."""
        # Set existing environment variable
        os.environ["EXISTING_KEY"] = "existing_value"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("EXISTING_KEY=new_value\n")
            f.flush()
            
            result = load_env(f.name, override=True)
            assert result["EXISTING_KEY"] == "new_value"
            assert os.environ["EXISTING_KEY"] == "new_value"
            
        os.unlink(f.name)
        
        # Clean up
        del os.environ["EXISTING_KEY"]
    
    def test_load_without_override(self):
        """Test loading without override (preserve existing)."""
        # Set existing environment variable
        os.environ["EXISTING_KEY"] = "existing_value"
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("EXISTING_KEY=new_value\n")
            f.flush()
            
            result = load_env(f.name, override=False)
            assert result["EXISTING_KEY"] == "new_value"
            # Should not override existing
            assert os.environ["EXISTING_KEY"] == "existing_value"
            
        os.unlink(f.name)
        
        # Clean up
        del os.environ["EXISTING_KEY"]
    
    def test_load_with_caching(self):
        """Test loading with caching enabled."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            # First load
            result1 = load_env(f.name, cache=True)
            assert result1["KEY1"] == "value1"
            
            # Second load should use cache
            result2 = load_env(f.name, cache=True)
            assert result2["KEY1"] == "value1"
            
        os.unlink(f.name)
    
    def test_load_without_caching(self):
        """Test loading without caching."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            # First load
            result1 = load_env(f.name, cache=False)
            assert result1["KEY1"] == "value1"
            
            # Second load should not use cache
            result2 = load_env(f.name, cache=False)
            assert result2["KEY1"] == "value1"
            
        os.unlink(f.name)


class TestWatchEnv:
    """Test environment watching functionality."""
    
    def test_watch_env_creation(self):
        """Test creating an environment watcher."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            watcher = watch_env(f.name)
            assert watcher.path == Path(f.name)
            assert not watcher.running
            
        os.unlink(f.name)
    
    def test_watch_env_start_stop(self):
        """Test starting and stopping the watcher."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            watcher = watch_env(f.name)
            assert not watcher.running
            
            # Start watching
            watcher.start()
            assert watcher.running
            
            # Stop watching
            watcher.stop()
            assert not watcher.running
            
        os.unlink(f.name)
    
    def test_watch_env_callback(self):
        """Test watcher callback functionality."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            watcher = watch_env(f.name, callback=callback)
            watcher.start()
            
            # Simulate file change
            watcher._handle_change()
            assert callback_called
            
            watcher.stop()
            
        os.unlink(f.name)
