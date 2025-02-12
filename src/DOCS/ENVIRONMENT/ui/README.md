# UI Development Environment

## Overview
This document details the UI development environment setup and configuration for the Smart Gateway project. The UI is built using Next.js with TypeScript, providing a type-safe interface to the gateway's functionality.

## Prerequisites
- Node.js 18+ LTS
- npm 8+ or yarn
- Docker and Docker Compose (shared with backend)
- VS Code (recommended) with extensions:
  - ESLint
  - Prettier
  - TypeScript and JavaScript Language Features
  - Tailwind CSS IntelliSense

## Directory Structure
```
ui/
├── src/
│   ├── components/        # Reusable UI components
│   │   ├── common/       # Base components (buttons, inputs)
│   │   ├── forms/        # Form components
│   │   └── layout/       # Layout components
│   ├── app/              # Next.js app router pages
│   ├── types/            # TypeScript type definitions
│   ├── lib/              # Utilities and API clients
│   └── store/            # State management
├── public/               # Static assets
└── tests/                # UI tests
```

## Environment Setup

### Development Environment
1. **Initial Setup**
```bash
# Create UI directory
mkdir ui
cd ui

# Initialize Next.js project
npx create-next-app@latest . --typescript --tailwind --eslint

# Install dependencies
npm install
```

2. **Docker Configuration**
Add to existing docker-compose.yml:
```yaml
services:
  ui:
    build:
      context: ./ui
      dockerfile: ui.Dockerfile
    ports:
      - "3001:3001"
    volumes:
      - ./ui:/app
    environment:
      - NODE_ENV=development
      - NEXT_PUBLIC_API_URL=http://app:8000
    command: npm run dev
```

3. **Development Tools Setup**
```bash
# Install additional development dependencies
npm install -D @testing-library/react @testing-library/jest-dom jest
```

### Production Environment
Production builds require additional configuration:
```bash
# Build the application
npm run build

# Start production server
npm run start
```

## Type Safety
The UI maintains type safety with the backend through shared type definitions:

```typescript
// src/types/api.ts
export enum NetworkType {
  ISATDATA_PRO = 0,
  OGX = 1
}

export interface Message {
  id: string;
  network: NetworkType;
  payload: Record<string, unknown>;
  status: string;
}
```

## Current Implementation Scope
The current UI implementation focuses on core functionality:

1. **Message Submission**
   - Network type selection
   - Message payload construction
   - Submission status tracking

2. **Authentication**
   - Login form
   - Token management
   - Session handling

3. **Status Display**
   - Message status tracking
   - Error display
   - Response viewing

## Development Workflow

### Starting Development Environment
```bash
# Start all services including UI
docker-compose up -d

# View UI logs
docker-compose logs -f ui
```

### Making Changes
1. Components go in `src/components/`
2. Pages go in `src/app/`
3. Types go in `src/types/`
4. API calls go in `src/lib/`

### Testing Changes
```bash
# Run tests
npm run test

# Run type checking
npm run type-check
```

## Testing

### Unit Tests
```typescript
// Example test structure
import { render, screen } from '@testing-library/react';
import { MessageForm } from '@/components/forms/MessageForm';

describe('MessageForm', () => {
  it('validates network type selection', () => {
    render(<MessageForm />);
    // Test implementation
  });
});
```

### Integration Tests
Integration tests focus on component interaction and API communication.

## Troubleshooting

### Common Issues

1. **Type Errors**
   - Ensure types match backend definitions
   - Run `npm run type-check` to verify all types

2. **Build Errors**
   - Clear `.next` directory
   - Rebuild node_modules
   - Verify environment variables

3. **API Connection Issues**
   - Check API_URL environment variable
   - Verify backend is running
   - Check network settings in Docker

## Monitoring and Debugging

### Development Tools
- React Developer Tools
- Network tab in browser DevTools
- Next.js development overlay

### Production Monitoring
- Error tracking
- Performance monitoring
- User session tracking

## Security Considerations

1. **Authentication**
   - Token storage
   - Session management
   - CSRF protection

2. **API Communication**
   - HTTPS enforcement
   - Request validation
   - Error handling

## Future Enhancements

1. **Planned Features**
   - Advanced message composition
   - Real-time updates
   - Enhanced error handling

2. **Technical Improvements**
   - Performance optimization
   - Enhanced type safety
   - Expanded test coverage

## References
- [Next.js Documentation](https://nextjs.org/docs)
- [TypeScript Documentation](https://www.typescriptlang.org/docs)
- [Testing Library Documentation](https://testing-library.com/docs)

## Support
For development support:
- Review troubleshooting section
- Check component documentation
- Consult backend API documentation 