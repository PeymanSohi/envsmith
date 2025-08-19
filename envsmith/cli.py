"""Command-line interface for smart-envloader."""

import argparse
import json
import logging
import sys
from pathlib import Path
from typing import List, Optional

from .core import load_env
from .validation import validate_env
from .schema_loader import load_schema
from ._types import (
    EnvLoaderError, EnvFileNotFound, MissingRequiredVars, 
    ValidationError, SchemaError, SecretResolutionError
)

logger = logging.getLogger(__name__)

def setup_logging(verbose: bool = False, quiet: bool = False):
    """Setup logging configuration."""
    if quiet:
        level = logging.ERROR
    elif verbose:
        level = logging.DEBUG
    else:
        level = logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def print_table(data: dict, title: str = "Environment Variables"):
    """Print data in a table format."""
    try:
        import rich
        from rich.console import Console
        from rich.table import Table
        
        console = Console()
        table = Table(title=title)
        table.add_column("Key", style="cyan", no_wrap=True)
        table.add_column("Value", style="green")
        
        for key, value in data.items():
            table.add_row(key, str(value))
        
        console.print(table)
        return
    except ImportError:
        # Fall back to plain text if rich is not available
        pass
    
    # Plain text table
    print(f"\n{title}")
    print("=" * (len(title) + 2))
    print(f"{'Key':<30} {'Value'}")
    print("-" * 50)
    
    for key, value in data.items():
        # Truncate long values for display
        display_value = str(value)
        if len(display_value) > 50:
            display_value = display_value[:47] + "..."
        print(f"{key:<30} {display_value}")

def print_json(data: dict):
    """Print data in JSON format."""
    print(json.dumps(data, indent=2, default=str))

def print_env(data: dict):
    """Print data in environment file format."""
    for key, value in data.items():
        # Escape quotes and newlines in values
        if isinstance(value, str):
            if '"' in value or '\n' in value:
                value = f"'{value}'"
            else:
                value = f'"{value}"'
        print(f"{key}={value}")

def cmd_check(args):
    """Handle the check subcommand."""
    try:
        # Use default file if none specified
        files = args.file if args.file else [".env"]
        
        # Load environment files
        env_data = load_env(
            paths=files,
            required=args.require,
            override=args.override,
            expand=args.expand
        )
        
        print(f"✓ Environment check passed")
        print(f"  Loaded {len(env_data)} variables from {len(args.file)} file(s)")
        
        if args.require:
            print(f"  All required variables present: {', '.join(args.require)}")
        
        return 0
        
    except MissingRequiredVars as e:
        print(f"✗ Missing required variables: {', '.join(e.missing_vars)}")
        return 3
    except EnvFileNotFound as e:
        print(f"✗ Environment file not found: {e}")
        return 5
    except Exception as e:
        print(f"✗ Error during environment check: {e}")
        return 1

def cmd_validate(args):
    """Handle the validate subcommand."""
    try:
        # Load schema
        schema = load_schema(args.schema)
        
        # Use default file if none specified
        files = args.file if args.file else [".env"]
        
        # Load environment files
        env_data = load_env(
            paths=files,
            override=args.override,
            expand=args.expand
        )
        
        # Validate environment
        validated_data = validate_env(schema, strict=args.strict)
        
        print(f"✓ Environment validation passed")
        print(f"  Validated {len(validated_data)} variables against schema")
        
        # Print results
        if args.format == "table":
            print_table(validated_data, "Validated Environment Variables")
        elif args.format == "json":
            print_json(validated_data)
        else:  # env format
            print_env(validated_data)
        
        return 0
        
    except ValidationError as e:
        print(f"✗ Validation failed:")
        for key, error in e.errors.items():
            print(f"  {key}: {error}")
        return 2
    except SchemaError as e:
        print(f"✗ Schema error: {e}")
        return 4
    except EnvFileNotFound as e:
        print(f"✗ Environment file not found: {e}")
        return 5
    except Exception as e:
        print(f"✗ Error during validation: {e}")
        return 1

def cmd_print(args):
    """Handle the print subcommand."""
    try:
        # Use default file if none specified
        files = args.file if args.file else [".env"]
        
        # Load environment files
        env_data = load_env(
            paths=files,
            override=args.override,
            expand=args.expand
        )
        
        # Filter to only loaded variables if not --all
        if not args.all:
            # Get current os.environ to see what was there before
            import os
            original_env = set(os.environ.keys())
            
            # Only show variables that were loaded (not pre-existing)
            loaded_keys = set(env_data.keys()) - original_env
            env_data = {k: v for k, v in env_data.items() if k in loaded_keys}
        
        # Print results
        if args.format == "table":
            print_table(env_data, "Environment Variables")
        elif args.format == "json":
            print_json(env_data)
        else:  # env format
            print_env(env_data)
        
        return 0
        
    except EnvFileNotFound as e:
        print(f"✗ Environment file not found: {e}")
        return 5
    except Exception as e:
        print(f"✗ Error during print: {e}")
        return 1

def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        prog="envloader",
        description="Smart environment variable loader with validation and schema support",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  envloader check --file .env --require DB_HOST --require DB_PORT
  envloader validate --schema schema.yaml --file .env --format table
  envloader print --file .env --format json
        """
    )
    
    # Global options
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose logging"
    )
    parser.add_argument(
        "-q", "--quiet",
        action="store_true",
        help="Suppress all output except errors"
    )
    
    # Subcommands
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Check command
    check_parser = subparsers.add_parser(
        "check",
        help="Check environment files and required variables"
    )
    check_parser.add_argument(
        "--file", "-f",
        action="append",
        help="Environment file(s) to load (can be specified multiple times, defaults to .env if none specified)"
    )
    check_parser.add_argument(
        "--require", "-r",
        action="append",
        help="Required environment variable (can be specified multiple times)"
    )
    check_parser.add_argument(
        "--override",
        action="store_true",
        help="Override existing environment variables"
    )
    check_parser.add_argument(
        "--expand",
        action="store_true",
        default=True,
        help="Enable variable expansion (default: enabled)"
    )
    check_parser.add_argument(
        "--no-expand",
        dest="expand",
        action="store_false",
        help="Disable variable expansion"
    )
    
    # Validate command
    validate_parser = subparsers.add_parser(
        "validate",
        help="Validate environment against a schema"
    )
    validate_parser.add_argument(
        "--schema", "-s",
        required=True,
        help="Schema file (YAML or JSON)"
    )
    validate_parser.add_argument(
        "--file", "-f",
        action="append",
        help="Environment file(s) to load (can be specified multiple times, defaults to .env if none specified)"
    )
    validate_parser.add_argument(
        "--format",
        choices=["table", "json", "env"],
        default="table",
        help="Output format (default: table)"
    )
    validate_parser.add_argument(
        "--override",
        action="store_true",
        help="Override existing environment variables"
    )
    validate_parser.add_argument(
        "--expand",
        action="store_true",
        default=True,
        help="Enable variable expansion (default: enabled)"
    )
    validate_parser.add_argument(
        "--no-expand",
        dest="expand",
        action="store_false",
        help="Disable variable expansion"
    )
    validate_parser.add_argument(
        "--strict",
        action="store_true",
        default=True,
        help="Enable strict validation (default: enabled)"
    )
    validate_parser.add_argument(
        "--no-strict",
        dest="strict",
        action="store_false",
        help="Disable strict validation"
    )
    
    # Print command
    print_parser = subparsers.add_parser(
        "print",
        help="Print loaded environment variables"
    )
    print_parser.add_argument(
        "--file", "-f",
        action="append",
        help="Environment file(s) to load (can be specified multiple times, defaults to .env if none specified)"
    )
    print_parser.add_argument(
        "--format",
        choices=["table", "json", "env"],
        default="table",
        help="Output format (default: table)"
    )
    print_parser.add_argument(
        "--override",
        action="store_true",
        help="Override existing environment variables"
    )
    print_parser.add_argument(
        "--expand",
        action="store_true",
        default=True,
        help="Enable variable expansion (default: enabled)"
    )
    print_parser.add_argument(
        "--no-expand",
        dest="expand",
        action="store_false",
        help="Disable variable expansion"
    )
    print_parser.add_argument(
        "--all",
        action="store_true",
        help="Show all environment variables, not just loaded ones"
    )
    
    # Parse arguments
    args = parser.parse_args()
    
    # Setup logging
    setup_logging(args.verbose, args.quiet)
    
    # Handle no command case
    if not args.command:
        parser.print_help()
        return 1
    
    # Execute command
    try:
        if args.command == "check":
            return cmd_check(args)
        elif args.command == "validate":
            return cmd_validate(args)
        elif args.command == "print":
            return cmd_print(args)
        else:
            print(f"Unknown command: {args.command}")
            return 1
    except KeyboardInterrupt:
        print("\nOperation cancelled by user")
        return 130
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        print(f"✗ Unexpected error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
