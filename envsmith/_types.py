"""Type definitions and custom exceptions for smart-envloader."""

from typing import Any, Callable, Dict, List, Optional, Union, Protocol
from typing_extensions import Literal

# Type aliases
SchemaDict = Dict[str, Union[type, Dict[str, Any]]]
ValidationResult = Dict[str, Any]
EnvDict = Dict[str, str]

# Custom exceptions
class EnvLoaderError(Exception):
    """Base exception for all envloader errors."""
    pass

class EnvFileNotFound(EnvLoaderError):
    """Raised when an environment file cannot be found."""
    pass

class InvalidEnvLine(EnvLoaderError):
    """Raised when an environment file line cannot be parsed."""
    pass

class MissingRequiredVars(EnvLoaderError):
    """Raised when required environment variables are missing."""
    
    def __init__(self, missing_vars: List[str]):
        self.missing_vars = missing_vars
        super().__init__(f"Missing required environment variables: {', '.join(missing_vars)}")

class SchemaError(EnvLoaderError):
    """Raised when there's an error with the schema definition."""
    pass

class ValidationError(EnvLoaderError):
    """Raised when environment variable validation fails."""
    
    def __init__(self, errors: Dict[str, str]):
        self.errors = errors
        error_messages = [f"{key}: {msg}" for key, msg in errors.items()]
        super().__init__(f"Validation failed:\n" + "\n".join(error_messages))
    
    def __str__(self) -> str:
        return self.args[0]

class SecretResolutionError(EnvLoaderError):
    """Raised when secret resolution fails."""
    pass

# Protocol definitions
class SecretProvider(Protocol):
    """Protocol for secret providers."""
    
    scheme: str
    
    def resolve(self, uri: str) -> str:
        """Resolve a secret URI to its value."""
        ...

# Type definitions for validation
ValidatorFunc = Callable[[Any], bool]
TransformFunc = Callable[[Any], Any]
ConstraintValue = Union[str, int, float, List[Any]]

# Schema constraint types
class SchemaConstraints:
    """Schema constraint definitions."""
    
    def __init__(
        self,
        *,
        regex: Optional[str] = None,
        choices: Optional[List[Any]] = None,
        min: Optional[Union[int, float]] = None,
        max: Optional[Union[int, float]] = None,
        min_len: Optional[int] = None,
        max_len: Optional[int] = None,
        validator: Optional[ValidatorFunc] = None,
        transform: Optional[TransformFunc] = None,
    ):
        self.regex = regex
        self.choices = choices
        self.min = min
        self.max = max
        self.min_len = min_len
        self.max_len = max_len
        self.validator = validator
        self.transform = transform

# Extended schema format
ExtendedSchemaValue = Union[
    type,
    Dict[str, Union[
        type,
        bool,
        str,
        int,
        float,
        List[Any],
        ValidatorFunc,
        TransformFunc,
        SchemaConstraints
    ]]
]
