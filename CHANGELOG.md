# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Initial project setup and structure
- Core environment loading functionality
- Multi-file support with precedence
- Variable expansion with cycle detection
- File caching for performance
- Comprehensive validation system
- Schema loading from YAML and JSON
- Secret resolution with pluggable providers
- File watching with auto-reload
- CLI tool with multiple subcommands
- FastAPI integration
- Django integration
- Full type hints and documentation

### Changed
- N/A

### Deprecated
- N/A

### Removed
- N/A

### Fixed
- N/A

### Security
- N/A

## [0.2.0] - 2024-01-01

### Added
- Initial release of Smart EnvLoader
- Core environment loading with `load_env()` function
- Advanced validation with `validate_env()` function
- Schema loading from files with `load_schema()` function
- Secret resolution with built-in providers
- File watching with `watch_env()` function
- CLI tool with check, validate, and print commands
- FastAPI integration with Settings class
- Django integration with AppConfig
- Comprehensive test suite
- Full documentation and examples

### Features
- Multi-file environment loading with precedence
- Variable expansion and cycle detection
- Type validation for all Python types
- Constraint validation (min/max, regex, choices, etc.)
- Custom validators and transformers
- Pluggable secret providers
- File change detection with callbacks
- Performance optimizations and caching
- Rich error messages and custom exceptions
- Framework integrations
- Command-line interface

## [0.1.0] - 2023-12-01

### Added
- Project initialization
- Basic project structure
- Development setup and tooling
- CI/CD configuration
- Documentation framework
