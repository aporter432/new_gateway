# UI Authentication Testing

## Overview
This document outlines the testing strategy and implementation for the UI authentication system. The UI authentication system is separate from OGWS authentication and handles user access to the Gateway's user interface.

## Test Structure

### 1. Test Locations
```
/tests/
├── integration/
│   └── api/
│       └── auth/
│           ├── test_password_utils.py  # Password hashing and validation
│           ├── test_jwt.py            # JWT token management
│           └── test_oauth2.py         # OAuth2 flow and dependencies
├── e2e/
│   └── api/
│       └── auth/
│           └── test_auth_flow.py      # End-to-end authentication flows
└── unit/
    └── api/
        └── auth/
            └── test_validation.py      # Input validation and error handling
```

## Dependencies

### 1. Database
- SQLite in-memory database for unit tests (using aiosqlite)
- PostgreSQL for integration and end-to-end tests
- Test database isolation (separate from development)
- Alembic migrations must be run before integration tests
- Automatic cleanup between test runs

### 2. Test Configuration
```python
# Required test environment variables
# For integration tests:
TEST_DATABASE_URL="postgresql+asyncpg://test:test@localhost:5432/test_db"
# For unit tests:
TEST_DATABASE_URL="sqlite+aiosqlite:///:memory:"
JWT_SECRET_KEY="test_secret_key"
ACCESS_TOKEN_EXPIRE_MINUTES=30
```

### 3. Python Dependencies
```toml
# Additional test dependencies in pyproject.toml
[tool.poetry.group.test.dependencies]
pytest = "^7.4.0"
pytest-asyncio = "^0.21.1"
pytest-cov = "^4.1.0"
httpx = "^0.24.1"  # For async HTTP testing
aiosqlite = "^0.21.0"  # For async SQLite testing
email-validator = "^2.2.0"  # For Pydantic email validation
asyncpg = "^0.29.0"  # For async PostgreSQL database support
```

## Test Categories

### 1. Password Utilities
- Password hashing and verification
- Password validation rules
- Error handling for invalid inputs
- Security requirements compliance

### 2. JWT Token Management
- Token creation and signing
- Token validation and verification
- Expiration handling
- Error cases and security measures

### 3. OAuth2 Implementation
- User authentication flow
- Token-based authorization
- Role-based access control
- Session management

### 4. End-to-End Flows
- User registration
- Login/logout
- Password reset
- Account management

## Test Data Management

### 1. Fixtures
- Test user creation
- Admin user setup
- Invalid user cases
- Token generation

### 2. Database State
- Isolated test database
- Pre-test data setup
- Post-test cleanup
- Transaction rollback

## Logging and Monitoring

### 1. Test Logs
```
/logs/test/auth/
├── test_auth.log        # Authentication-specific logs
├── test_security.log    # Security-related events
└── test_errors.log      # Error cases and failures
```

### 2. Metrics Collection
- Authentication attempts
- Success/failure rates
- Token usage statistics
- Performance metrics

## Best Practices

### 1. Security Testing
- Password strength validation
- Token security measures
- Rate limiting tests
- Security header verification

### 2. Error Handling
- Invalid credentials
- Expired tokens
- Malformed requests
- Edge cases

### 3. Performance
- Response time monitoring
- Resource usage tracking
- Concurrent request handling
- Rate limit compliance

## Running Tests

### 1. Individual Components
```bash
# Run specific test categories
pytest tests/integration/api/auth/test_password_utils.py
pytest tests/integration/api/auth/test_jwt.py
pytest tests/integration/api/auth/test_oauth2.py
```

### 2. Full Test Suite
```bash
# Run all auth tests with coverage
pytest tests/integration/api/auth/ --cov=api.security

# Run with detailed logging
pytest tests/integration/api/auth/ --log-cli-level=DEBUG

# Run specific auth test with coverage and missing lines report
PYTHONPATH=src poetry run pytest tests/unit/api/auth/test_login.py -v --cov=src --cov-report=term-missing
```

## Related Documentation
- [Main Testing Guide](../README.md)
- [Database Migrations](../../development/README.md#database-migrations)
- [Security Configuration](../../security/README.md)
- [API Documentation](../../api/README.md) 