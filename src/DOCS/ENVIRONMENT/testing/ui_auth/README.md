# UI Authentication Testing

## Overview
This document outlines the testing strategy and implementation for the UI authentication system. The UI authentication system handles user access to the Gateway's user interface.

## Current Test Coverage

### 1. Test Locations
```
/tests/
└── unit/
    └── api/
        └── auth/
            ├── test_login.py      # Login endpoint testing
            └── conftest.py        # Auth test fixtures
```

## Dependencies

### 1. Database
- SQLite in-memory database for unit tests
- Uses SQLAlchemy async engine
- Test database isolation per function
- Automatic cleanup between tests

### 2. Test Configuration
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

## Current Test Coverage

### 1. Login Functionality (`test_login.py`)
- Successful login with valid credentials
- Login with invalid password
- Login with inactive user account
- Login with non-existent user
- Login with missing fields

### 2. Test Fixtures
- `db_engine`: Creates SQLAlchemy engine per test
- `db_connection`: Manages database connection
- `db_session`: Provides isolated database session
- `test_user`: Creates test user with default credentials
- `client`: FastAPI test client
- `app`: FastAPI test application

## Running Tests

### 1. Login Tests
```bash
# Run login tests
PYTHONPATH=src poetry run pytest tests/unit/api/auth/test_login.py -v

# Run with coverage
PYTHONPATH=src poetry run pytest tests/unit/api/auth/test_login.py -v --cov=src --cov-report=term-missing
```

## Test Data

### 1. Default Test User
```python
{
    "email": "test@example.com",
    "password": "testpassword123!",
    "name": "Test User",
    "is_active": True
}
```

## Planned Test Coverage

### 1. JWT Token Tests (TODO)
- Token creation and validation
- Token expiration
- Invalid token handling
- Token refresh

### 2. OAuth2 Tests (TODO)
- Token-based authentication
- Role-based access control
- Session management
- Permission validation

### 3. User Management Tests (TODO)
- User creation
- User updates
- User deletion
- Password management

## Best Practices

### 1. Database Usage
- Always use provided `db_session` fixture
- Don't create new database connections
- Let fixtures handle cleanup

### 2. Async/Sync Operations
- Mark tests with `@pytest.mark.asyncio`
- Use `async/await` with database operations
- Use synchronous calls with test client

### 3. Test Isolation
- Each test function gets fresh database
- Use function-scoped fixtures
- Clean up all test data

## Related Files
- `src/api/routes/auth/user.py`: Login endpoint implementation
- `src/api/security/jwt.py`: JWT token handling
- `src/api/security/oauth2.py`: OAuth2 implementation
- `src/infrastructure/database/repositories/user_repository.py`: User data access 