# Gateway Testing Guide

## Test Environment Types

### Integration Tests (Docker-Based)
Integration tests are designed to run exclusively in Docker containers. They require:
- Full Docker environment (redis, postgres, localstack, etc.)
- Docker network connectivity between services
- Specific container names and ports

**Important:** Never run integration tests locally. Always use:
```bash
# Run all integration tests
docker-compose run test pytest tests/integration

# Run specific integration test
docker-compose run test pytest tests/integration/path/to/test.py
```

### Unit Tests (Local)
Unit tests can run locally without Docker:
```bash
poetry run pytest tests/unit
```

## Docker Environment Setup

1. Required Services:
```yaml
services:
  - new_gateway-redis (Redis server on port 6379)
  - new_gateway-db (PostgreSQL on port 5432)
  - new_gateway-localstack (AWS services on port 4566)
  - new_gateway-proxy (OGx proxy on port 8080)
```

2. Start Docker Environment:
```bash
# Start all services
docker-compose up -d

# Verify services
docker-compose ps
```

## Prerequisites

Before running tests, ensure you have:
- Docker and Docker Compose installed
- Python 3.11.6+ installed
- Poetry 1.7.1+ installed
- Access to test OGx credentials

## Environment Setup

1. Start the development environment:
```bash
# Start all services
docker-compose up -d

# Verify all services are running and healthy
docker-compose ps
```

2. Verify environment variables:
```bash
# Copy example environment file if not done
cp .env.example .env

# Required variables for testing:
ENVIRONMENT=test
REDIS_HOST=redis
REDIS_PORT=6379
REDIS_DB=15
OGx_BASE_URL=http://proxy:8080/api/v1.0
OGx_CLIENT_ID=70000934  # Test account
OGx_TEST_MODE=true
```

## Test Execution Plan

### 1. Basic Connectivity Tests

```bash
# Test Redis connection
docker-compose exec redis redis-cli ping
# Expected: PONG

# Test OGx proxy
curl http://localhost:8080/health
# Expected: 200 OK

# Test gateway health
curl http://localhost:8000/health
# Expected: 200 OK
```

### 2. Authentication Tests

```bash
# Run token setup test
docker-compose run test python -m tests.api.auth.test_token_setup

# Run authentication test suite
docker-compose run test pytest tests/integration/api/auth/test_token_setup.py -v
docker-compose run test pytest tests/integration/api/auth/test_token_errors.py -v
```

### 3. Message Processing Tests

```bash
# Run protocol handler tests
docker-compose run test pytest tests/integration/protocol/ogx/services/ -v

# Run message validation tests
docker-compose run test pytest tests/integration/protocol/ogx/validation/ -v
```

### 4. End-to-End Flow Test

```bash
# Run the gateway flow test
docker-compose run test pytest tests/integration/test_gateway_flow.py -v
```

### 5. Complete Test Suite

```bash
# Run all tests with coverage
docker-compose run test pytest --cov=src tests/ -v --cov-report=term-missing
```

## Monitoring and Verification

### 1. Log Monitoring

```bash
# Monitor gateway logs
docker-compose logs -f app

# Monitor Redis logs
docker-compose logs -f redis

# Monitor test execution
docker-compose logs -f test
```

### 2. Metrics Verification

```bash
# Check gateway metrics
curl http://localhost:8000/metrics

# Access Grafana dashboard
open http://localhost:3000
# Default credentials: admin/admin

# Access Prometheus metrics
open http://localhost:9090
```

## Implementation Checklist

### Basic Setup
- [ ] All services start successfully
- [ ] Health checks pass
- [ ] Redis connection works
- [ ] OGx proxy responds

### Authentication
- [ ] Token acquisition works
- [ ] Token storage in Redis works
- [ ] Token validation works
- [ ] Token refresh works

### Message Processing
- [ ] Message validation works
- [ ] Message submission works
- [ ] State tracking works
- [ ] Error handling works

### Monitoring
- [ ] Metrics are being collected
- [ ] Grafana shows data
- [ ] Logs are being generated
- [ ] Alerts are configured

### Performance
- [ ] Rate limiting works
- [ ] Message queuing works
- [ ] Redis performance is good
- [ ] No memory leaks

## Troubleshooting Common Issues

### 1. Service Connection Issues
```bash
# Restart specific service
docker-compose restart [service_name]

# Check service logs
docker-compose logs [service_name]

# Verify network connectivity
docker network inspect gateway_net
```

### 2. Redis Issues
```bash
# Clear Redis database
docker-compose exec redis redis-cli FLUSHDB

# Check Redis info
docker-compose exec redis redis-cli INFO

# Monitor Redis in real-time
docker-compose exec redis redis-cli MONITOR
```

### 3. Test Failures
```bash
# Run failed tests with more detail
docker-compose run test pytest [test_file] -v -s

# Check test logs
docker-compose logs test

# Run specific test with debugging
docker-compose run test pytest [test_file]::[test_name] -v -s --pdb
```

## Notes

1. **Test Database Isolation**
   - Tests use Redis DB 15 (isolated from development)
   - Each test run cleans up its data
   - LocalStack provides isolated AWS services

2. **Test Environment Differences**
   - Uses test credentials
   - Relaxed rate limits
   - Additional logging
   - Mock external services

3. **Security Considerations**
   - Test credentials are for development only
   - Never use test credentials in production
   - Keep test environment isolated

## Support

For test-related issues:
1. Check the logs first
2. Verify service health
3. Ensure correct environment variables
4. Review test requirements

For additional support:
- Review the test documentation in `tests/integration/README.md`
- Check the development guide in project root
- Contact the development team

```bash
# Run token lifecycle test
docker-compose run --remove-orphans test

# Note: The test command is configured in docker-compose.yml
# If you need to run a different test, you can override the command:
# docker-compose run --remove-orphans test python -m pytest <test_path> -v
```

## Test Organization

```
tests/
├── integration/  # Docker-based integration tests
│   ├── api/     # API integration tests
│   ├── auth/    # Authentication tests
│   └── ...
├── unit/        # Local unit tests
└── ...
```

## Common Issues

1. "Redis connection failed" or similar connection errors:
   - Ensure you're running tests in Docker
   - Check if services are running: docker-compose ps
   - Verify network connectivity: docker network inspect

2. "Not running in Docker" warning:
   - Integration tests must run in Docker
   - Use docker-compose run test instead of poetry run pytest
