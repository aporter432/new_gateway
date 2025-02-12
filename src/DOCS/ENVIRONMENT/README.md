# Environment Documentation

## Overview
This directory contains comprehensive documentation for all environment configurations in the Smart Gateway project.

## Environment Types

### Development Environment
- **Authentication & Security**:
  - Test credentials (OGWS_CLIENT_ID=70000934)
  - One-year token expiry for development
  - Redis-based token storage (local)
  - HTTP proxy for OGWS simulation

- **Infrastructure**:
  - LocalStack for AWS services
  - Single-node services
  - Basic health checks
  - Development proxy settings

- **Configuration**:
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
- **Authentication & Security**:
  - Secure environment variables for credentials
  - 24-hour token expiry with auto-rotation
  - Redis Enterprise with encryption
  - Full SSL/TLS implementation
  - Direct OGWS connection

- **Infrastructure**:
  - Full AWS service integration
  - Multi-node deployment
  - Advanced health monitoring
  - Load balancer configuration

- **Configuration**:
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
  ```

### Testing Environment
- **Configuration**:
  - Isolated Redis instance (DB 15)
  - Mock OGWS endpoints
  - Metrics isolation
  - Separate logging configuration

## Infrastructure Requirements

### Development
- Redis (Message state, caching)
- PostgreSQL (Customer data)
- LocalStack (AWS emulation)
- Nginx (OGWS proxy)

### Production
- **Redis Enterprise/ElastiCache**:
  - Multi-AZ deployment
  - Automatic failover
  - Encryption at rest

- **DynamoDB**:
  - Auto-scaling enabled
  - Point-in-time recovery
  - Global tables for DR

- **Load Balancer**:
  - SSL termination
  - Health checks
  - Rate limiting

## Environment Variables

### Core Files
- `.env` - Active development environment configuration
- `.env.example` - Template with safe default values
- `docker-compose.yml` - Container orchestration
- `nginx.conf` - OGWS proxy configuration

### Variable Categories
1. **Application Settings**:
   - APP_NAME
   - ENVIRONMENT
   - DEBUG
   - LOG_LEVEL

2. **Service Configuration**:
   - Database connection details
   - Redis settings
   - AWS credentials
   - API endpoints

3. **Security Settings**:
   - Authentication tokens
   - API keys
   - Encryption keys
   - Rate limits

## Deployment Procedures

### Development Setup
1. Clone repository
2. Copy `.env.example` to `.env`
3. Configure development settings
4. Start services with Docker Compose

### Production Deployment
1. Configure environment variables
2. Deploy infrastructure
3. Deploy application services
4. Verify monitoring and logging

## Security Guidelines

1. **Credential Management**:
   - Never commit sensitive data
   - Use environment variables
   - Rotate credentials regularly
   - Implement least privilege

2. **Network Security**:
   - Configure firewalls
   - Use SSL/TLS
   - Implement rate limiting
   - Monitor access logs

3. **Data Protection**:
   - Encrypt sensitive data
   - Regular backups
   - Access control
   - Audit logging

## Monitoring Setup

### Development
- Local log files
- Debug level logging
- All metrics enabled
- Basic Prometheus/Grafana

### Production
- CloudWatch logging
- Production log levels
- Aggregated metrics
- Advanced alerting

## Performance Tuning

### Development
- Basic rate limiting
- Simple caching
- Default timeouts
- Flexible validation

### Production
- Strict rate limits
- Distributed caching
- Optimized timeouts
- Strict validation 