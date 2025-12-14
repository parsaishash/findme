# Contributing to FindMe

Thank you for your interest in contributing to FindMe! This document provides guidelines and best practices for contributors.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Development Workflow](#development-workflow)
- [Git Conventions](#git-conventions)
- [Code Style](#code-style)
- [Testing](#testing)
- [Documentation](#documentation)
- [Submitting Changes](#submitting-changes)
- [Review Process](#review-process)

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all contributors. By participating, you agree to:

- Be respectful and inclusive
- Focus on constructive feedback
- Accept responsibility for mistakes
- Show empathy towards other contributors
- Help create a positive community

## Getting Started

1. **Fork the repository** on GitLab
2. **Clone your fork** locally
3. **Set up the development environment** (see below)
4. **Create a feature branch** from `develop`
5. **Make your changes** following the guidelines
6. **Submit a merge request** to the `develop` branch

## Development Setup

### Prerequisites

- Python 3.12+
- Docker & Docker Compose
- Git
- uv (Python package manager)

### Local Development

1. **Clone the repository:**
   ```bash
   git clone https://gitlab.com/yourusername/findme.git
   cd findme
   ```

2. **Set up Python environment:**
   ```bash
   # Install uv if not already installed
   curl -LsSf https://astral.sh/uv/install.sh | sh

   # Install dependencies
   uv pip install -r findme/requirements.txt
   uv pip install -r requirements-dev.txt
   ```

3. **Set up pre-commit hooks:**
   ```bash
   pre-commit install
   pre-commit install --hook-type commit-msg
   ```

4. **Set up environment:**
   ```bash
   cp findme/env.example findme/.env
   # Edit .env with your local configuration
   ```

5. **Run with Docker:**
   ```bash
   make build
   make up
   make migrate
   ```

### Alternative: Pure Python Development

If you prefer not to use Docker for development:

```bash
cd findme
python manage.py migrate
python manage.py runserver
```

## Development Workflow

### Branch Naming Convention

Use the following branch naming pattern:

```
<type>/<description>
```

**Types:**
- `feature/` - New features
- `bugfix/` - Bug fixes
- `hotfix/` - Critical fixes for production
- `refactor/` - Code refactoring
- `docs/` - Documentation updates
- `test/` - Testing improvements
- `ci/` - CI/CD pipeline changes

**Examples:**
- `feature/add-user-authentication`
- `bugfix/fix-file-upload-validation`
- `refactor/simplify-api-endpoints`
- `docs/update-docker-readme`

### Commit Message Convention

Follow [Conventional Commits](https://conventionalcommits.org/) specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat:` - New features
- `fix:` - Bug fixes
- `docs:` - Documentation changes
- `style:` - Code style changes (formatting, etc.)
- `refactor:` - Code refactoring
- `test:` - Adding or updating tests
- `chore:` - Maintenance tasks (dependencies, etc.)
- `perf:` - Performance improvements
- `ci:` - CI/CD pipeline changes
- `revert:` - Revert previous commits

**Examples:**
```bash
feat: add user authentication system
fix: resolve memory leak in file upload
docs: update API documentation
refactor: simplify database query logic
test: add unit tests for user model
chore: update dependencies to latest versions
```

**Breaking Changes:**
For commits that introduce breaking changes, add `BREAKING CHANGE:` in the footer:

```
feat: change API response format

BREAKING CHANGE: The response format has changed from XML to JSON
```

### Pull Request Guidelines

1. **Create a feature branch** from `develop`
2. **Keep PRs focused** - one feature/fix per PR
3. **Write descriptive titles** following commit conventions
4. **Provide detailed descriptions** including:
   - What changes were made
   - Why the changes were needed
   - How to test the changes
   - Screenshots/videos for UI changes
5. **Reference issues** using keywords: `Fixes #123`, `Closes #456`
6. **Ensure CI passes** before requesting review
7. **Request review** from appropriate team members

## Code Style

This project uses several tools to maintain code quality:

### Python Code Style

- **Black** for code formatting (88 character line length)
- **isort** for import sorting (compatible with Black)
- **flake8** for linting
- **mypy** for type checking

### Django-Specific Guidelines

- Follow Django's coding style and conventions
- Use type hints for function parameters and return values
- Write descriptive docstrings for classes and functions
- Keep views thin by moving business logic to services/utilities
- Use Django's ORM effectively - avoid raw SQL unless necessary

### JavaScript/Vue.js Guidelines

- Use ES6+ features
- Follow Vue.js style guide
- Use meaningful variable and function names
- Add comments for complex logic

### HTML/CSS Guidelines

- Use semantic HTML5 elements
- Follow BEM methodology for CSS classes
- Ensure responsive design
- Maintain accessibility standards

## Testing

### Running Tests

```bash
# Run all tests
make test

# Run specific test file
python manage.py test tests.test_specific_module

# Run with coverage
python manage.py test --verbosity=2 --keepdb
```

### Writing Tests

- Write tests for all new features and bug fixes
- Use descriptive test names that explain what is being tested
- Follow the AAA pattern: Arrange, Act, Assert
- Use factories (Factory Boy) for test data creation
- Mock external dependencies
- Test both positive and negative scenarios

### Test Coverage

Maintain minimum 80% code coverage. Coverage reports are generated automatically in CI.

## Documentation

### Code Documentation

- Add docstrings to all public functions, classes, and modules
- Use Google-style docstrings
- Document complex algorithms and business logic
- Keep comments up-to-date with code changes

### User Documentation

- Update `DOCKER_README.md` for deployment changes
- Update API documentation for endpoint changes
- Add migration notes for breaking changes
- Include examples and usage instructions

## Submitting Changes

### Before Submitting

1. **Run pre-commit hooks:**
   ```bash
   pre-commit run --all-files
   ```

2. **Run tests:**
   ```bash
   make test
   ```

3. **Check code quality:**
   ```bash
   make lint
   ```

4. **Update documentation** if needed

5. **Squash commits** if you have many small commits

### Creating a Merge Request

1. **Push your branch** to your fork
2. **Create a merge request** targeting the `develop` branch
3. **Fill out the merge request template**
4. **Assign appropriate reviewers**
5. **Ensure CI pipeline passes**

## Review Process

### For Reviewers

- Review code for functionality, style, and best practices
- Test changes locally when possible
- Provide constructive feedback
- Approve when requirements are met
- Use GitLab's review tools for inline comments

### For Contributors

- Address all review comments
- Make requested changes or explain why changes aren't needed
- Keep discussions focused and productive
- Mark resolved comments as resolved

## Release Process

### Version Numbering

Follow [Semantic Versioning](https://semver.org/spec/v2.0.0):

- **MAJOR.MINOR.PATCH** (e.g., 1.2.3)
- **MAJOR**: Breaking changes
- **MINOR**: New features (backward compatible)
- **PATCH**: Bug fixes (backward compatible)

### Release Branches

- `main` - Production releases
- `develop` - Development integration
- `release/v*` - Release preparation branches

### Release Checklist

- [ ] All tests pass
- [ ] Code review completed
- [ ] Documentation updated
- [ ] Migration scripts tested
- [ ] Performance benchmarks pass
- [ ] Security scan passed
- [ ] Tag created with version number
- [ ] Release notes published

## Getting Help

- **Issues**: Use GitLab issues for bugs and feature requests
- **Discussions**: Use GitLab discussions for questions and ideas
- **Documentation**: Check `DOCKER_README.md` and inline code documentation

## Recognition

Contributors are recognized in:
- Git commit history
- CHANGELOG.md (for significant contributions)
- Release notes

Thank you for contributing to FindMe! 🎉