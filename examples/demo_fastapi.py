#!/usr/bin/env python3
"""
FastAPI demo application demonstrating smart-envloader integration.

This example shows how to use smart-envloader with FastAPI for automatic
environment loading and validation.

To run this demo:
1. Create a .env file with your configuration
2. Install dependencies: pip install fastapi uvicorn
3. Run: python demo_fastapi.py
"""

import os
from typing import Dict, Any

from fastapi import FastAPI, Depends, HTTPException
from fastapi.responses import JSONResponse

# Import smart-envloader integration
from smart_envloader.integrations.fastapi import Settings, get_settings

# Create FastAPI app
app = FastAPI(
    title="Smart EnvLoader Demo",
    description="Demonstrates smart-envloader integration with FastAPI",
    version="1.0.0"
)

# Define settings class with environment loading
class AppSettings(Settings):
    """Application settings with environment validation."""
    
    def __init__(self):
        super().__init__(
            files=[".env", ".env.local"],  # Load multiple env files
            schema_path="schema.yaml",     # Validate against schema
            required=["APP_NAME", "PORT", "DEBUG"],  # Required variables
            override=False,                # Don't override existing env vars
            expand=True,                   # Enable variable expansion
            cache=True,                    # Enable file caching
            strict=True                    # Strict validation
        )

# Create dependency
get_app_settings = get_settings(AppSettings)

@app.get("/")
async def root():
    """Root endpoint."""
    return {
        "message": "Smart EnvLoader FastAPI Demo",
        "docs": "/docs",
        "config": "/config",
        "health": "/health"
    }

@app.get("/config")
async def get_config(settings: AppSettings = Depends(get_app_settings)):
    """Get current configuration."""
    return {
        "app_name": getattr(settings, 'APP_NAME', 'Unknown'),
        "environment": getattr(settings, 'ENVIRONMENT', 'Unknown'),
        "debug": getattr(settings, 'DEBUG', False),
        "port": getattr(settings, 'PORT', 8000),
        "timeout": getattr(settings, 'TIMEOUT', 30.0),
        "allowed_hosts": getattr(settings, 'ALLOWED_HOSTS', []),
        "feature_flags": getattr(settings, 'FEATURE_FLAGS', []),
        "database_config": getattr(settings, 'DATABASE_CONFIG', {}),
        "api_keys": getattr(settings, 'API_KEYS', []),
        "base_url": getattr(settings, 'BASE_URL', ''),
        "log_level": getattr(settings, 'LOG_LEVEL', 'INFO')
    }

@app.get("/health")
async def health_check(settings: AppSettings = Depends(get_app_settings)):
    """Health check endpoint."""
    debug_mode = getattr(settings, 'DEBUG', False)
    
    return {
        "status": "healthy",
        "debug": debug_mode,
        "environment": getattr(settings, 'ENVIRONMENT', 'Unknown'),
        "timestamp": "2024-01-01T00:00:00Z"
    }

@app.post("/validate")
async def validate_config(settings: AppSettings = Depends(get_app_settings)):
    """Validate current configuration."""
    try:
        # This will trigger validation if not already done
        config = get_config(settings)
        return {
            "valid": True,
            "message": "Configuration is valid",
            "config": config
        }
    except Exception as e:
        raise HTTPException(
            status_code=400,
            detail=f"Configuration validation failed: {str(e)}"
        )

@app.get("/env-info")
async def env_info():
    """Get information about loaded environment variables."""
    # Get all environment variables that were loaded by smart-envloader
    # This is a simplified approach - in practice you might want to track
    # which variables were loaded vs which were pre-existing
    
    env_vars = {}
    for key in [
        'APP_NAME', 'ENVIRONMENT', 'DEBUG', 'PORT', 'TIMEOUT',
        'MAX_CONNECTIONS', 'ENABLE_LOGGING', 'MAINTENANCE_MODE',
        'ALLOWED_HOSTS', 'FEATURE_FLAGS', 'DATABASE_CONFIG',
        'API_KEYS', 'BASE_URL', 'LOG_LEVEL'
    ]:
        if key in os.environ:
            env_vars[key] = os.environ[key]
    
    return {
        "loaded_variables": env_vars,
        "total_count": len(env_vars),
        "python_version": os.environ.get('PYTHON_VERSION', 'Unknown')
    }

if __name__ == "__main__":
    import uvicorn
    
    # Load environment variables before starting the server
    try:
        settings = AppSettings()
        port = getattr(settings, 'PORT', 8000)
        debug = getattr(settings, 'DEBUG', False)
        
        print(f"Starting FastAPI demo server...")
        print(f"Port: {port}")
        print(f"Debug: {debug}")
        print(f"Environment: {getattr(settings, 'ENVIRONMENT', 'Unknown')}")
        print(f"App Name: {getattr(settings, 'APP_NAME', 'Unknown')}")
        print(f"API Documentation: http://localhost:{port}/docs")
        
        uvicorn.run(
            "demo_fastapi:app",
            host="0.0.0.0",
            port=port,
            reload=debug,
            log_level="info" if not debug else "debug"
        )
        
    except Exception as e:
        print(f"Failed to start server: {e}")
        print("Make sure you have a valid .env file and schema.yaml")
        exit(1)
