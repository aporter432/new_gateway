# SMART-GATEWAY

A comprehensive enterprise gateway implementation for managing ORBCOMM ISAT (MTWS/MTBP) and OGx protocols, with production-grade security, monitoring, and scalability features.

## Documentation Index

This project contains several README files and documentation resources:

### Main Documentation
- `/README.md` (this file) - Main project documentation
- `/CONTRIBUTING.md` - Contribution guidelines and standards
- `/CHANGELOG.md` - Version history and changes

### Environment Documentation
- `/src/DOCS/ENVIRONMENT/README.md` - Environment setup overview
  - `/development/README.md` - Development environment setup
  - `/production/README.md` - Production deployment and security
  - `/testing/README.md` - Test environment configuration

### Test Documentation
- `/tests/test_setup.md` - Test environment setup guide
- `/tests/integration/README.md` - Integration testing guide
- `/tests/e2e/README.md` - End-to-end testing documentation
- `/tests/unit/protocol/ogx/validation/README.md` - OGx validation test documentation
- `/tests/rules/cursor_rules_investigation.md` - Rules 

### Component Documentation
- `/src/DOCS/ENVIRONMENT/logging/README.md` - Logging system documentation
- `/src/protocols/ogx/README.md` - OGx protocol implementation details

### ISAT Documentation
- `/src/DOCS/ISAT DOCS/INTRO/intro.md` - ISAT introduction
- `/src/DOCS/ISAT DOCS/SIN_VALUES.md` - SIN values reference
- `/src/DOCS/ISAT DOCS/Terminal_Software_Architecture/architecture.md` - Terminal architecture
- `/src/DOCS/ISAT DOCS/LUA_FIRMWARE_EXTENSIONS/systems.md` - LUA systems documentation
- `/src/DOCS/ISAT DOCS/LUA_FIRMWARE_EXTENSIONS/global_functions.md` - LUA global functions

### Additional Resources
- `.pytest_cache/README.md` - Pytest cache information
- Various package documentation in `.venv/lib/python3.11/site-packages/`

## Key Application Files

### Core Application
- `/src/api/main.py` - Main FastAPI application entry point
  - API route registration
  - Middleware configuration
  - Health check endpoints
  - Application startup/shutdown events

### Configuration
- `/src/core/app_settings.py` - Application settings management
  - Environment-specific configuration
  - Pydantic settings validation
  - Development/Production mode handling
  - Security constraints

### Environment
- `.env` - Primary environment configuration file
  - Location: `/Users/aaronporter/Desktop/Projects/new_gateway/.env`
  - Purpose: Development environment defaults
  - Contains:
    - Application settings (APP_NAME, DEBUG, etc.)
    - Server configuration (HOST, PORT, WORKERS)
    - Database and Redis connection details
    - AWS credentials and endpoints
    - Gateway-specific settings (ISAT, OGx)
    - Security and monitoring parameters
  - Note: Production should use secure environment variables, not this file

### Development vs Production Configuration
- **Development**:
  - Uses `.env` file for easy configuration
  - Contains safe default values
  - Includes development-specific settings
  - Can be version controlled (with example values)

- **Production**:
  - Uses secure environment variables
  - No file-based configuration
  - Credentials managed via secure store
  - Environment-specific settings

### Proxy Configuration
- `nginx.conf` - OGWS proxy configuration
  - API routing
  - Health check endpoint
  - Request buffering
  - SSL configuration

## Overview

Smart Gateway provides a robust, production-ready interface for ORBCOMM's OGWS (OGx Gateway Web Service), supporting:

- **High Availability**: Containerized microservices architecture with health monitoring
- **Security**: Token-based authentication with automatic rotation
- **Scalability**: Redis-backed caching and DynamoDB for production workloads
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Compliance**: Adherence to OGWS-1.txt specifications

## OGWS Integration Details

### Authentication & Security
- **Token Management**:
  - Automatic token acquisition and rotation
  - Redis-based token storage with metadata
  - Token validation and refresh logic
  - Production credential management
  - Rate limiting and throttling

### Message Processing Pipeline
- **Validation**:
  - Message format and size constraints
  - Field-level validation
  - Network-specific payload limits
  - Terminal ID verification
  - Field serialization (OGWS-1.txt compliance):
    - Capitalized field names required (e.g., "Name", "Value", "Type")
    - Use `model_dump(by_alias=True)` for proper OGWS field serialization
    - String representation for numeric and boolean values in output

- **State Management**:
  - Redis (Development) / DynamoDB (Production) state tracking
  - State transition validation
  - Error state handling
  - Message history tracking

- **Transport Selection**:
  - Smart routing between Satellite/Cellular
  - Network optimization
  - Cost-based routing decisions
  - Failover handling

### Device Support
- **Terminal Types**:
  - ST6100 devices
  - ST9100 devices
  - Hardware control interface
  - Modem management

- **Configuration**:
  - LSF (Lua Service Framework) integration
  - Template-based configuration
  - Remote updates
  - Status monitoring

## Deployment Configuration

### Development Environment
```yaml
services:
  app:
    build: .
    environment:
      - REDIS_HOST=redis
      - REDIS_PORT=6379
      - OGWS_BASE_URL=http://proxy:8080/api/v1.0
      - OGWS_CLIENT_ID=70000934
      - OGWS_TEST_MODE=true
    depends_on:
      - redis
      - proxy
```

### Production Environment
```yaml
services:
  app:
    image: smart-gateway:${VERSION}
    environment:
      - ENVIRONMENT=production
      - REDIS_HOST=${REDIS_CLUSTER_URL}
      - DYNAMODB_TABLE_NAME=${MESSAGE_STATE_TABLE}
      - OGWS_BASE_URL=${OGWS_PROD_URL}
      - OGWS_CLIENT_ID=${OGWS_PROD_CLIENT_ID}
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
      restart_policy:
        condition: on-failure
    logging:
      driver: awslogs
      options:
        awslogs-group: /smart-gateway/production
```

### Infrastructure Requirements

#### Development
- Redis (Message state, caching)
- PostgreSQL (Customer data)
- LocalStack (AWS emulation)
- Nginx (OGWS proxy)

#### Production
- Redis Enterprise/ElastiCache
  - Multi-AZ deployment
  - Automatic failover
  - Encryption at rest

- DynamoDB
  - Auto-scaling enabled
  - Point-in-time recovery
  - Global tables for DR

- Load Balancer
  - SSL termination
  - Health checks
  - Rate limiting

## Monitoring & Metrics

### Message Processing
- **Rate Metrics**:
  - Messages processed per second
  - Success/failure rates
  - Processing latency
  - Queue depth

- **State Transitions**:
  - State change rates
  - Time in each state
  - Error state frequency
  - Recovery times

### Authentication
- **Token Metrics**:
  - Token refresh rates
  - Validation success/failure
  - Token lifetime stats
  - Auth errors by type

### Network Performance
- **Transport Metrics**:
  - Satellite vs Cellular usage
  - Network latency
  - Payload sizes
  - Bandwidth utilization

### System Health
- **Resource Usage**:
  - CPU/Memory utilization
  - Redis connection pool
  - DynamoDB capacity
  - API response times

### Alerting Rules
```yaml
rules:
  - alert: HighMessageProcessingLatency
    expr: message_processing_latency_seconds > 5
    for: 5m
    labels:
      severity: warning
  
  - alert: TokenRefreshFailure
    expr: token_refresh_failures_total > 0
    for: 5m
    labels:
      severity: critical

  - alert: MessageQueueBacklog
    expr: message_queue_size > 1000
    for: 10m
    labels:
      severity: warning
```

## Operational Procedures

### Deployment
1. **Pre-deployment**:
   - Validate configuration
   - Run integration tests
   - Check dependencies

2. **Deployment Steps**:
   - Update environment variables
   - Deploy infrastructure changes
   - Rolling update of services
   - Verify health checks

3. **Post-deployment**:
   - Monitor error rates
   - Verify metrics
   - Check log patterns

### Troubleshooting

#### Common Issues
1. **Token Errors**:
   - Check OGWS credentials
   - Verify Redis connectivity
   - Check token rotation logs

2. **Message Processing**:
   - Verify message format
   - Check rate limits
   - Monitor state transitions

3. **Performance Issues**:
   - Review Redis metrics
   - Check DynamoDB capacity
   - Monitor API latencies

## Architecture

### Core Components

- **API Layer** (`src/api/`)
  - FastAPI-based REST endpoints
  - Authentication middleware
  - Rate limiting
  - Request validation

- **Protocol Layer** (`src/protocols/`)
  - OGWS message processing
  - State management
  - Transport selection
  - Error handling

- **Infrastructure** (`src/infrastructure/`)
  - Redis caching
  - DynamoDB integration
  - AWS service clients
  - Metrics collection

### Service Dependencies

- **Development**
  - Redis (Message state, caching)
  - PostgreSQL (Customer data)
  - LocalStack (AWS service emulation)
  - Nginx (OGWS proxy)

- **Production**
  - AWS DynamoDB
  - AWS CloudWatch
  - Redis Enterprise/ElastiCache
  - Production-grade PostgreSQL

## Getting Started

### Prerequisites

- Python 3.11.6+
- Docker and Docker Compose
- AWS credentials
- Poetry 1.7.1+

### Development Setup

1. **Clone and Configure**
   ```bash
   git clone [repository-url]
   cd new_gateway
   cp .env.example .env
   # Edit .env with your settings
   ```

2. **Install Dependencies**
   ```bash
   poetry install
   poetry install --with dev  # Include development tools
   ```

3. **Start Development Services**
   ```bash
   docker-compose up -d
   ```

4. **Initialize Development Environment**
   ```bash
   poetry run python -m scripts.auth.setup_token  # Set up initial OGWS token
   poetry run pytest  # Verify setup with tests
   ```

### Production Deployment

1. **Environment Configuration**
   - Set required environment variables:
     ```
     ENVIRONMENT=production
     OGWS_CLIENT_ID=<production-id>
     OGWS_CLIENT_SECRET=<production-secret>
     CUSTOMER_ID=<customer-id>
     ```
   - Configure AWS credentials
   - Set up monitoring endpoints

2. **Infrastructure Requirements**
   - DynamoDB table for message state
   - Redis cluster for caching
   - Load balancer configuration
   - Network security groups

3. **Deployment Process**
   ```bash
   # Build production image
   docker build -t smart-gateway:latest .
   
   # Deploy with production compose file
   docker-compose -f docker-compose.prod.yml up -d
   ```

4. **Health Verification**
   ```bash
   curl http://localhost:8000/health
   ```

## Development Workflow

### Code Quality

The project enforces strict quality standards through automated tools:

```bash
# Format code
poetry run black .
poetry run isort .

# Static analysis
poetry run mypy .
poetry run flake8

# Run tests with coverage
poetry run pytest --cov=src tests/
```

### Testing Strategy

1. **Unit Tests**
   ```bash
   poetry run pytest tests/unit
   ```

2. **Integration Tests**
   ```bash
   poetry run pytest tests/integration
   ```

3. **Performance Tests**
   ```bash
   poetry run locust -f tests/performance/locustfile.py
   ```

### Monitoring and Metrics

- **Prometheus Metrics**
  - Message processing rates
  - Error rates
  - Token refresh metrics
  - API latencies

- **Grafana Dashboards**
  - System health
  - Message throughput
  - Error tracking
  - Performance metrics

## API Documentation

- **OpenAPI Documentation**: Available at `/docs` when running
- **Authentication**: Bearer token using OGWS credentials
- **Rate Limiting**: Configurable per endpoint
- **Error Handling**: Standardized error responses

## Production Considerations

### Security

- Credentials management via environment variables
- Token rotation and validation
- Request authentication
- Rate limiting and throttling

### Scaling

- Horizontal scaling of API nodes
- Redis cluster configuration
- DynamoDB capacity planning
- Load balancer setup

### Monitoring

- CloudWatch integration
- Prometheus metrics
- Grafana dashboards
- Error tracking and alerting

### Backup and Recovery

- DynamoDB point-in-time recovery
- Redis persistence configuration
- Regular state backups
- Disaster recovery procedures

## Troubleshooting

### Common Issues

1. **Token Errors**
   - Check OGWS credentials
   - Verify token storage in Redis
   - Check token rotation logs

2. **Message Processing**
   - Verify message format
   - Check rate limits
   - Monitor state transitions

3. **Performance Issues**
   - Review Redis metrics
   - Check DynamoDB capacity
   - Monitor API latencies

### Logging

- Structured JSON logging
- Component-specific loggers
- Error tracking with context
- Performance monitoring

## Contributing

1. Branch naming: `feature/`, `bugfix/`, `hotfix/`
2. Commit message format: `type(scope): description`
3. Required checks before PR:
   - All tests passing
   - Code formatting
   - Type checking
   - No security vulnerabilities

## License

Proprietary - All rights reserved

## Support

For production support:
- Email: [support-email]
- Documentation: [docs-url]
- Emergency: [emergency-contact]

## Development vs Production Differences

### Authentication & Security
- **Development**:
  - Uses test credentials (OGWS_CLIENT_ID=70000934)
  - One-year token expiry for extended development
  - Redis-based token storage (local)
  - Protected mode disabled for easy access
  - HTTP proxy for OGWS simulation

- **Production**:
  - Secure environment variables for credentials
  - 24-hour token expiry with auto-rotation
  - Redis Enterprise with encryption
  - Full SSL/TLS implementation
  - Direct OGWS connection

### State Management
- **Development**:
  - Local Redis instance
  - Simple persistence (RDB + AOF)
  - 1GB memory limit
  - Basic monitoring

- **Production**:
  - Redis Enterprise/ElastiCache cluster
  - DynamoDB for message state
  - Auto-scaling and failover
  - Cross-AZ replication

### Logging & Monitoring
- **Development**:
  - Local log files in `logs/` directory
  - Debug level logging
  - All metrics enabled
  - Basic Prometheus/Grafana setup

- **Production**:
  - CloudWatch logging
  - Production log levels (INFO/ERROR)
  - Aggregated metrics
  - Advanced alerting rules

### Infrastructure
- **Development**:
  - LocalStack for AWS services
  - Single-node services
  - Basic health checks
  - Development proxy settings

- **Production**:
  - Full AWS service integration
  - Multi-node deployment
  - Advanced health monitoring
  - Load balancer configuration

### Performance Tuning
- **Development**:
  - Basic rate limiting
  - Simple caching
  - Default timeouts
  - Flexible validation

- **Production**:
  - Strict rate limits
  - Distributed caching
  - Optimized timeouts
  - Strict validation
