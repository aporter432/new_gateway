# UI Authentication Testing

## Overview
This document outlines the testing strategy and implementation for the UI authentication system. The UI authentication system handles user access to the Gateway's user interface.

## Test Structure

### 1. Test Locations
```
/tests/
└── integration/
    └── api/
        └── auth/
            ├── test_login.py      # Login endpoint testing
            ├── test_jwt.py        # JWT token validation testing
            └── conftest.py        # Auth test fixtures
```

## Setup Requirements

### 1. Database Configuration
- SQLite in-memory database for unit tests
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
# Run JWT tests
PYTHONPATH=src poetry run pytest tests/integration/api/auth/test_jwt.py -v
```

## Related Files
- `src/api/routes/auth/user.py`: Login endpoint implementation
- `src/api/security/jwt.py`: JWT token handling
- `src/api/security/oauth2.py`: OAuth2 implementation
- `src/infrastructure/database/repositories/user_repository.py`: User data access 