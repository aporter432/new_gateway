# Smart Gateway UI

Next.js-based user interface for the Smart Gateway project, providing a modern and type-safe interface for managing ORBCOMM ISAT and OGx protocols.

## Development Setup

### Using Docker (Recommended)

The UI is designed to run as part of the Smart Gateway Docker environment:

```bash
# From the root directory
docker-compose up -d ui
```

Access the UI at [http://localhost:3001](http://localhost:3001)

### Local Development

If you need to run the UI outside of Docker:

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

## Additional Documentation

For detailed documentation on:
- Environment setup
- Docker configuration
- API integration
- Testing guidelines

See the [UI Development Environment](../DOCS/ENVIRONMENT/ui/README.md) documentation.
