Look at the volume mount configurations in more detail?
Continue investigating other potential issues?# SMART-GATEWAY

A comprehensive gateway implementation for managing ORBCOMM ISAT (MTWS/MTBP) and OGx protocols, supporting device configuration, customer hierarchy, and notifications.

## Features

- **Protocol Support**
  - ISAT MTWS/MTBP protocol implementation
  - OGx protocol implementation
  - Message state tracking and queue management

- **Device Management**
  - Support for ST6100 and ST9100 devices
  - Hardware and modem control
  - LSF (Lua Service Framework) integration
  - Configuration template management

- **Customer Management**
  - Hierarchical customer structure
  - Custom terminology support
  - Asset tracking and management

- **Notification System**
  - Multi-channel alert delivery (Email, SMS, Webhook)
  - Configurable alert triggers
  - Template-based notifications

## Project Structure

```
new_gateway/
├── src/
│   └── new_gateway/    # Main package directory
├── api/                  # API endpoints and routes
├── core/                 # Core protocol and device implementations
├── services/             # Business logic services
├── infrastructure/       # Data persistence and external integrations
└── tests/               # Unit, integration, and performance tests
```

## Requirements

- Python 3.11.6+
- Poetry (Python package manager)
- Redis
- AWS credentials (for boto3)

## Installation

1. Clone the repository

2. Install Poetry if you haven't already:
   ```bash
   curl -sSL https://install.python-poetry.org | python3 -
   ```

3. Install project dependencies:
   ```bash
   poetry install
   ```

## Development Setup

1. Activate the Poetry virtual environment:
   ```bash
   poetry shell
   ```

2. Install development dependencies:
   ```bash
   poetry install --with dev
   ```

3. Run tests:
   ```bash
   poetry run pytest
   ```

4. Start the development server:
   ```bash
   poetry run uvicorn smart_gateway.main:app --reload
   ```

## Code Quality Tools

The project includes several code quality tools configured in pyproject.toml:

- **Black**: Code formatting
  ```bash
  poetry run black .
  ```

- **isort**: Import sorting
  ```bash
  poetry run isort .
  ```

- **flake8**: Code linting
  ```bash
  poetry run flake8
  ```

- **mypy**: Static type checking
  ```bash
  poetry run mypy .
  ```

## Configuration

1. Copy the example environment file:
   ```bash
   cp .env.example .env
   ```

2. Configure environment variables in `.env`
3. Set up AWS credentials
4. Configure database connections

## Performance Testing

The project includes Locust for performance testing:
```bash
poetry run locust -f tests/performance/locustfile.py
```

## License

Proprietary - All rights reserved
