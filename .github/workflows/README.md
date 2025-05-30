# GitHub Workflows for PAMP Submissions Service

This directory contains GitHub Actions workflows for automating various tasks in the PAMP Submissions Service codebase.

## Available Workflows

### 1. Tests (`test.yml`)

Runs the automated test suite on push to the `main` branch and on pull requests.

- Sets up PostgreSQL service for testing
- Installs Python dependencies
- Creates a test environment configuration
- Executes the test suite with pytest

### 2. Format & Lint Check (`format.yml`)

Verifies code quality standards on push to the `main` branch and on pull requests.

- Checks code formatting with Black
- Verifies import sorting with isort
- Checks code quality with Flake8
- Posts comments on pull requests when issues are found
- Provides detailed instructions for fixing issues

### 3. Build Docker Image (`build.yml`)

Builds and publishes a Docker image to GitHub Container Registry (GHCR).

- Triggered on push to the `main` branch and on tags matching `v*.*.*`
- Uses Docker BuildX for efficient builds
- Publishes the image with appropriate tags
- Caches build layers for faster builds

### 4. Create Release (`release.yml`)

Creates a GitHub Release when a new tag is pushed.

- Triggered on tags matching `v*.*.*`
- Generates a changelog from git commits
- Creates a GitHub Release with the changelog
- Includes instructions for pulling the Docker image

## Python Tools Used

### Black
Code formatter that ensures consistent Python code style.
- **Usage**: `black app/`
- **Check only**: `black --check app/`

### isort
Import sorter for Python imports.
- **Usage**: `isort app/`
- **Check only**: `isort --check-only app/`

### Flake8
Python linting tool that checks for style and programming errors.
- **Usage**: `flake8 app/ --max-line-length=120 --extend-ignore=E203,W503`

### pytest
Python testing framework for running unit and integration tests.
- **Usage**: `pytest -v`
- **With coverage**: `pytest --cov=app`

## Local Development

To run the same checks locally before pushing:

```bash
# Format code
black app/

# Sort imports
isort app/

# Check linting
flake8 app/ --max-line-length=120 --extend-ignore=E203,W503

# Run tests
pytest -v
```

## Database Requirements

The test workflow requires a PostgreSQL database. When running locally, ensure you have PostgreSQL running or use the provided docker-compose.yml:

```bash
docker-compose up -d db
``` 