# envsmith

[![PyPI version](https://badge.fury.io/py/envsmith.svg)](https://badge.fury.io/py/envsmith)
[![CI](https://github.com/PeymanSohi/envsmith/actions/workflows/publish.yml/badge.svg)](https://github.com/PeymanSohi/envsmith/actions/workflows/publish.yml)

A modern, production-ready solution for loading, validating, and managing environment variables in Python using a schema-first approach.

## Features
- Load from `.env`, system, or dict
- YAML/JSON schema validation
- Secrets management (mock interface for AWS, Vault, etc.)
- FastAPI & Django integrations
- CLI for init, validate, export
- Type hints, logging, doctests

## Installation
```bash
pip install envsmith
```

## Quick Start
```python
from envsmith import EnvSmith
settings = EnvSmith(schema_path="schema.yaml")
print(settings["DATABASE_URL"])
```

## CLI Usage
```bash
envsmith init      # Create .env and schema.yaml
envsmith validate  # Validate .env against schema
envsmith export    # Export env as JSON/YAML
```

## FastAPI Example
```python
from fastapi import FastAPI, Depends
from envsmith.integrations.fastapi import get_settings

app = FastAPI()

@app.get("/info")
def info(settings = Depends(get_settings)):
    return {"env": settings["ENV"]}
```

## Django Example
```python
# settings.py
from envsmith.integrations.django import load_envsmith
load_envsmith(schema_path="schema.yaml")
```

## Contribution
- Fork & PRs welcome
- Run tests: `pytest --cov=envsmith`
- Follow PEP8 & add type hints

## License
MIT
