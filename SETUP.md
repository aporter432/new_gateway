# Smart Gateway Setup Guide

## Prerequisites

- Docker Desktop installed and running
- Git
- Poetry (Python package manager)
- Node.js 18+ (for UI development)

## Initial Setup

1. Clone the repository:
   ```bash
   git clone <repository-url>
   cd new_gateway
   ```
## Running the Application

### First Time Setup

1. Start all services:
   ```bash
   docker-compose up -d
   ```

2. Run database migrations:
   ```bash
   docker-compose exec app poetry run alembic upgrade head
   ```

   This creates the database schema and the admin user:
   - Email: aaron.porter225@gmail.com
   - Password: ThisIsRussia#225

### Regular Development

1. Start services:
   ```bash
   # Start all services
   docker-compose up -d

   # View logs
   docker-compose logs -f
   ```

2. Access the application:
   - UI: http://localhost:3001
   - API: http://localhost:8000
   - API Docs: http://localhost:8000/docs

### Database Management

The database uses a persistent volume (`postgres_data`) to store data. This means:
- Data persists between container restarts
- Data persists when containers are stopped (`docker-compose down`)
- Data is lost when volumes are removed (`docker-compose down -v`)

If you need to reset the database:
```bash
# Stop services and remove volumes
docker-compose down -v

# Start services
docker-compose up -d

# Run migrations to recreate schema and admin user
docker-compose exec app poetry run alembic upgrade head
```

### Development Workflow

1. Make changes to code
2. Run pre-commit hooks:
   ```bash
   poetry run pre-commit run --all-files
   ```

3. Run tests:
   ```bash
   docker-compose exec app poetry run pytest
   ```

### Troubleshooting

1. UI Issues:
   ```bash
   # Rebuild UI container
   docker-compose build ui
   docker-compose up -d ui
   ```

2. Database Issues:
   ```bash
   # Reset database
   docker-compose down -v
   docker-compose up -d
   docker-compose exec app poetry run alembic upgrade head
   ```

3. Cache Issues:
   ```bash
   # Clear Redis cache
   docker-compose exec redis redis-cli FLUSHALL
   ```

4. Container Issues:
   ```bash
   # Rebuild all containers
   docker-compose build --no-cache
   docker-compose up -d
   ```

## Architecture Overview

- FastAPI backend (port 8000)
- Next.js frontend (port 3001)
- Nginx proxy (port 8080)
- PostgreSQL database (port 5432)
- Redis cache (port 6379)
- LocalStack for AWS services (port 4566)
- Prometheus metrics (port 9090)
- Grafana dashboards (port 3000)

## Environment Variables

Key environment variables are set in `docker-compose.yml`. For local development, you typically don't need to modify these.

## Contributing

1. Create a feature branch
2. Make changes
3. Run pre-commit hooks
4. Run tests
5. Submit PR

## Common Commands

```bash
# View logs
docker-compose logs -f [service]

# Rebuild specific service
docker-compose build [service]

# Restart specific service
docker-compose restart [service]

# Run tests
docker-compose exec app poetry run pytest

# Create new migration
docker-compose exec app poetry run alembic revision -m "description"

# Apply migrations
docker-compose exec app poetry run alembic upgrade head
```
