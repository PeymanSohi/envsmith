"""Tests for the CLI module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.cli import main, cmd_check, cmd_validate, cmd_print, setup_logging
from smart_envloader._types import (
    MissingRequiredVars, ValidationError, SchemaError, 
    EnvFileNotFound, SecretResolutionError
)


class TestSetupLogging:
    """Test logging setup."""
    
    def test_setup_logging_verbose(self):
        """Test verbose logging setup."""
        setup_logging(verbose=True, quiet=False)
        # Should not raise any errors
    
    def test_setup_logging_quiet(self):
        """Test quiet logging setup."""
        setup_logging(verbose=False, quiet=True)
        # Should not raise any errors
    
    def test_setup_logging_default(self):
        """Test default logging setup."""
        setup_logging(verbose=False, quiet=False)
        # Should not raise any errors


class TestCmdCheck:
    """Test check command."""
    
    def test_cmd_check_success(self):
        """Test successful check command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\n")
            f.flush()
            
            try:
                args = MagicMock()
                args.file = [f.name]
                args.require = ["KEY1", "KEY2"]
                args.override = False
                args.expand = True
                
                result = cmd_check(args)
                assert result == 0
            finally:
                Path(f.name).unlink()
    
    def test_cmd_check_missing_required(self):
        """Test check command with missing required variables."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                args = MagicMock()
                args.file = [f.name]
                args.require = ["KEY1", "MISSING_KEY"]
                args.override = False
                args.expand = True
                
                result = cmd_check(args)
                assert result == 3  # Missing required vars
            finally:
                Path(f.name).unlink()
    
    def test_cmd_check_file_not_found(self):
        """Test check command with file not found."""
        args = MagicMock()
        args.file = ["nonexistent.env"]
        args.require = None
        args.override = False
        args.expand = True
        
        result = cmd_check(args)
        assert result == 5  # IO error


class TestCmdValidate:
    """Test validate command."""
    
    def test_cmd_validate_success(self):
        """Test successful validate command."""
        # Create schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as schema_f:
            schema_f.write("""
            PORT:
              type: int
              required: true
            DEBUG:
              type: bool
              default: false
            """)
            schema_f.flush()
            
            # Create env file
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as env_f:
                env_f.write("PORT=8080\n")
                env_f.flush()
                
                try:
                    args = MagicMock()
                    args.schema = schema_f.name
                    args.file = [env_f.name]
                    args.format = "table"
                    args.override = False
                    args.expand = True
                    args.strict = True
                    
                    result = cmd_validate(args)
                    assert result == 0
                finally:
                    Path(env_f.name).unlink()
            
            Path(schema_f.name).unlink()
    
    def test_cmd_validate_validation_error(self):
        """Test validate command with validation error."""
        # Create schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as schema_f:
            schema_f.write("""
            PORT:
              type: int
              required: true
            """)
            schema_f.flush()
            
            # Create env file with invalid value
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as env_f:
                env_f.write("PORT=not_a_number\n")
                env_f.flush()
                
                try:
                    args = MagicMock()
                    args.schema = schema_f.name
                    args.file = [env_f.name]
                    args.format = "table"
                    args.override = False
                    args.expand = True
                    args.strict = True
                    
                    result = cmd_validate(args)
                    assert result == 2  # Validation error
                finally:
                    Path(env_f.name).unlink()
            
            Path(schema_f.name).unlink()
    
    def test_cmd_validate_schema_error(self):
        """Test validate command with schema error."""
        # Create invalid schema file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as schema_f:
            schema_f.write("""
            PORT:
              # Missing type field
              required: true
            """)
            schema_f.flush()
            
            # Create env file
            with tempfile.NamedTemporaryFile(mode='w', delete=False) as env_f:
                env_f.write("PORT=8080\n")
                env_f.flush()
                
                try:
                    args = MagicMock()
                    args.schema = schema_f.name
                    args.file = [env_f.name]
                    args.format = "table"
                    args.override = False
                    args.expand = True
                    args.strict = True
                    
                    result = cmd_validate(args)
                    assert result == 4  # Schema error
                finally:
                    Path(env_f.name).unlink()
            
            Path(schema_f.name).unlink()


class TestCmdPrint:
    """Test print command."""
    
    def test_cmd_print_success(self):
        """Test successful print command."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\nKEY2=value2\n")
            f.flush()
            
            try:
                args = MagicMock()
                args.file = [f.name]
                args.format = "table"
                args.override = False
                args.expand = True
                args.all = False
                
                result = cmd_print(args)
                assert result == 0
            finally:
                Path(f.name).unlink()
    
    def test_cmd_print_file_not_found(self):
        """Test print command with file not found."""
        args = MagicMock()
        args.file = ["nonexistent.env"]
        args.format = "table"
        args.override = False
        args.expand = True
        args.all = False
        
        result = cmd_print(args)
        assert result == 5  # IO error


class TestMain:
    """Test main CLI function."""
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'check', '--file', '.env'])
    @patch('smart_envloader.cli.cmd_check')
    def test_main_check_command(self, mock_cmd_check):
        """Test main function with check command."""
        mock_cmd_check.return_value = 0
        
        result = main()
        assert result == 0
        mock_cmd_check.assert_called_once()
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'validate', '--schema', 'schema.yaml', '--file', '.env'])
    @patch('smart_envloader.cli.cmd_validate')
    def test_main_validate_command(self, mock_cmd_validate):
        """Test main function with validate command."""
        mock_cmd_validate.return_value = 0
        
        result = main()
        assert result == 0
        mock_cmd_validate.assert_called_once()
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'print', '--file', '.env'])
    @patch('smart_envloader.cli.cmd_print')
    def test_main_print_command(self, mock_cmd_print):
        """Test main function with print command."""
        mock_cmd_print.return_value = 0
        
        result = main()
        assert result == 0
        mock_cmd_print.assert_called_once()
    
    @patch('smart_envloader.cli.sys.argv', ['envloader'])
    def test_main_no_command(self):
        """Test main function with no command."""
        result = main()
        assert result == 1
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'unknown'])
    def test_main_unknown_command(self):
        """Test main function with unknown command."""
        result = main()
        assert result == 1
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'check', '--file', '.env'])
    @patch('smart_envloader.cli.cmd_check')
    def test_main_keyboard_interrupt(self, mock_cmd_check):
        """Test main function with keyboard interrupt."""
        mock_cmd_check.side_effect = KeyboardInterrupt()
        
        result = main()
        assert result == 130
    
    @patch('smart_envloader.cli.sys.argv', ['envloader', 'check', '--file', '.env'])
    @patch('smart_envloader.cli.cmd_check')
    def test_main_unexpected_error(self, mock_cmd_check):
        """Test main function with unexpected error."""
        mock_cmd_check.side_effect = Exception("Unexpected error")
        
        result = main()
        assert result == 1
