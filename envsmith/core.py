"""Core environment loading functionality."""

import os
import re
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple, Union
from copy import deepcopy

from ._types import EnvDict, EnvFileNotFound, InvalidEnvLine, MissingRequiredVars
from .secrets import resolve_secret_maybe

logger = logging.getLogger(__name__)

# Cache for parsed environment files
_FILE_CACHE: Dict[str, Tuple[float, EnvDict]] = {}

# Precompiled regex patterns
_VAR_EXPANSION_PATTERN = re.compile(r'\$\{([^}]+)\}')
_QUOTED_STRING_PATTERN = re.compile(r'^(["\'])(.*)\1$')

def _parse_line(line: str) -> Optional[Tuple[str, str]]:
    """
    Parse a single line from an environment file.
    
    Args:
        line: The line to parse
        
    Returns:
        Tuple of (key, value) or None if line should be skipped
        
    Raises:
        InvalidEnvLine: If the line cannot be parsed
    """
    # Strip whitespace and skip empty lines
    line = line.strip()
    if not line:
        return None
    
    # Skip comments
    if line.startswith('#'):
        return None
    
    # Find the first equals sign
    eq_pos = line.find('=')
    if eq_pos == -1:
        raise InvalidEnvLine(f"Invalid line format (missing '='): {line}")
    
    key = line[:eq_pos].strip()
    value = line[eq_pos + 1:].strip()
    
    if not key:
        raise InvalidEnvLine(f"Empty key in line: {line}")
    
    # Handle quoted values
    if value.startswith('"') and value.endswith('"'):
        # Double quoted string
        value = value[1:-1]
        value = value.replace('\\"', '"').replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
    elif value.startswith("'") and value.endswith("'"):
        # Single quoted string
        value = value[1:-1]
        value = value.replace("\\'", "'").replace('\\n', '\n').replace('\\t', '\t').replace('\\\\', '\\')
    
    return key, value

def _expand_variables(value: str, env_dict: EnvDict, os_environ: Dict[str, str]) -> str:
    """
    Expand variable references in a value string.
    
    Args:
        value: The value string to expand
        env_dict: Dictionary of already-loaded environment variables
        os_environ: Current os.environ dictionary
        
    Returns:
        The expanded value string
        
    Raises:
        InvalidEnvLine: If there's a circular reference or invalid expansion
    """
    def expand_var(match):
        var_name = match.group(1)
        
        # Check for circular references
        if var_name in _expansion_stack:
            raise InvalidEnvLine(f"Circular reference detected: {var_name}")
        
        # First check os.environ, then our loaded values
        if var_name in os_environ:
            return os_environ[var_name]
        elif var_name in env_dict:
            return env_dict[var_name]
        else:
            # Return empty string for undefined variables
            logger.warning(f"Undefined variable reference: ${var_name}")
            return ""
    
    # Track expansion stack to detect cycles
    _expansion_stack = set()
    
    # Replace all variable references
    expanded = _VAR_EXPANSION_PATTERN.sub(expand_var, value)
    
    # Check if we need to expand further (nested expansions)
    if _VAR_EXPANSION_PATTERN.search(expanded):
        # Limit recursion depth
        if len(_expansion_stack) > 10:
            raise InvalidEnvLine("Maximum expansion depth exceeded")
        
        # Recursively expand nested references
        expanded = _expand_variables(expanded, env_dict, os_environ)
    
    return expanded

def _load_single_file(file_path: Union[str, Path], expand: bool = True) -> EnvDict:
    """
    Load environment variables from a single file.
    
    Args:
        file_path: Path to the environment file
        expand: Whether to expand variable references
        
    Returns:
        Dictionary of key-value pairs
        
    Raises:
        EnvFileNotFound: If the file doesn't exist
        InvalidEnvLine: If any line cannot be parsed
    """
    file_path = Path(file_path)
    
    if not file_path.exists():
        raise EnvFileNotFound(f"Environment file not found: {file_path}")
    
    logger.debug(f"Loading environment file: {file_path}")
    
    env_dict: EnvDict = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                try:
                    parsed = _parse_line(line)
                    if parsed:
                        key, value = parsed
                        
                        # Resolve secrets if present
                        if value.startswith(('secret://', 'env://', 'file://')):
                            value = resolve_secret_maybe(value)
                        
                        env_dict[key] = value
                        
                except InvalidEnvLine as e:
                    raise InvalidEnvLine(f"Line {line_num}: {e}")
                    
    except Exception as e:
        if isinstance(e, InvalidEnvLine):
            raise
        raise EnvFileNotFound(f"Error reading file {file_path}: {e}")
    
    return env_dict

def load_env(
    paths: Union[List[str], str] = ".env",
    required: Optional[List[str]] = None,
    override: bool = False,
    expand: bool = True,
    cache: bool = True,
) -> EnvDict:
    """
    Load environment variables from one or more files.
    
    Args:
        paths: Single path or list of paths to environment files
        required: List of required environment variable names
        override: Whether to override existing os.environ values
        expand: Whether to expand variable references
        cache: Whether to use file caching
        
    Returns:
        Dictionary of loaded environment variables
        
    Raises:
        EnvFileNotFound: If no files can be loaded
        MissingRequiredVars: If required variables are missing
    """
    if isinstance(paths, str):
        paths = [paths]
    
    if not paths:
        raise ValueError("At least one path must be provided")
    
    # Get current os.environ snapshot
    os_environ = dict(os.environ)
    loaded_env: EnvDict = {}
    
    # Load from each file, later files override earlier ones
    for path in paths:
        try:
            if cache:
                # Check cache first
                file_path = Path(path).resolve()
                mtime = file_path.stat().st_mtime if file_path.exists() else 0
                
                if path in _FILE_CACHE:
                    cached_mtime, cached_env = _FILE_CACHE[path]
                    if mtime <= cached_mtime:
                        logger.debug(f"Cache hit for {path}")
                        file_env = deepcopy(cached_env)
                    else:
                        logger.debug(f"Cache miss for {path} (mtime changed)")
                        file_env = _load_single_file(path, expand)
                        _FILE_CACHE[path] = (mtime, deepcopy(file_env))
                else:
                    logger.debug(f"Cache miss for {path} (not cached)")
                    file_env = _load_single_file(path, expand)
                    _FILE_CACHE[path] = (mtime, deepcopy(file_env))
            else:
                file_env = _load_single_file(path, expand)
            
            # Expand variables if requested
            if expand:
                for key, value in file_env.items():
                    file_env[key] = _expand_variables(value, loaded_env, os_environ)
            
            # Merge with loaded environment (later files override earlier)
            loaded_env.update(file_env)
            
        except EnvFileNotFound as e:
            # If this is the only file and we have required vars, raise
            if len(paths) == 1 and required:
                raise
            logger.warning(f"Skipping file {path}: {e}")
            continue
    
    # Check if we have any required variables
    if required:
        missing_vars = [var for var in required if var not in loaded_env]
        if missing_vars:
            raise MissingRequiredVars(missing_vars)
    
    # Apply to os.environ if override is True
    if override:
        for key, value in loaded_env.items():
            os.environ[key] = value
            logger.debug(f"Set {key}={value}")
    else:
        # Only set variables that don't already exist in os.environ
        for key, value in loaded_env.items():
            if key not in os.environ:
                os.environ[key] = value
                logger.debug(f"Set {key}={value}")
            else:
                logger.debug(f"Keeping existing {key}={os.environ[key]}")
    
    logger.info(f"Loaded {len(loaded_env)} environment variables from {len(paths)} file(s)")
    return deepcopy(loaded_env)

def watch_env(
    path: Union[str, Path] = ".env",
    callback: Optional[callable] = None,
    interval: float = 1.0,
    use_watchdog: bool = True,
) -> 'EnvWatcher':
    """
    Watch an environment file for changes and reload automatically.
    
    Args:
        path: Path to the environment file to watch
        callback: Function to call when file changes
        interval: Polling interval in seconds (used if watchdog not available)
        use_watchdog: Whether to use watchdog if available
        
    Returns:
        EnvWatcher instance with stop() method
    """
    return EnvWatcher(path, callback, interval, use_watchdog)

class EnvWatcher:
    """File watcher for environment files."""
    
    def __init__(
        self,
        path: Union[str, Path],
        callback: Optional[callable] = None,
        interval: float = 1.0,
        use_watchdog: bool = True,
    ):
        self.path = Path(path)
        self.callback = callback
        self.interval = interval
        self.use_watchdog = use_watchdog
        self.running = False
        self._thread = None
        self._last_mtime = 0
        
        if self.path.exists():
            self._last_mtime = self.path.stat().st_mtime
    
    def start(self):
        """Start watching the file."""
        if self.running:
            return
        
        self.running = True
        
        if self.use_watchdog:
            try:
                self._start_watchdog()
            except ImportError:
                logger.info("watchdog not available, falling back to polling")
                self._start_polling()
        else:
            self._start_polling()
    
    def stop(self):
        """Stop watching the file."""
        self.running = False
        if self._thread and self._thread.is_alive():
            self._thread.join()
    
    def _start_watchdog(self):
        """Start watching using watchdog."""
        try:
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class EnvFileHandler(FileSystemEventHandler):
                def __init__(self, watcher):
                    self.watcher = watcher
                
                def on_modified(self, event):
                    if not event.is_directory and event.src_path == str(self.watcher.path):
                        self.watcher._handle_change()
            
            self._observer = Observer()
            handler = EnvFileHandler(self)
            self._observer.schedule(handler, str(self.path.parent), recursive=False)
            self._observer.start()
            
        except ImportError:
            raise ImportError("watchdog package not available")
    
    def _start_polling(self):
        """Start polling for file changes."""
        import threading
        
        def poll_loop():
            while self.running:
                try:
                    if self.path.exists():
                        current_mtime = self.path.stat().st_mtime
                        if current_mtime > self._last_mtime:
                            self._handle_change()
                            self._last_mtime = current_mtime
                    
                    time.sleep(self.interval)
                except Exception as e:
                    logger.error(f"Error in polling loop: {e}")
        
        self._thread = threading.Thread(target=poll_loop, daemon=True)
        self._thread.start()
    
    def _handle_change(self):
        """Handle file change event."""
        logger.info(f"Environment file changed: {self.path}")
        
        if self.callback:
            try:
                self.callback()
            except Exception as e:
                logger.error(f"Error in change callback: {e}")
        
        # Reload environment with override=True
        try:
            load_env(str(self.path), override=True)
        except Exception as e:
            logger.error(f"Error reloading environment: {e}")
