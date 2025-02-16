# Testing Environment

## Overview
Configuration and setup for all testing environments in the Smart Gateway project.

## Environment Types

### 1. Integration Testing
Configured in `/tests/integration/`:
- Isolated Redis instance (DB 15)
- LocalStack for AWS services
- Mock OGWS endpoints
- Metrics isolation

### 2. End-to-End Testing
Configured in `/tests/e2e/`:
- Full service stack
- Real service connections
- Production-like configuration
- Performance monitoring

### 3. Unit Testing
- No external dependencies
- Mock services and responses
- In-memory databases
- Fast execution

## Test Environment Setup
1. **Prerequisites**
   - Docker and Docker Compose
   - Python 3.11.6+
   - Poetry 1.7.1+
   - Test OGWS credentials

2. **Configuration**
   ```bash
   # Required variables
   ENVIRONMENT=test
   REDIS_HOST=redis
   REDIS_PORT=6379
   REDIS_DB=15
   OGWS_BASE_URL=http://proxy:8080/api/v1.0
   OGWS_CLIENT_ID=70000934
   OGWS_TEST_MODE=true
   ```

## Service Configuration

### Redis
- Test database: DB 15
- Automatic cleanup between tests
- Connection verification
- State management utilities

### AWS Services (LocalStack)
- DynamoDB for message persistence
- SQS for message queuing
- CloudWatch for logging
- Test credentials

### Metrics
- Isolated registry per test
- Metric value verification
- No metric bleeding
- Performance tracking

## Test Data Management
- Automated cleanup
- Isolated test databases
- Mock data generation
- State verification

## Best Practices
1. **Service Isolation**
   - Use dedicated test databases
   - Clean state between tests
   - Avoid resource sharing

2. **Resource Management**
   - Use helper functions
   - Verify service health
   - Handle cleanup properly

3. **Security**
   - Use test credentials only
   - Isolate from production
   - Mock sensitive services

## Additional Resources
- `/tests/test_setup.md` - Detailed setup guide
- `/tests/integration/README.md` - Integration testing
- `/tests/e2e/README.md` - End-to-end testing
- `/tests/unit/protocol/ogx/validation/README.md` - OGx validation

## Logging
For detailed logging configuration and usage in test environments, see:
[Gateway Logging System Documentation](../logging/README.md)

Test-specific logging features are covered in the logging documentation under:
- Environment-Specific Settings
- Component-Specific Behaviors
- Error Handling
- Best Practices

## Logging Configuration
### Test Environment Settings
```python
# Located in src/core/logging/log_settings.py
test = {
    "level": "DEBUG",
    "file_rotation": "50MB",
    "backup_count": 5,
    "buffer_size": 100
}
```

### Test Log Directory
```
./logs/test/               # Test-specific logs
├── protocol/
│   └── test_protocol.log
├── auth/
│   └── test_auth.log
├── api/
│   └── test_api.log
└── metrics/
    └── test_metrics.log
```

### Test Logging Features
1. **Isolation**:
   - Separate log files for each test run
   - Clean log files between tests
   - Component-specific logging
   - Test run identifiers in logs

2. **Debug Information**:
   - Detailed error logging
   - Request/Response payloads
   - State transitions
   - Performance metrics

3. **Test-Specific Logging**:
   ```python
   # Example test logging
   from core.logging.loggers import get_test_logger

   logger = get_test_logger("test_name")
   logger.debug("Test step completed", extra={
       "test_id": "test_123",
       "step": "message_validation",
       "result": "success"
   })
   ```

### Log Monitoring During Tests
1. View test logs:
   ```bash
   # All test logs
   tail -f logs/test/*/test_*.log

   # Component-specific test logs
   tail -f logs/test/api/test_api.log
   ```

2. Test run logs:
   ```bash
   # Latest test run
   docker-compose logs -f test
   ```

### Log Cleanup
- Automatic cleanup after each test run
- Keep failed test logs for debugging
- Maximum log retention: 7 days
- Emergency cleanup at 85% disk usage

# Integration Test Environment

This directory contains the integration test suite for the Gateway service. The test environment is designed to provide a reliable, isolated, and comprehensive way to test the service's interactions with its dependencies and external services.

## Environment Structure

### Core Configuration Files

1. `conftest.py` (Root Level)
   - Manages test session-wide fixtures and service connections
   - Handles environment variables and service health checks
   - Provides fixtures for:
     - Redis connection management
     - DynamoDB (LocalStack) client
     - SQS client
     - CloudWatch client
     - HTTP client for API testing
     - Metrics registry management

2. `helpers.py`
   - Contains utility classes and functions for test operations:
     - `RedisHelper`: Redis state management
     - `DynamoDBHelper`: Test table operations
     - `MetricsHelper`: Metrics verification
     - `MessageHelper`: Test message generation and validation

## Service Configuration

### Redis
- Test database: DB 15 (isolated from production)
- Automatic cleanup between tests
- Connection verification before tests
- State management utilities

### AWS Services (via LocalStack)
- DynamoDB for message persistence
- SQS for message queuing
- CloudWatch for logging
- Configured with test credentials

### Metrics Collection
- Isolated registry per test
- Metric value verification
- Prevents metric bleeding between tests

## Environment Variables
```
ENVIRONMENT=test
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_DB=15
AWS_ENDPOINT_URL=http://localhost:4566
AWS_REGION=us-east-1
OGWS_BASE_URL=http://proxy:8080/api/v1.0
```

## Test Helpers

### Message State Management
```python
# Example usage
async def test_message_flow():
    redis_helper, dynamo_helper = await setup_test_environment(
        redis_client,
        dynamodb_client,
        "test_messages"
    )

    # Create and verify message state
    await redis_helper.set_message_state("msg_id", {"state": "processing"})
    state = await redis_helper.get_message_state("msg_id")
```

### Test Data Generation
```python
# Example usage
message = MessageHelper.create_test_message(
    message_type="test",
    payload={"key": "value"}
)
```

### Metrics Verification
```python
# Example usage
MetricsHelper.assert_metric_present(metrics_data, "message_processed_total")
MetricsHelper.assert_metric_value(metrics_data, "queue_size", 1.0)
```

## Service Health Verification

The environment automatically verifies the health of required services before running tests:
- Redis connection check
- LocalStack services health check
- Metrics registry initialization

## Clean Up Procedures

1. Automatic cleanup between tests:
   - Redis database flushing
   - Metrics registry reset
   - Test table cleanup

2. Session cleanup:
   - Service connections closed
   - Test databases cleaned
   - Temporary resources removed

## Best Practices

1. **Service Isolation**
   - Use dedicated test databases
   - Clean state between tests
   - Avoid sharing resources between tests

2. **Resource Management**
   - Always use helper functions for cleanup
   - Verify service health before tests
   - Handle connection errors gracefully

3. **Test Data**
   - Use helper classes for consistent test data
   - Avoid hardcoding test values
   - Clean up test data after use

4. **Metrics Testing**
   - Use isolated registries
   - Verify metric presence and values
   - Reset metrics between tests

## Known Issues

1. Linter Warnings:
   - `aioredis` import resolution
   - Type hints for `boto3.client`
   - These are known issues and don't affect functionality

## Future Improvements

1. Add PostgreSQL integration
2. Enhance service mocking capabilities
3. Add more helper utilities for common test scenarios
4. Improve error handling and reporting
