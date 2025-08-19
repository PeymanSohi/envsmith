# Smart EnvLoader

[![PyPI version](https://badge.fury.io/py/smart-envloader.svg)](https://badge.fury.io/py/smart-envloader)
[![Python versions](https://img.shields.io/pypi/pyversions/smart-envloader.svg)](https://pypi.org/project/smart-envloader/)
[![License](https://img.shields.io/pypi/l/smart-envloader.svg)](https://pypi.org/project/smart-envloader/)
[![Tests](https://github.com/smart-envloader/smart-envloader/workflows/tests/badge.svg)](https://github.com/smart-envloader/smart-envloader/actions)
[![Coverage](https://codecov.io/gh/smart-envloader/smart-envloader/branch/main/graph/badge.svg)](https://codecov.io/gh/smart-envloader/smart-envloader)

A production-ready Python package for loading, validating, and managing environment variables with support for multi-file loading, schema validation, secrets resolution, and more.

## Features

- **Multi-file loading**: Load from one or multiple `.env` files with precedence (later files override earlier ones)
- **Advanced validation**: Support for complex types, constraints, and custom validators
- **Schema support**: Define schemas in YAML or JSON with type annotations
- **Secrets resolution**: Pluggable secret providers for secure configuration
- **Auto-reload**: Watch files for changes and reload automatically
- **Framework integrations**: FastAPI and Django support out of the box
- **CLI tool**: Command-line interface for environment management
- **High performance**: Caching and file change detection
- **Type hints**: Full type annotation support

## Installation

### Basic Installation

```bash
pip install smart-envloader
```

### With Optional Dependencies

```bash
# For file watching (recommended)
pip install smart-envloader[watch]

# For FastAPI integration
pip install smart-envloader[fastapi]

# For Django integration
pip install smart-envloader[django]

# For development
pip install smart-envloader[dev]
```

## Quick Start

### Basic Usage

```python
from smart_envloader import load_env, validate_env

# Load environment variables
env_vars = load_env([".env", ".env.local"])

# Validate against a schema
schema = {
    "PORT": {"type": int, "required": True, "min": 1, "max": 65535},
    "DEBUG": {"type": bool, "default": False},
    "ALLOWED_HOSTS": {"type": list[str], "default": []}
}

validated = validate_env(schema)
print(f"Server running on port {validated['PORT']}")
```

### Schema from File

```yaml
# schema.yaml
PORT:
  type: int
  required: true
  min: 1
  max: 65535
  description: "TCP port number"

DEBUG:
  type: bool
  default: false
  description: "Enable debug mode"

ALLOWED_HOSTS:
  type: list[str]
  default: ["localhost", "127.0.0.1"]
  min_len: 1
  description: "List of allowed hostnames"
```

```python
from smart_envloader import load_schema, validate_env

# Load schema from file
schema = load_schema("schema.yaml")

# Validate environment
validated = validate_env(schema)
```

### Secrets Resolution

```bash
# .env
DB_PASSWORD=secret://env/DB_PASS
API_KEY=secret://file/./secrets/api.key
```

```python
from smart_envloader import load_env

# Secrets are automatically resolved
env_vars = load_env(".env")
print(f"DB Password: {env_vars['DB_PASSWORD']}")
```

### Auto-reload

```python
from smart_envloader import watch_env

def on_env_change():
    print("Environment changed, reloading...")
    # Your reload logic here

# Watch for changes
watcher = watch_env(".env", callback=on_env_change)
watcher.start()

# ... later ...
watcher.stop()
```

## CLI Usage

The `envloader` command-line tool provides several subcommands:

### Check Environment

```bash
# Check if required variables are present
envloader check --file .env --require DB_HOST --require DB_PORT

# Check multiple files
envloader check --file .env --file .env.local --require DEBUG
```

### Validate Environment

```bash
# Validate against schema
envloader validate --schema schema.yaml --file .env --format table

# Output in different formats
envloader validate --schema schema.yaml --file .env --format json
envloader validate --schema schema.yaml --file .env --format env
```

### Print Environment

```bash
# Print loaded variables
envloader print --file .env --format table

# Show all environment variables
envloader print --file .env --format json --all
```

### Global Options

```bash
# Verbose output
envloader -v check --file .env

# Quiet mode
envloader -q check --file .env

# Override existing variables
envloader check --file .env --override

# Disable variable expansion
envloader check --file .env --no-expand
```

## Framework Integrations

### FastAPI

```python
from fastapi import FastAPI, Depends
from smart_envloader.integrations.fastapi import Settings, get_settings

class AppSettings(Settings):
    def __init__(self):
        super().__init__(
            files=[".env", ".env.local"],
            schema_path="schema.yaml",
            required=["PORT", "DEBUG"]
        )

app = FastAPI()
get_app_settings = get_settings(AppSettings)

@app.get("/config")
async def get_config(settings: AppSettings = Depends(get_app_settings)):
    return {"port": settings.PORT, "debug": settings.DEBUG}
```

### Django

```python
# settings.py
INSTALLED_APPS = [
    # ... other apps ...
    'smart_envloader.integrations.django.EnvAppConfig',
]

# Optional: Configure environment loading
ENV_FILES = ['.env', '.env.local', '.env.production']
ENV_SCHEMA_PATH = 'schema.yaml'
ENV_REQUIRED_VARS = ['DEBUG', 'SECRET_KEY', 'DATABASE_URL']
ENV_OVERRIDE = False
ENV_EXPAND = True
ENV_CACHE = True
ENV_STRICT = True
```

## Advanced Features

### Custom Secret Providers

```python
from smart_envloader.secrets import register_provider

class AWSSMProvider:
    scheme = "aws-sm"
    
    def resolve(self, uri):
        # Extract secret name from URI
        secret_name = uri.replace("aws-sm://", "")
        # Use boto3 to get secret from AWS Secrets Manager
        # ... implementation ...
        return secret_value

# Register the provider
register_provider(AWSSMProvider())

# Use in .env file
# API_KEY=aws-sm://my-api-key
```

### Custom Validators

```python
schema = {
    "EMAIL": {
        "type": str,
        "validator": lambda x: "@" in x and "." in x,
        "description": "Valid email address"
    },
    "PORT": {
        "type": int,
        "validator": lambda x: 1024 <= x <= 65535,
        "description": "Port in user range"
    }
}
```

### Transform Functions

```python
schema = {
    "HOSTS": {
        "type": list[str],
        "transform": lambda x: [h.strip() for h in x],
        "description": "List of hosts with whitespace removed"
    }
}
```

## Configuration Options

### Environment Loading

- `paths`: Single path or list of paths to environment files
- `required`: List of required environment variable names
- `override`: Whether to override existing `os.environ` values
- `expand`: Whether to expand variable references (e.g., `${VAR}`)
- `cache`: Whether to use file caching for performance

### Validation

- `strict`: Whether to raise errors for missing non-required variables
- `min/max`: Numeric constraints for numbers
- `min_len/max_len`: Length constraints for strings and collections
- `regex`: Regular expression validation for strings
- `choices`: Allowed values for validation
- `validator`: Custom validation function
- `transform`: Custom transformation function

### File Watching

- `interval`: Polling interval in seconds (fallback mode)
- `use_watchdog`: Whether to use watchdog if available
- `callback`: Function to call when file changes

## Error Handling

The package provides clear error messages and custom exceptions:

- `EnvLoaderError`: Base exception for all errors
- `EnvFileNotFound`: Environment file not found
- `InvalidEnvLine`: Invalid line in environment file
- `MissingRequiredVars`: Required variables missing
- `SchemaError`: Schema definition error
- `ValidationError`: Validation failure with detailed error messages
- `SecretResolutionError`: Secret resolution failure

## Performance Features

- **File caching**: Avoid re-parsing unchanged files
- **Efficient parsing**: Precompiled regex patterns and optimized loops
- **Lazy loading**: Only load files when needed
- **Memory efficient**: Deep copy results to prevent mutation surprises

## Examples

See the `examples/` directory for complete working examples:

- `env.example`: Sample environment file
- `schema.example.yaml`: Sample schema file
- `demo_fastapi.py`: FastAPI integration example

## Development

### Running Tests

```bash
# Install development dependencies
pip install -e .[dev]

# Run tests
pytest

# Run with coverage
pytest --cov=smart_envloader --cov-report=html

# Run specific test file
pytest tests/test_core.py
```

### Code Quality

```bash
# Type checking
mypy smart_envloader/

# Linting
ruff check smart_envloader/

# Formatting
black smart_envloader/
isort smart_envloader/
```

### Building

```bash
# Build package
python -m build

# Install build tools
pip install build twine

# Upload to PyPI (after building)
twine upload dist/*
```

## Contributing

We welcome contributions! Please see our [Contributing Guide](CONTRIBUTING.md) for details.

### Development Setup

1. Fork the repository
2. Create a virtual environment: `python -m venv venv`
3. Activate it: `source venv/bin/activate` (Linux/Mac) or `venv\Scripts\activate` (Windows)
4. Install in development mode: `pip install -e .[dev]`
5. Run tests: `pytest`
6. Make your changes and ensure tests pass

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes.

## Support

- **Documentation**: [https://smart-envloader.readthedocs.io/](https://smart-envloader.readthedocs.io/)
- **Issues**: [GitHub Issues](https://github.com/smart-envloader/smart-envloader/issues)
- **Discussions**: [GitHub Discussions](https://github.com/smart-envloader/smart-envloader/discussions)

## Roadmap

- [ ] Kubernetes secrets integration
- [ ] HashiCorp Vault integration
- [ ] Configuration hot-reloading for web frameworks
- [ ] Environment variable encryption
- [ ] Configuration validation schemas (JSON Schema, OpenAPI)
- [ ] Web UI for configuration management
- [ ] Configuration diffing and rollback
- [ ] Multi-environment configuration management
- [ ] Configuration testing framework
- [ ] Performance benchmarking suite

## Acknowledgments

- Inspired by `python-dotenv` and `pydantic-settings`
- Built with modern Python best practices
- Community-driven development and feedback
