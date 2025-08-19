# envsmith

[![PyPI version](https://badge.fury.io/py/envsmith.svg)](https://badge.fury.io/py/envsmith)
[![CI](https://github.com/PeymanSohi/envsmith/actions/workflows/publish.yml/badge.svg)](https://github.com/PeymanSohi/envsmith/actions/workflows/publish.yml)

A modern, production-ready solution for loading, validating, and managing environment variables in Python using a schema-first approach.

## 🚀 How It Works

`envsmith` is a Python package that provides a robust way to manage environment variables with the following workflow:

1. **Schema Definition**: You define a YAML or JSON schema that specifies:
   - Which environment variables are required
   - What data types they should have
   - Default values for optional variables
   - Validation rules

2. **Environment Loading**: The package loads variables from multiple sources:
   - `.env` files
   - System environment variables
   - Custom dictionaries
   - Priority: System > .env file > defaults

3. **Validation & Type Casting**: Each variable is validated against the schema:
   - Required variables are checked for presence
   - Values are cast to the specified types (str, int, float, bool)
   - Helpful error messages for missing/invalid variables

4. **Integration**: Seamlessly integrates with FastAPI and Django applications

## 🔧 Technical Architecture

### **Core Processing Pipeline**
```python
class EnvSmith(dict):
    def __init__(self, schema_path, env_file=".env", env=None):
        # Step 1: Load .env file into environment
        load_dotenv(env_file)
        
        # Step 2: Parse schema file (YAML/JSON)
        self.schema = load_schema(schema_path)
        
        # Step 3: Get environment (system + .env merged)
        self.env = env or dict(os.environ)
        
        # Step 4: Validate and cast types
        validated = validate_env(self.env, self.schema)
        
        # Step 5: Update the dictionary
        self.update(validated)
```

### **Data Flow & Priority System**
1. **Schema Loading**: YAML/JSON → Python dict with validation rules
2. **Environment Merging**: System env + .env files + custom dicts
3. **Priority Chain**: System > .env > Schema defaults
4. **Type Casting**: Automatic conversion (str, int, float, bool)
5. **Validation**: Required checks + type validation + error collection

### **Key Components**
- **`core.py`**: Main engine that orchestrates the entire process
- **`schema_loader.py`**: Parses YAML/JSON schema files
- **`validation.py`**: Type casting and validation logic
- **`integrations/`**: Framework-specific adapters (FastAPI, Django)
- **`cli.py`**: Command-line interface for common operations

## 📊 Comparison with Other Tools

| Feature | envsmith | python-dotenv | pydantic-settings | dynaconf | python-decouple |
|---------|----------|---------------|-------------------|----------|-----------------|
| **Schema Validation** | ✅ YAML/JSON | ❌ None | ✅ Pydantic models | ✅ TOML/YAML | ❌ None |
| **Type Casting** | ✅ Automatic | ❌ Strings only | ✅ Pydantic types | ✅ Basic | ❌ Strings only |
| **Framework Integration** | ✅ FastAPI/Django | ❌ None | ✅ Pydantic ecosystem | ✅ Multiple | ❌ None |
| **CLI Tools** | ✅ Built-in | ❌ None | ❌ None | ✅ Rich CLI | ❌ None |
| **Priority System** | ✅ System > .env > defaults | ❌ .env only | ✅ Environment > .env | ✅ Multiple sources | ✅ .env > env |
| **Error Handling** | ✅ Comprehensive | ❌ Basic | ✅ Pydantic errors | ✅ Good | ❌ Basic |
| **Production Ready** | ✅ Logging, testing | ⚠️ Basic | ✅ Enterprise | ✅ Enterprise | ⚠️ Basic |

### **Why Choose envsmith?**

#### **vs python-dotenv**
- **python-dotenv**: Only loads `.env` files, no validation, no type casting
- **envsmith**: Full validation, type safety, multiple sources, framework integration

#### **vs pydantic-settings**
- **pydantic-settings**: Requires Pydantic knowledge, more complex setup
- **envsmith**: Simple YAML/JSON schemas, easier to understand and maintain

#### **vs dynaconf**
- **dynaconf**: More complex, multiple config formats, overkill for simple apps
- **envsmith**: Focused on environment variables, simple and lightweight

#### **vs python-decouple**
- **python-decouple**: Basic .env loading, no validation, no type safety
- **envsmith**: Full validation suite, type casting, production features

### **Performance Characteristics**
- **Startup Time**: Fast - single pass validation
- **Memory Usage**: Minimal - only stores validated variables
- **Runtime Overhead**: Zero - all processing happens at initialization
- **Error Reporting**: Comprehensive - all issues reported at once

### **Use Cases Where envsmith Excels**
✅ **Web Applications**: FastAPI, Django, Flask
✅ **Microservices**: Environment-based configuration
✅ **Docker Containers**: Environment variable validation
✅ **CI/CD Pipelines**: Configuration validation
✅ **Team Development**: Clear schema documentation
✅ **Production Deployments**: Early error detection

## ✨ Features

- **Schema-First**: Define your environment structure in YAML/JSON
- **Multiple Sources**: Load from `.env`, system, or custom dicts
- **Type Safety**: Automatic type casting and validation
- **Framework Integration**: FastAPI and Django support
- **CLI Tools**: Command-line interface for common tasks
- **Secrets Management**: Mock interface for external secret providers
- **Production Ready**: Logging, error handling, and comprehensive testing

## 📦 Installation

```bash
pip install envsmith
```

With optional extras:
```bash
pip install envsmith[fastapi,django]
```

## 🎯 Quick Start

### 1. Create a Schema

Create a `schema.yaml` file:

```yaml
DATABASE_URL:
  type: str
  required: true
  description: "Database connection string"

SECRET_KEY:
  type: str
  required: true
  description: "Application secret key"

DEBUG:
  type: bool
  default: false
  description: "Debug mode"

PORT:
  type: int
  default: 8000
  description: "Server port"

API_TIMEOUT:
  type: float
  default: 30.0
  description: "API timeout in seconds"
```

### 2. Create Environment File

Create a `.env` file:

```bash
DATABASE_URL=postgresql://user:pass@localhost:5432/mydb
SECRET_KEY=your-super-secret-key-here
DEBUG=true
PORT=8080
API_TIMEOUT=45.0
```

### 3. Use in Python

```python
from envsmith import EnvSmith

# Load with schema validation
settings = EnvSmith(schema_path="schema.yaml", env_file=".env")

# Access validated variables
print(settings["DATABASE_URL"])  # postgresql://user:pass@localhost:5432/mydb
print(settings["DEBUG"])         # True (bool)
print(settings["PORT"])          # 8080 (int)
print(settings["API_TIMEOUT"])   # 45.0 (float)

# Get with default fallback
print(settings.get("NONEXISTENT", "default_value"))
```

## 🛠️ CLI Usage

### Initialize Project

Create `.env` and `schema.yaml` files:

```bash
python3 -m envsmith init
```

### Validate Environment

Check if your `.env` file matches the schema:

```bash
python3 -m envsmith validate
```

### Export Environment

Export validated variables in different formats:

```bash
# Export as JSON
python3 -m envsmith export --format json

# Export as YAML
python3 -m envsmith export --format yaml
```

## 🔌 Framework Integrations

### FastAPI Integration

```python
from fastapi import FastAPI, Depends
from envsmith.integrations.fastapi import get_settings

app = FastAPI()

@app.get("/config")
def get_config(settings = Depends(get_settings)):
    return {
        "database_url": settings["DATABASE_URL"],
        "debug": settings["DEBUG"],
        "port": settings["PORT"]
    }

@app.get("/health")
def health_check(settings = Depends(get_settings)):
    return {
        "status": "healthy",
        "environment": settings.get("ENV", "development")
    }
```

### Django Integration

In your `settings.py`:

```python
from envsmith.integrations.django import load_envsmith

# Load environment variables with schema validation
load_envsmith(schema_path="schema.yaml")

# Now you can use them directly
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': DATABASE_NAME,
        'USER': DATABASE_USER,
        'PASSWORD': DATABASE_PASSWORD,
        'HOST': DATABASE_HOST,
        'PORT': DATABASE_PORT,
    }
}

SECRET_KEY = SECRET_KEY
DEBUG = DEBUG
ALLOWED_HOSTS = ALLOWED_HOSTS.split(',') if ALLOWED_HOSTS else []
```

## 🔐 Secrets Management

For production environments, you can integrate with external secret providers:

```python
from envsmith.secrets import SecretProvider

# Mock interface (replace with actual AWS, Vault, etc.)
secrets = SecretProvider()

# Get secret from external provider
api_key = secrets.get_secret("API_KEY")

# Fallback to local secret
fallback_key = secrets.get_local_secret("API_KEY")
```

## 📋 Schema Reference

### Supported Types

- **str**: String values
- **int**: Integer values
- **float**: Floating-point values
- **bool**: Boolean values (accepts: true/false, yes/no, 1/0, on/off)

### Schema Structure

```yaml
VARIABLE_NAME:
  type: str|int|float|bool
  required: true|false
  default: "default_value"
  description: "Human-readable description"
```

### Example Schema

```yaml
# Database Configuration
DATABASE_URL:
  type: str
  required: true
  description: "PostgreSQL connection string"

DATABASE_POOL_SIZE:
  type: int
  default: 10
  description: "Database connection pool size"

# Application Settings
DEBUG:
  type: bool
  default: false
  description: "Enable debug mode"

LOG_LEVEL:
  type: str
  default: "INFO"
  description: "Logging level"

# API Configuration
API_TIMEOUT:
  type: float
  default: 30.0
  description: "API request timeout in seconds"

MAX_REQUESTS:
  type: int
  default: 1000
  description: "Maximum concurrent requests"
```

## 🧪 Testing

Run the test suite:

```bash
# Install test dependencies
pip install pytest pytest-cov

# Run tests with coverage
python3 -m pytest --cov=envsmith

# Run specific test file
python3 -m pytest tests/test_core.py
```

## 🚀 Development

### Project Structure

```
envsmith/
├── envsmith/           # Main package
│   ├── __init__.py    # Package initialization
│   ├── core.py        # Core loader and validation
│   ├── cli.py         # Command-line interface
│   ├── validation.py  # Schema validation logic
│   ├── schema_loader.py # YAML/JSON schema loading
│   ├── secrets.py     # Secrets management
│   ├── _types.py      # Type definitions
│   └── integrations/  # Framework integrations
│       ├── fastapi.py # FastAPI integration
│       └── django.py  # Django integration
├── tests/             # Test suite
├── examples/          # Usage examples
└── docs/             # Documentation
```

### Adding New Features

1. **Type Support**: Add new types in `validation.py`
2. **Framework Integration**: Create new integration modules
3. **CLI Commands**: Extend `cli.py` with new subcommands
4. **Secrets Providers**: Implement actual secret provider interfaces

## 📝 Examples

Check the `examples/` directory for complete working examples:

- `demo_fastapi.py` - FastAPI application with envsmith
- `demo_django.py` - Django settings with envsmith
- `env.example` - Example environment file

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests for new functionality
5. Ensure all tests pass
6. Submit a pull request

### Development Setup

```bash
# Clone the repository
git clone https://github.com/PeymanSohi/envsmith.git
cd envsmith

# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install in development mode
pip install -e ".[fastapi,django]"

# Install test dependencies
pip install pytest pytest-cov

# Run tests
python3 -m pytest
```

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **Issues**: [GitHub Issues](https://github.com/PeymanSohi/envsmith/issues)
- **Documentation**: [README](https://github.com/PeymanSohi/envsmith#readme)
- **Examples**: Check the `examples/` directory

## 🔄 Changelog

See [CHANGELOG.md](CHANGELOG.md) for a detailed history of changes and releases.
