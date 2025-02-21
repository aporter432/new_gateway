# Smart Gateway UI

Next.js-based user interface for the Smart Gateway project, providing a modern and type-safe interface for managing ORBCOMM ISAT and OGx protocols.

## Development Setup

### Required Services

The UI requires several core services to function properly. Start them with:

```bash
# Start core services (required)
docker-compose up -d ui app proxy redis db localstack

# Core Services and Their Purposes:
# - ui:        Next.js frontend (port 3001)
# - app:       FastAPI backend API (port 8000)
# - proxy:     OGx proxy for protocol communication (port 8080)
# - redis:     Message state and caching
# - db:        PostgreSQL for customer data
# - localstack: AWS service emulation for development
```

### Optional Monitoring Services

For development monitoring (optional), start these additional services:

```bash
# Start monitoring services (optional)
docker-compose up -d prometheus grafana

# Monitoring Services:
# - prometheus: Metrics collection (port 9090)
# - grafana:    Metrics visualization (port 3000)
```

### Verifying Services

Check that required services are running and healthy:

```bash
# Check service status
docker-compose ps

# View service logs
docker-compose logs -f ui    # UI logs only
docker-compose logs -f       # All logs
```

All services should show as "healthy" in their status.

### Health Check Endpoints

- UI: http://localhost:3001/health
- API: http://localhost:8000/health
- Proxy: http://localhost:8080/health

## Local Development

If you need to run the UI outside of Docker (not recommended):

```bash
# Install dependencies
npm install

# Start development server
npm run dev
```

The UI will be available at [http://localhost:3001](http://localhost:3001)

## Features

- Message submission form with network type selection
- Real-time validation and error handling
- Type-safe API integration
- Modern UI with Tailwind CSS
- Full TypeScript support

## Project Structure

```
src/
├── app/              # Next.js app router pages
├── components/       # React components
├── lib/             # Utilities and API client
└── types/           # TypeScript definitions
```

## Configuration

Environment variables are managed through:
- `.env.local` for local development
- `.env.example` for documentation
- Docker environment variables for container deployment

See the [UI Development Documentation](../DOCS/ENVIRONMENT/ui/README.md) for detailed setup instructions.

## Testing

```bash
# Run tests
npm test

# Run tests with coverage
npm run test:coverage

# Type checking
npm run type-check
```

## Troubleshooting

### Common Issues

1. **UI Container Unhealthy**
   - Check UI logs: `docker-compose logs ui`
   - Verify health endpoint: `curl http://localhost:3001/health`
   - Ensure all required services are running

2. **API Connection Failed**
   - Verify app container is healthy: `docker-compose ps app`
   - Check API health: `curl http://localhost:8000/health`
   - Review app container logs: `docker-compose logs app`

3. **Development Server Issues**
   - Clear node_modules: `docker-compose down && rm -rf ui/node_modules`
   - Rebuild: `docker-compose up -d --build ui`
   - Check for port conflicts on 3001

## Additional Documentation

For detailed documentation on:
- Environment setup
- Docker configuration
- API integration
- Testing guidelines

See the [UI Development Environment](../DOCS/ENVIRONMENT/ui/README.md) documentation.
