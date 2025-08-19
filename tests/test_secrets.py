"""Tests for the secrets module."""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.secrets import (
    resolve_secret_maybe, register_provider, PROVIDERS,
    EnvSecretProvider, FileSecretProvider
)
from smart_envloader._types import SecretResolutionError


class TestEnvSecretProvider:
    """Test environment secret provider."""
    
    def test_resolve_env_secret(self):
        """Test resolving environment secret."""
        provider = EnvSecretProvider()
        
        # Set environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        try:
            result = provider.resolve("env://TEST_VAR")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]
    
    def test_resolve_env_secret_alternative_format(self):
        """Test resolving environment secret with alternative format."""
        provider = EnvSecretProvider()
        
        # Set environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        try:
            result = provider.resolve("secret://env/TEST_VAR")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]
    
    def test_resolve_env_secret_missing(self):
        """Test resolving missing environment secret."""
        provider = EnvSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="is not set"):
            provider.resolve("env://MISSING_VAR")
    
    def test_resolve_env_secret_empty_name(self):
        """Test resolving environment secret with empty name."""
        provider = EnvSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="Empty environment variable name"):
            provider.resolve("env://")
    
    def test_resolve_env_secret_invalid_format(self):
        """Test resolving environment secret with invalid format."""
        provider = EnvSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="Invalid env URI format"):
            provider.resolve("invalid://format")


class TestFileSecretProvider:
    """Test file secret provider."""
    
    def test_resolve_file_secret(self):
        """Test resolving file secret."""
        provider = FileSecretProvider()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("secret content")
            f.flush()
            
            try:
                result = provider.resolve(f"file://{f.name}")
                assert result == "secret content"
            finally:
                Path(f.name).unlink()
    
    def test_resolve_file_secret_alternative_format(self):
        """Test resolving file secret with alternative format."""
        provider = FileSecretProvider()
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("secret content")
            f.flush()
            
            try:
                result = provider.resolve(f"secret://file/{f.name}")
                assert result == "secret content"
            finally:
                Path(f.name).unlink()
    
    def test_resolve_file_secret_nonexistent(self):
        """Test resolving non-existent file secret."""
        provider = FileSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="does not exist"):
            provider.resolve("file:///nonexistent/file")
    
    def test_resolve_file_secret_empty_path(self):
        """Test resolving file secret with empty path."""
        provider = FileSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="Empty file path"):
            provider.resolve("file://")
    
    def test_resolve_file_secret_invalid_format(self):
        """Test resolving file secret with invalid format."""
        provider = FileSecretProvider()
        
        with pytest.raises(SecretResolutionError, match="Invalid file URI format"):
            provider.resolve("invalid://format")


class TestRegisterProvider:
    """Test provider registration."""
    
    def test_register_valid_provider(self):
        """Test registering a valid provider."""
        class TestProvider:
            scheme = "test"
            
            def resolve(self, uri):
                return "test_value"
        
        # Clear existing providers
        original_providers = PROVIDERS.copy()
        PROVIDERS.clear()
        
        try:
            register_provider(TestProvider())
            assert "test" in PROVIDERS
            assert PROVIDERS["test"].scheme == "test"
        finally:
            # Restore original providers
            PROVIDERS.clear()
            PROVIDERS.update(original_providers)
    
    def test_register_provider_missing_scheme(self):
        """Test registering provider without scheme."""
        class InvalidProvider:
            def resolve(self, uri):
                return "test_value"
        
        with pytest.raises(ValueError, match="must have a 'scheme' attribute"):
            register_provider(InvalidProvider())
    
    def test_register_provider_missing_resolve(self):
        """Test registering provider without resolve method."""
        class InvalidProvider:
            scheme = "test"
        
        with pytest.raises(ValueError, match="must have a 'resolve' method"):
            register_provider(InvalidProvider())
    
    def test_register_provider_non_callable_resolve(self):
        """Test registering provider with non-callable resolve."""
        class InvalidProvider:
            scheme = "test"
            resolve = "not callable"
        
        with pytest.raises(ValueError, match="must have a 'resolve' method"):
            register_provider(InvalidProvider())


class TestResolveSecretMaybe:
    """Test secret resolution."""
    
    def test_resolve_not_secret_uri(self):
        """Test resolving non-secret URI."""
        result = resolve_secret_maybe("plain_value")
        assert result == "plain_value"
    
    def test_resolve_env_secret(self):
        """Test resolving environment secret."""
        # Set environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        try:
            result = resolve_secret_maybe("env://TEST_VAR")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]
    
    def test_resolve_file_secret(self):
        """Test resolving file secret."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("secret content")
            f.flush()
            
            try:
                result = resolve_secret_maybe(f"file://{f.name}")
                assert result == "secret content"
            finally:
                Path(f.name).unlink()
    
    def test_resolve_secret_uri(self):
        """Test resolving secret URI format."""
        # Set environment variable
        os.environ["TEST_VAR"] = "test_value"
        
        try:
            result = resolve_secret_maybe("secret://env/TEST_VAR")
            assert result == "test_value"
        finally:
            del os.environ["TEST_VAR"]
    
    def test_resolve_secret_uri_invalid_format(self):
        """Test resolving secret URI with invalid format."""
        with pytest.raises(SecretResolutionError, match="Invalid secret URI format"):
            resolve_secret_maybe("secret://invalid")
    
    def test_resolve_unknown_scheme(self):
        """Test resolving with unknown scheme."""
        with pytest.raises(SecretResolutionError, match="No provider registered for scheme"):
            resolve_secret_maybe("unknown://something")
    
    def test_resolve_provider_error(self):
        """Test resolving when provider raises error."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("secret content")
            f.flush()
            
            try:
                # This should work
                result = resolve_secret_maybe(f"file://{f.name}")
                assert result == "secret content"
            finally:
                Path(f.name).unlink()


class TestBuiltinProviders:
    """Test built-in providers are registered."""
    
    def test_env_provider_registered(self):
        """Test that env provider is registered."""
        assert "env" in PROVIDERS
        assert isinstance(PROVIDERS["env"], EnvSecretProvider)
    
    def test_file_provider_registered(self):
        """Test that file provider is registered."""
        assert "file" in PROVIDERS
        assert isinstance(PROVIDERS["file"], FileSecretProvider)
