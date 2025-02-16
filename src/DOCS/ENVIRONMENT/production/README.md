# Production Environment

## Overview
Production environment configuration and deployment guidelines for the Smart Gateway service.

## Security Requirements
- No file-based configuration (`.env` not used)
- All credentials managed via secure environment variables
- Strict access control and authentication
- Regular security audits and updates

## Environment Variables
Required variables must be set in the production environment:
```bash
ENVIRONMENT=production
REDIS_HOST=${REDIS_CLUSTER_URL}
DYNAMODB_TABLE_NAME=${MESSAGE_STATE_TABLE}
OGWS_BASE_URL=${OGWS_PROD_URL}
OGWS_CLIENT_ID=${OGWS_PROD_CLIENT_ID}
OGWS_CLIENT_SECRET=${OGWS_PROD_CLIENT_SECRET}
CUSTOMER_ID=${CUSTOMER_ID}
```

## Infrastructure Requirements
### Redis Enterprise/ElastiCache
- Multi-AZ deployment
- Automatic failover
- Encryption at rest
- Backup configuration

### DynamoDB
- Auto-scaling enabled
- Point-in-time recovery
- Global tables for DR
- Capacity planning

### Load Balancer
- SSL termination
- Health checks
- Rate limiting
- Security groups

## Deployment Process
1. **Pre-deployment**
   - Validate configuration
   - Run integration tests
   - Check dependencies

2. **Deployment Steps**
   - Update environment variables
   - Deploy infrastructure changes
   - Rolling update of services
   - Verify health checks

3. **Post-deployment**
   - Monitor error rates
   - Verify metrics
   - Check log patterns

## Monitoring
### Required Metrics
- Message processing rates
- Error rates
- Token refresh metrics
- API latencies
- Resource utilization

### Alerting
Configure alerts for:
- High message processing latency
- Token refresh failures
- Message queue backlog
- Resource exhaustion

## Backup and Recovery
- Regular state backups
- Disaster recovery procedures
- Failover testing
- Data retention policies

## Security Procedures
- Credential rotation
- Access control updates
- Security patch management
- Audit logging

## Logging
For detailed logging configuration and usage in production, see:
[Gateway Logging System Documentation](../logging/README.md)

Production-specific logging considerations are covered in the logging documentation under:
- Environment-Specific Settings
- Log Retention Policies
- Security Considerations
- Component-Specific Behaviors

## Logging Configuration
### Production Log Settings
```python
# Located in src/core/logging/log_settings.py
production = {
    "level": "INFO",
    "file_rotation": "200MB",
    "backup_count": 20,
    "buffer_size": 5000
}
```

### Log Directory Structure
```
/var/log/gateway/          # Production logs
├── protocol/
│   ├── current.log       # Active log file
│   └── protocol.log.*    # Rotated logs
├── auth/
│   ├── current.log
│   └── auth.log.*
├── api/
│   ├── current.log
│   └── api.log.*
└── metrics/
    ├── current.log
    └── metrics.log.*
```

### Log Retention Policies
```python
# Retention periods (in days) by component
retention = {
    LogComponent.PROTOCOL: 30,    # Message processing logs
    LogComponent.SYSTEM: 90,      # System operations
    LogComponent.INFRA: 60,       # Infrastructure logs
    LogComponent.API: 30,         # API request logs
    LogComponent.AUTH: 365,       # Authentication (kept longer)
    LogComponent.METRICS: 7       # Performance metrics
}
```

### Security Considerations
- PII and credential sanitization enabled
- Syslog integration for security monitoring
- Component-specific access controls
- Audit trail for authentication events

### Log Management
1. **Rotation**:
   - Size-based rotation (200MB per file)
   - Compression of rotated logs
   - 20 backup files per component

2. **Cleanup**:
   - Daily cleanup job based on retention policy
   - Emergency cleanup at 85% disk usage
   - Compressed archive management

3. **Monitoring**:
   - CloudWatch integration
   - Log aggregation
   - Alert configuration
   - Performance metrics extraction
