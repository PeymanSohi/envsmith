"""Tests for the watch functionality."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

from smart_envloader.core import watch_env, EnvWatcher


class TestEnvWatcher:
    """Test environment watcher functionality."""
    
    def test_watcher_creation(self):
        """Test creating a watcher."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name)
                assert watcher.path == Path(f.name)
                assert not watcher.running
                assert watcher.callback is None
                assert watcher.interval == 1.0
                assert watcher.use_watchdog is True
            finally:
                Path(f.name).unlink()
    
    def test_watcher_with_callback(self):
        """Test creating a watcher with callback."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, callback=callback)
                assert watcher.callback == callback
            finally:
                Path(f.name).unlink()
    
    def test_watcher_start_stop(self):
        """Test starting and stopping the watcher."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name)
                assert not watcher.running
                
                # Start watching
                watcher.start()
                assert watcher.running
                
                # Stop watching
                watcher.stop()
                assert not watcher.running
            finally:
                Path(f.name).unlink()
    
    def test_watcher_double_start(self):
        """Test starting an already running watcher."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name)
                watcher.start()
                assert watcher.running
                
                # Start again should not change state
                watcher.start()
                assert watcher.running
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    def test_watcher_callback_execution(self):
        """Test that callback is executed on file change."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, callback=callback)
                watcher.start()
                
                # Simulate file change
                watcher._handle_change()
                assert callback_called
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    def test_watcher_callback_exception_handling(self):
        """Test that callback exceptions don't crash the watcher."""
        def callback():
            raise Exception("Callback error")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, callback=callback)
                watcher.start()
                
                # Simulate file change - should not crash
                watcher._handle_change()
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    def test_watcher_polling_fallback(self):
        """Test polling fallback when watchdog is not available."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, use_watchdog=False)
                watcher.start()
                assert watcher.running
                
                # Give it a moment to start polling
                time.sleep(0.1)
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    @patch('smart_envloader.core.watchdog')
    def test_watcher_watchdog_import_error(self, mock_watchdog):
        """Test fallback to polling when watchdog import fails."""
        mock_watchdog.observers.side_effect = ImportError("No module named 'watchdog'")
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, use_watchdog=True)
                watcher.start()
                assert watcher.running
                
                # Should fall back to polling
                time.sleep(0.1)
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    def test_watcher_file_change_detection(self):
        """Test that file changes are detected."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, use_watchdog=False, interval=0.1)
                original_mtime = watcher._last_mtime
                
                watcher.start()
                
                # Wait a bit for polling to start
                time.sleep(0.2)
                
                # Modify the file
                with open(f.name, 'a') as f:
                    f.write("KEY2=value2\n")
                
                # Wait for change detection
                time.sleep(0.3)
                
                # Check that mtime was updated
                assert watcher._last_mtime > original_mtime
                
                watcher.stop()
            finally:
                Path(f.name).unlink()
    
    def test_watcher_handle_change_method(self):
        """Test the _handle_change method."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name, callback=callback)
                
                # Test without callback
                watcher._handle_change()
                assert not callback_called
                
                # Test with callback
                watcher.callback = callback
                watcher._handle_change()
                assert callback_called
                
            finally:
                Path(f.name).unlink()


class TestWatchEnvFunction:
    """Test the watch_env function."""
    
    def test_watch_env_returns_watcher(self):
        """Test that watch_env returns an EnvWatcher instance."""
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(f.name)
                assert isinstance(watcher, EnvWatcher)
                assert watcher.path == Path(f.name)
            finally:
                Path(f.name).unlink()
    
    def test_watch_env_with_custom_parameters(self):
        """Test watch_env with custom parameters."""
        callback_called = False
        
        def callback():
            nonlocal callback_called
            callback_called = True
        
        with tempfile.NamedTemporaryFile(mode='w', delete=False) as f:
            f.write("KEY1=value1\n")
            f.flush()
            
            try:
                watcher = watch_env(
                    path=f.name,
                    callback=callback,
                    interval=2.0,
                    use_watchdog=False
                )
                
                assert watcher.callback == callback
                assert watcher.interval == 2.0
                assert watcher.use_watchdog is False
                
                # Test callback
                watcher._handle_change()
                assert callback_called
                
            finally:
                Path(f.name).unlink()
