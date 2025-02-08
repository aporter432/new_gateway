# Gateway Logging System

A comprehensive, enterprise-grade logging system designed for high-performance message processing and monitoring.

## Architecture

### Components
```
logging/
├── formatters.py        # Custom log formatters for different components
├── handlers/           
│   ├── batch.py        # Buffered logging for high volume
│   ├── file.py         # File-based logging with rotation
│   ├── metrics.py      # Metrics collection
│   ├── stream.py       # Console output
│   └── syslog.py       # System logging integration
├── loggers/
│   ├── api.py          # API-specific logging
│   ├── auth.py         # Authentication logging
│   ├── factory.py      # Logger factory implementation
│   ├── infra.py        # Infrastructure logging
│   ├── protocol.py     # Protocol-specific logging
│   └── system.py       # System-wide logging
└── log_settings.py     # Centralized configuration
```

## Features

### High-Performance Logging
- **Batch Processing**: Buffered writes for high-volume operations
- **Async Flushing**: Background thread for log writing
- **Memory Management**: Configurable buffer sizes and flush intervals
- **Rotation**: Size-based log rotation with compression

### Component-Specific Logging
- **API Logs**: Request tracking, endpoints, latencies
- **Protocol Logs**: Message IDs, validation details
- **Auth Logs**: Security events (sanitized)
- **Infrastructure Logs**: System state, resource usage
- **Metrics**: Performance and operational metrics

### Security
- **Sanitization**: Automatic PII and credential removal
- **Audit Trail**: Authentication and authorization events
- **Syslog Integration**: Security event monitoring
- **Access Control**: Component-specific log files

## Usage

### Basic Logging
```python
from core.logging.loggers import get_api_logger

logger = get_api_logger("endpoint_name")
logger.info("Processing request", extra={
    "request_id": "123",
    "endpoint": "/api/v1/messages",
    "customer_id": "customer_123"
})
```

### High-Volume Logging
```python
from core.logging.loggers import get_protocol_logger

logger = get_protocol_logger("message_processor")
logger.debug("Processing message batch", extra={
    "batch_size": 100,
    "message_ids": ["msg1", "msg2"],
    "customer_id": "customer_123"
})
```

### Metrics Logging
```python
from core.logging.loggers import get_system_logger

logger = get_system_logger("metrics")
logger.info("Message processing metrics", extra={
    "metric_name": "message_processing_rate",
    "metric_value": 1000,
    "metric_unit": "msgs/sec",
    "customer_id": "customer_123"
})
```

## Configuration

### Environment-Specific Settings
```python
class LoggingConfig:
    # Development
    development = {
        "level": "DEBUG",
        "file_rotation": "100MB",
        "backup_count": 10,
        "buffer_size": 1000
    }
    
    # Production
    production = {
        "level": "INFO",
        "file_rotation": "200MB",
        "backup_count": 20,
        "buffer_size": 5000
    }
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

### Log Cleanup Mechanism
- Automatic rotation based on file size (configured per component)
- Compression of rotated logs (*.gz format)
- Daily cleanup job removes logs older than retention period
- Separate cleanup thresholds for development/production
- Emergency cleanup if disk usage exceeds 85%

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

./logs/                   # Development logs (same structure)
```

### Error Handling

#### Batch Processing Errors
```python
try:
    # Force flush if buffer full
    if self._buffer.full():
        self.flush()

    self._buffer.put_nowait(record)
except (Full, IOError, OSError):
    # Handles:
    # - Queue full conditions
    # - IO errors during write
    # - System level errors
    self.handleError(record)
```

#### Syslog Fallback
```python
try:
    # Try local syslog first
    handler = SysLogHandler(address="/dev/log")
except (FileNotFoundError, ConnectionError):
    # Fall back to UDP syslog
    handler = SysLogHandler(
        address=("localhost", 514)
    )
```

### Component-Specific Behaviors

#### Protocol Logging
- High volume message processing
- Batch size: 5000 records
- Flush interval: 0.5 seconds
- Maximum buffer: 50000 records
- Rotation: 200MB files, 20 backups

#### Authentication Logging
- Security event tracking
- Immediate flushing
- Extended retention (365 days)
- Syslog integration for monitoring
- PII sanitization

#### Metrics Logging
- Performance data collection
- Large batch sizes for efficiency
- Frequent flushing (0.5s)
- Short retention (7 days)
- Prometheus/Grafana integration

## Log Formats

### Base Format
```json
{
    "timestamp": "2024-01-01T12:00:00.000Z",
    "level": "INFO",
    "component": "api",
    "customer_id": "customer_123",
    "asset_id": "gateway_1",
    "message": "Request processed successfully",
    "process": {
        "name": "MainProcess",
        "id": 1234
    },
    "thread": {
        "name": "MainThread",
        "id": 5678
    }
}
```

### Metrics Format
```json
{
    "timestamp": "2024-01-01T12:00:00.000Z",
    "component": "metrics",
    "metric": {
        "name": "message_processing_rate",
        "value": 1000,
        "unit": "msgs/sec",
        "tags": {
            "customer_id": "customer_123",
            "message_type": "ogx"
        }
    }
}
```

## Best Practices

### Performance
1. Use batch logging for high-volume components
2. Configure appropriate buffer sizes
3. Monitor log rotation and cleanup
4. Use structured logging with proper indexing

### Security
1. Never log sensitive data (credentials, PII)
2. Use appropriate log levels
3. Implement log retention policies
4. Monitor log access

### Monitoring
1. Set up log aggregation
2. Configure alerts for error patterns
3. Monitor log volume and rotation
4. Track metrics for system health

## Troubleshooting

### Common Issues
1. **High Log Volume**
   - Increase batch size
   - Adjust rotation settings
   - Review log levels

2. **Missing Logs**
   - Check file permissions
   - Verify logger configuration
   - Monitor disk space

3. **Performance Impact**
   - Tune buffer sizes
   - Adjust flush intervals
   - Review log levels

### Debug Mode
```python
# Enable debug logging for specific component
logger = get_protocol_logger("debug")
logger.setLevel(logging.DEBUG)
```

## Integration

### Prometheus Metrics
- Message processing rates
- Error counts
- Token refresh metrics
- API latencies

### Grafana Dashboards
- System health
- Message throughput
- Error tracking
- Performance metrics

### Log Aggregation
- ELK Stack integration
- CloudWatch Logs
- Custom metrics collection
- Alert configuration 