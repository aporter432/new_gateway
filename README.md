# SMART-GATEWAY

A comprehensive enterprise gateway implementation for managing ORBCOMM ISAT (MTWS/MTBP) and OGx protocols, with production-grade security, monitoring, and scalability features.

## Quick Start

```bash
# Clone the repository
git clone [repository-url]
cd new_gateway

# Copy environment configuration
cp .env.example .env
cp src/ui/.env.example src/ui/.env.local

# Start the development environment
docker-compose up -d
```

Access the services:
- UI: http://localhost:3001
- API: http://localhost:8000
- Grafana: http://localhost:3000
- Prometheus: http://localhost:9090

## Project Overview

Smart Gateway provides a robust, production-ready interface for ORBCOMM's OGx (OGx Gateway Web Service), featuring:

- **High Availability**: Containerized microservices architecture
- **Security**: Token-based authentication with automatic rotation
- **Scalability**: Redis-backed caching and DynamoDB support
- **Monitoring**: Prometheus metrics and Grafana dashboards
- **Compliance**: Full OGx-1.txt specification compliance

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

## Development Environment

### Prerequisites
- Docker and Docker Compose
- Python 3.11.6+
- Node.js 18+
- Poetry 1.7.1+

### Key Services
- **UI (Next.js)**: Modern web interface for message management
- **API (FastAPI)**: RESTful API for message handling
- **Redis**: Message state and caching
- **PostgreSQL**: Customer data storage
- **LocalStack**: AWS service emulation
- **Prometheus/Grafana**: Monitoring and metrics

### Health Checks
All services include health checks accessible at their respective `/health` endpoints:
- UI: http://localhost:3001/health
- API: http://localhost:8000/health
- Proxy: http://localhost:8080/health


## Support

For issues and support:
- Create an issue in the repository
- Check the documentation in `src/DOCS`
- Contact the development team
