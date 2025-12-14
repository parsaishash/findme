# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- Comprehensive Docker setup with multi-stage builds
- Standalone Traefik reverse proxy configuration with auto-SSL
- Django root endpoint configuration for multi-project deployments
- Pre-commit hooks for code quality and consistency
- GitLab CI/CD pipeline with automated testing and deployment
- Development tools: Black, isort, flake8, mypy, safety
- Makefile with convenient Docker and development commands
- Detailed documentation and contributing guidelines

### Changed
- Reorganized Docker files to project root
- Updated dependencies with django-celery-beat
- Enhanced environment configuration for multiple deployment scenarios

### Technical Details
- Multi-stage Dockerfile with Python 3.12 and uv package manager
- Traefik integration with path-based routing and self-signed certificates
- Configurable Django URL prefixes via DJANGO_ROOT_ENDPOINT
- Comprehensive pre-commit hooks for Python, Docker, and security
- GitLab CI/CD with test, build, and deployment stages
- Branch protection and merge request guidelines

## [0.1.0] - 2025-01-01

### Added
- Initial Django application setup
- Basic file sharing functionality
- User authentication system
- Celery background task processing
- HTMX-based frontend
- SQLite database configuration
- Basic API endpoints

### Infrastructure
- Docker and Docker Compose configuration
- Redis for caching and Celery broker
- Basic project structure with apps: core, browser, users
- Environment-based configuration
- Development and production settings