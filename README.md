# SMART-GATEWAY

A comprehensive enterprise gateway implementation for managing ORBCOMM ISAT (MTWS/MTBP) and OGx protocols, with production-grade security, monitoring, and scalability features.

## Quick Start

```bash
# Clone the repository
git clone [repository-url]
cd new_gateway

# Copy environment configuration
cp .env.example .env

# Start the development environment
docker-compose up -d
```

Access the services:
- UI: http://localhost:3001
- API: http://localhost:8000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Project Overview

Smart Gateway provides a robust, production-ready interface for ORBCOMM's OGWS (OGx Gateway Web Service), featuring:

- **High Availability**: Containerized microservices architecture
- **Security**: Token-based authentication with automatic rotation
- **Scalability**: Redis-backed caching and DynamoDB support
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Compliance**: Full OGWS-1.txt specification compliance

## Architecture

The system consists of several key components:

- **Gateway API**: FastAPI-based REST interface
- **Message Worker**: Asynchronous message processing
- **State Management**: Redis/DynamoDB-backed state tracking
- **UI**: Next.js-based management interface
- **Monitoring**: Prometheus/Grafana metrics stack

## Documentation Structure

### Core Documentation
- [Environment Setup](src/DOCS/ENVIRONMENT/README.md)
  - Development environment configuration
  - Production deployment guidelines
  - Testing environment setup
  - Infrastructure requirements

- [UI Development](src/DOCS/ENVIRONMENT/ui/README.md)
  - Frontend architecture
  - Development workflow
  - Component documentation
  - Testing guidelines

### Protocol Documentation
- [OGx Protocol](src/protocols/ogx/README.md)
  - Message format specifications
  - Validation rules
  - Transport configuration
  - Error handling

### Testing Documentation
- [Integration Tests](tests/integration/README.md)
- [End-to-End Tests](tests/e2e/README.md)
- [Unit Tests](tests/unit/README.md)

### Additional Resources
- [Contributing Guidelines](CONTRIBUTING.md)
- [Changelog](CHANGELOG.md)
- [License](LICENSE)

## Support

For issues and support:
- GitHub Issues: [Issues Link]
- Documentation: [Docs Link]
- Emergency Contact: [Contact Info]
