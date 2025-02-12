# End-to-End Tests

This directory contains end-to-end tests that verify the gateway's functionality against real external services and APIs.

## Structure

```
e2e/
├── protocol/
│   └── ogx/
│       ├── message_flow/     # Complete message flow tests
│       ├── services/         # Service-level e2e tests
│       └── validation/       # Validation with real data
├── api/                      # API endpoint tests
├── scenarios/               # Complex multi-step scenarios
└── assets/                  # Test data and fixtures
```

## Test Categories

### Protocol Tests
- Complete message flows
- Real API interactions
- Full validation chains
- Actual network conditions

### Service Tests
- Real service interactions
- External API calls
- Database operations
- Redis operations

### Scenario Tests
- Multi-step workflows
- Complex use cases
- Error recovery scenarios
- Performance scenarios

## Setup and Installation

1. Run the setup script to create the test environment:
```bash
chmod +x tests/e2e/setup_e2e.sh
./tests/e2e/setup_e2e.sh
```

2. Configure your environment:
```bash
cp tests/e2e/.env.e2e.example tests/e2e/.env.e2e
# Edit .env.e2e with your credentials
```

## Configuration

### Environment Variables
Tests in this directory require:
- Valid API credentials
- Running services (Redis, PostgreSQL)
- Network access to OGWS
- Proper environment variables

### Test Database
- Uses Redis DB 15 (isolated from development)
- Automatic cleanup between tests
- Separate state storage

### Test Settings
```ini
# Available in .env.e2e
E2E_TEST_TIMEOUT=300    # Default timeout in seconds
E2E_POLL_INTERVAL=10    # State polling interval
E2E_MAX_RETRIES=3      # Maximum retry attempts
E2E_CLEANUP_ENABLED=true
```

## Running Tests

### Basic Usage
```bash
# Run all e2e tests (excluding slow tests)
pytest tests/e2e -v

# Run including slow tests
pytest tests/e2e --slow

# Run specific test category
pytest tests/e2e/protocol/ogx/message_flow -v

# Run with real credentials
OGWS_CLIENT_ID=xxxxx OGWS_CLIENT_SECRET=xxxxx pytest tests/e2e -v
```

### Test Selection
- Default: Skips slow tests
- Use `--slow` flag to include slow tests
- Use `-m` to select specific markers

### Available Markers
- `@pytest.mark.e2e`: Marks test as end-to-end test
- `@pytest.mark.external_api`: Test requires external API
- `@pytest.mark.requires_credentials`: Test needs real credentials
- `@pytest.mark.slow`: Long-running tests

## Test Features

### Shared Fixtures
- `settings`: Validated test settings
- `redis`: Isolated Redis connection
- `protocol_handler`: Authenticated handler
- `test_id`: Unique test identifier
- `event_loop`: Async test support

### Automatic Cleanup
- Redis cleanup before/after tests
- Automatic resource cleanup
- State management

### Logging and Monitoring
- Detailed test logging
- API call tracking
- Performance monitoring
- Error tracking

## Important Notes

1. These tests interact with real services
2. May incur API usage costs
3. Subject to rate limiting
4. Can take longer to run
5. Require proper credentials
6. May affect external systems

## Best Practices

1. Always use test credentials
2. Clean up after tests
3. Handle rate limits
4. Set appropriate timeouts
5. Use unique identifiers
6. Log all API interactions

## Troubleshooting

### Common Issues
1. Missing Credentials
   - Check .env.e2e configuration
   - Verify environment variables

2. Connection Issues
   - Verify network access
   - Check service health
   - Validate proxy settings

3. Test Failures
   - Check logs for details
   - Verify rate limits
   - Check service status

### Debug Commands
```bash
# Run failed tests with more detail
pytest tests/e2e [test_file] -v -s

# Check test logs
pytest tests/e2e --log-cli-level=DEBUG

# Run specific test with debugging
pytest tests/e2e [test_file]::[test_name] -v -s --pdb
```

## Support

For test-related issues:
1. Check the logs first
2. Verify service health
3. Ensure correct environment variables
4. Review test requirements

For additional support:
- Review the test documentation
- Check the development guide
- Contact the development team 