# UI Authentication Testing

## Overview
This document outlines the testing strategy and implementation for the UI authentication system. The UI authentication system handles user access to the Gateway's user interface.

## Test Structure

### 1. Test Locations
```
/tests/
├── conftest.py               # Root level fixtures (DB engine, session management)
├── unit/
│   └── api/
│       └── auth/
│           ├── test_login.py # Unit tests for login endpoint
│           └── __init__.py
└── integration/
    └── api/
        └── auth/
            ├── test_jwt.py           # JWT token validation testing
            ├── test_oauth2.py        # OAuth2 authentication testing
            ├── test_password_utils.py # Password utility testing
            ├── test_token_errors.py  # Token error handling tests
            ├── test_token_setup.py   # Token setup testing
            └── __init__.py
```

### 2. Test Types and Fixtures

#### Root Level (`/tests/conftest.py`)
Provides common fixtures for all tests:
- Database engine and session management
- Database connection handling
- Session cleanup
- Mock Redis client
- Test environment settings

#### Unit Tests
Located in `/tests/unit/api/auth/`
- Purpose: Test individual components in isolation
- Uses root fixtures for database handling
- Focus on single function/method behavior
- Fast execution, no external dependencies

Examples:
- `test_login.py`: Tests login endpoint functionality
  - Input validation
  - Error handling
  - Response formatting

#### Integration Tests
Located in `/tests/integration/api/auth/`
- Purpose: Test component interactions and full workflows
- Uses root fixtures for database and connections
- Tests complete authentication flows

Test Files:
- `test_jwt.py`: JWT token lifecycle and validation
- `test_oauth2.py`: OAuth2 authentication flows
- `test_password_utils.py`: Password hashing and verification
- `test_token_errors.py`: Token error handling
- `test_token_setup.py`: Token creation and setup

## Setup Requirements

### 1. Database Configuration
- SQLite in-memory database for tests
- Uses SQLAlchemy async engine
- Test database isolation per function
- Automatic cleanup between tests

### 2. Environment Configuration
```python
# Environment variables (set automatically in conftest.py)
TESTING=true

# Database URL (configured in session.py)
database_url = "sqlite+aiosqlite:///:memory:"
```

### 3. Required Dependencies
```toml
[tool.poetry.group.test.dependencies]
aiosqlite = "^0.21.0"
email-validator = "^2.2.0"
psycopg2-binary = "^2.9.10"
asyncpg = "^0.30.0"
bcrypt = ">=4.0.0"
passlib = {version = ">=1.7.4", extras = ["bcrypt"]}

[tool.poetry.dependencies]
fastapi = ">=0.100.0"
sqlalchemy = ">=2.0.0"
python-jose = {extras = ["cryptography"], version = ">=3.3.0"}
passlib = {extras = ["bcrypt"], version = ">=1.7.4"}
python-multipart = ">=0.0.6"
```

### 4. Running Tests
```bash
# Run all tests
PYTHONPATH=src poetry run pytest

# Run only unit tests
PYTHONPATH=src poetry run pytest tests/unit/

# Run only integration tests
PYTHONPATH=src poetry run pytest tests/integration/

# Run specific test file
PYTHONPATH=src poetry run pytest tests/integration/api/auth/test_jwt.py -v

# Run with coverage
PYTHONPATH=src poetry run pytest --cov=src --cov-report=term-missing
```

## Related Files
- `src/api/routes/auth/user.py`: Login endpoint implementation
- `src/api/security/jwt.py`: JWT token handling
- `src/api/security/oauth2.py`: OAuth2 implementation
- `src/infrastructure/database/repositories/user_repository.py`: User data access

## Test Markers
The following pytest markers are available for test selection:
```python
@pytest.mark.unit        # Mark as unit test
@pytest.mark.integration # Mark as integration test
@pytest.mark.slow       # Mark as slow test
```

Example usage:
```bash
# Run only unit tests
poetry run pytest -m unit

# Run all except slow tests
poetry run pytest -m "not slow"
``` 