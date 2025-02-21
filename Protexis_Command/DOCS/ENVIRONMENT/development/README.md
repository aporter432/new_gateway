# Development Environment

## Setup
1. **Prerequisites**
   - Python 3.11.6+
   - Docker and Docker Compose
   - Poetry 1.7.1+

2. **Environment Configuration**
   - Copy `.env.example` to `.env` in project root
   - Configure local development settings
   - Never commit `.env` to version control

## Configuration Files
### `.env` Configuration
Located at: `/Users/aaronporter/Desktop/Projects/new_gateway/.env`
Contains development defaults for:
- Application settings (APP_NAME, DEBUG, etc.)
- Server configuration (HOST, PORT, WORKERS)
- Database and Redis connection details
- AWS credentials and endpoints
- Gateway-specific settings (ISAT, OGx)
- Security and monitoring parameters

### Docker Configuration
`docker-compose.yml` provides:
- Service definitions
- Health checks
- Network configuration
- Volume management

### Proxy Configuration
`nginx.conf` handles:
- API routing
- Health check endpoints
- Request buffering
- SSL configuration

## Local Services
The development environment uses containerized services:
- Redis for caching and message state
- PostgreSQL for customer data
- LocalStack for AWS service emulation
- Nginx for OGx proxy

## Database Migrations
Located at: `src/infrastructure/database/migrations`

### Migration Files
- `alembic.ini`: Base Alembic configuration
- `env.py`: Environment-aware migration settings
- `versions/`: Migration script directory
  - `001_create_users_table.py`: Initial user table setup

### Running Migrations
1. **Development**:
   ```bash
   # Apply all pending migrations
   alembic upgrade head

   # Rollback last migration
   alembic downgrade -1

   # Generate new migration
   alembic revision -m "description"
   ```

2. **Environment Handling**:
   - Development: Uses DATABASE_URL from `.env`
   - Production: Uses environment variables
   - Testing: Uses isolated test database

### Migration Guidelines
- Always run migrations through Alembic
- Test migrations in development first
- Back up production database before migrating
- Include both upgrade and downgrade paths
- Document complex migrations

## Examples
See the `/examples` directory for:
- Sample environment configurations
- Docker Compose variations
- Testing setups

## Development Workflow
1. Start services: `docker-compose up -d`
2. Verify health: `docker-compose ps`
3. Run tests: `poetry run pytest`
4. Monitor logs: `docker-compose logs -f`

## Troubleshooting
Common issues and solutions are documented in:
- `/tests/test_setup.md`
- `/tests/integration/README.md`

## Logging
For detailed logging configuration and usage, see:
[Gateway Logging System Documentation](../logging/README.md)
