# Database Configuration

## Overview
The database configuration follows a simple, centralized approach with `app_settings.py` as the single source of truth.

## Configuration Structure

### 1. Source of Truth (`app_settings.py`)
```python
class Settings(BaseSettings):
    # Database Configuration
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/gateway"
    SQL_ECHO: bool = False
    DB_POOL_SIZE: int = 5
    DB_MAX_OVERFLOW: int = 10
    DB_POOL_TIMEOUT: int = 30
```

All database settings are defined here and follow this priority:
1. Environment variables
2. `.env` file values
3. Default values (development only)

### 2. Migration Configuration (`alembic.ini`)
Contains only static Alembic-specific configuration:
- Script locations
- File templates
- Version control settings
- Logging configuration

No database connection settings are stored here as they come from `app_settings.py`.

### 3. Migration Environment (`migrations/env.py`)
Connects Alembic with application settings:
- Uses `app_settings.py` for all database configuration
- Handles both async and sync migration scenarios
- Provides environment-specific behavior (e.g., SQLite for testing)

## Environment-Specific Behavior

### Development
```python
DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/gateway"
SQL_ECHO = False  # SQL logging disabled by default
```

### Testing
```python
# SQLite configuration for tests
render_as_batch = True  # For SQLite compatibility
DATABASE_URL = "sqlite+aiosqlite:///:memory:"
```

### Production
```python
# All values must come from environment variables
# No defaults allowed in production
DATABASE_URL = Required from environment
```

## Migration Management

### Running Migrations
```bash
# Apply all pending migrations
alembic upgrade head

# Generate new migration
alembic revision --autogenerate -m "description"
```

### Migration Files Location
```
src/infrastructure/database/migrations/
├── versions/          # Migration files
├── env.py            # Migration environment
└── script.py.mako    # Migration template
```

## Related Files
- `core/app_settings.py` - Configuration source of truth
- `alembic.ini` - Alembic static configuration
- `migrations/env.py` - Migration environment setup

## Security Notes
- Never commit real credentials
- Production requires explicit environment variables
- Test credentials are rejected in production
- Database URLs should use connection pooling in production
