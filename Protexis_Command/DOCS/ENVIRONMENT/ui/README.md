# UI Development Environment

## Overview
This document details the UI development environment setup for the Smart Gateway project. The UI is built using Next.js 14 with TypeScript, providing a type-safe interface to the gateway's functionality.

## MVP Implementation
The current MVP implementation includes:

### 1. Authentication System (`/src/lib/api.ts`, `/src/app/page.tsx`, `/src/app/dashboard/page.tsx`)
- JWT-based authentication
- Protected routes with client-side validation
- Token management in localStorage
- Centralized API client for auth operations

#### Authentication Flow
1. **Login (`/src/app/page.tsx`)**
   - User submits credentials
   - Credentials sent to backend via Next.js API route
   - JWT token stored in localStorage
   - Redirect to dashboard on success

2. **Protected Dashboard (`/src/app/dashboard/page.tsx`)**
   - Checks for token in localStorage
   - Verifies token validity with backend
   - Redirects to login if token is invalid/missing
   - Displays user information if authenticated

3. **API Client (`/src/lib/api.ts`)**
   - Centralized authentication endpoints
   - Token validation
   - Error handling
   - Session management

### 2. Message Submission Form (`/src/components/forms/MessageForm.tsx`)
- Network type selection (OGx/IsatData Pro)
- Destination ID input
- JSON payload editor
- Real-time form validation
- Error handling and status display

### 3. API Integration (`/src/lib/api.ts`)
- Message submission endpoint
- Status checking endpoint
- Error handling
- Type-safe API calls

### 4. Type Definitions (`/src/types/api.ts`)
- Network type enumeration
- Message interfaces
- API request/response types

## Directory Structure
```
src/ui/
├── src/
│   ├── app/                    # Next.js app pages
│   │   ├── page.tsx           # Login page
│   │   ├── dashboard/         # Protected routes
│   │   │   └── page.tsx       # Dashboard page
│   │   └── api/               # API routes
│   │       └── auth/          # Auth endpoints
│   │           ├── login/     # Login handler
│   │           ├── logout/    # Logout handler
│   │           └── me/        # User info handler
│   ├── components/            # React components
│   │   └── forms/
│   │       └── MessageForm.tsx
│   ├── lib/                   # Utilities
│   │   └── api.ts            # API client (auth + messages)
│   └── types/                 # TypeScript definitions
│       └── api.ts            # API types
├── public/                    # Static assets
├── next.config.ts            # Next.js configuration
├── tsconfig.json             # TypeScript configuration
├── postcss.config.mjs        # PostCSS configuration
├── tailwind.config.ts        # Tailwind CSS configuration
├── eslint.config.mjs         # ESLint configuration
└── next-env.d.ts            # Next.js TypeScript declarations
```

## Docker Configuration

### Development Setup
The UI service uses a simple development-focused Dockerfile (`ui.Dockerfile`) that provides:
- Hot reloading for development
- Development dependencies included
- Health checks
- Proper port exposure

```dockerfile
# Key Dockerfile features
FROM node:18-alpine
WORKDIR /app
RUN apk add --no-cache curl
EXPOSE 3001
HEALTHCHECK CMD curl -f http://localhost:3001/health || exit 1
```

### Building and Running
```bash
# Build the UI container
docker-compose build ui

# Run with other services
docker-compose up -d

# View logs
docker-compose logs -f ui
```

### Volume Mounts
The development setup includes proper volume mounts for:
- Source code for hot reloading
- `node_modules` persistence
- Environment files

### Health Checks
The UI container includes health checks that:
- Run every 30 seconds
- Verify the application is responding
- Allow Docker to monitor container health

## Development Setup

### 1. Environment Variables

The UI service uses environment variables for configuration. These are managed through:
- `.env.local` for local development
- `.env.example` for documentation
- Docker environment variables for container deployment

#### Required Variables
```bash
# Core Settings (required)
NODE_ENV=development        # Application environment
UI_PORT=3001               # Port for the UI service
UI_HOST=0.0.0.0           # Host binding for the service

# API Configuration
NEXT_PUBLIC_API_URL=http://app:8000  # Backend API URL
NEXT_PUBLIC_WS_URL=ws://app:8000     # WebSocket URL (if needed)
```

#### Optional Variables
```bash
# Development Settings
UI_DEV_SERVER_PORT=3001    # Development server port
UI_METRICS_PORT=3002       # Metrics endpoint port
UI_LOG_LEVEL=debug        # Logging verbosity
UI_CORS_ORIGIN=http://localhost:3001  # CORS configuration

# Next.js Settings
NEXT_TELEMETRY_DISABLED=1  # Disable telemetry
```

#### Environment Files
- `.env.local`: Local development settings (not committed)
- `.env.example`: Template with documentation
- Docker environment variables take precedence in containers

### 2. Development Dependencies
The project uses the following key dependencies:
- Next.js 14
- React 18
- TypeScript 5
- Tailwind CSS 3
- ESLint with Next.js configuration
- PostCSS for Tailwind processing

### 3. Development Workflow
1. Start the services:
   ```bash
   docker-compose up -d
   ```

2. View logs:
   ```bash
   docker-compose logs -f ui
   ```

3. Access the UI:
   - Development: http://localhost:3001
   - API: http://localhost:8000

### 4. Making Changes
- Edit files in the `ui/` directory
- Changes hot-reload automatically
- Container automatically rebuilds when package.json changes

### 5. Configuration Files
The UI project requires several configuration files:

#### Core Configuration
- `next.config.ts` - Next.js configuration (build options, environment, etc.)
- `tsconfig.json` - TypeScript compiler settings and path aliases
- `next-env.d.ts` - Next.js TypeScript declarations (auto-generated)

#### Styling and Linting
- `postcss.config.mjs` - PostCSS configuration for Tailwind CSS
- `tailwind.config.ts` - Tailwind CSS customization
- `eslint.config.mjs` - ESLint rules and plugins

Each file serves a specific purpose:
```typescript
// next.config.ts
{
  reactStrictMode: true,    // Recommended for catching bugs
  swcMinify: true,         // Faster builds
  output: 'standalone'     // Optimized for Docker
}

// tsconfig.json
{
  compilerOptions: {
    strict: true,          // Type safety
    paths: {              // Import aliases
      "@/*": ["./src/*"]
    }
  }
}

// tailwind.config.ts
{
  content: [
    './src/**/*.{ts,tsx}' // Files to scan for classes
  ]
}
```

## Testing the MVP

### Manual Testing Steps
1. Start the application
2. Navigate to http://localhost:3001
3. Fill out the message form:
   - Select network type
   - Enter destination ID
   - Enter JSON payload
4. Submit the form
5. Verify success/error states

### Common Issues
1. **UI Not Loading**
   - Check if container is running: `docker-compose ps`
   - View logs: `docker-compose logs ui`
   - Verify API URL is correct

2. **Development Server Issues**
   - Clear node_modules: `docker-compose down && rm -rf ui/node_modules`
   - Rebuild: `docker-compose up -d --build ui`

## Next Steps
After MVP:
1. Add authentication
2. Enhance message builder with:
   - JSON schema validation
   - Template support
   - History tracking
3. Add real-time updates
4. Implement advanced monitoring

## Type Safety
Basic type definitions for MVP:
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

### Test Setup
The project uses the following testing tools:
- Jest for test running and assertions
- React Testing Library for component testing
- Jest DOM for DOM-related assertions
- User Event for simulating user interactions

### Running Tests
```bash
# Run all tests
npm test

# Run tests in watch mode
npm run test:watch

# Run tests with coverage
npm run test:coverage
```

### Test Structure
Tests are co-located with their components:
```
src/
├── components/
│   └── forms/
│       ├── MessageForm.tsx
│       └── MessageForm.test.tsx
└── ...
```

### Writing Tests
Example test structure:
```typescript
import { render, screen, fireEvent } from '@testing-library/react'
import { MessageForm } from './MessageForm'

describe('MessageForm', () => {
  it('validates required fields', () => {
    render(<MessageForm />)
    const submitButton = screen.getByRole('button', { name: /Submit/i })

    fireEvent.click(submitButton)
    expect(screen.getByLabelText(/Destination ID/i)).toBeInvalid()
  })
})
```

### Test Coverage
Coverage reports are generated in the `coverage/` directory and include:
- Statement coverage
- Branch coverage
- Function coverage
- Line coverage

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

## Authentication Implementation

### Overview
The authentication system uses JWT tokens with a centralized API client for all auth operations. The implementation follows these key principles:
- Token-based authentication using JWT
- Client-side route protection
- Secure token storage in localStorage
- Centralized error handling

### Key Components

#### 1. API Client (`/src/lib/api.ts`)
```typescript
// Authentication endpoints
export async function login(username: string, password: string) {
    const response = await fetch('/api/auth/login', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/x-www-form-urlencoded',
            'Accept': 'application/json',
        },
        body: `username=${encodeURIComponent(username)}&password=${encodeURIComponent(password)}&grant_type=password`,
        credentials: 'include',
    });
    // ... error handling
}

export async function checkAuth(token: string) {
    const response = await fetch('/api/auth/me', {
        method: 'GET',
        headers: {
            'Authorization': `Bearer ${token}`,
        },
        credentials: 'include',
    });
    // ... error handling
}
```

#### 2. Protected Routes
Protected routes (like Dashboard) implement client-side authentication checks:
```typescript
useEffect(() => {
    const token = localStorage.getItem('token');
    if (!token) {
        router.push('/');
        return;
    }

    const verifyAuth = async () => {
        try {
            const data = await checkAuth(token);
            setUserName(data.name);
        } catch (err) {
            router.push('/');
        }
    };

    verifyAuth();
}, [router]);
```

#### 3. Login Flow
The login page handles:
- Form submission
- Token storage
- Error display
- Redirection

```typescript
async function handleSubmit(e: React.FormEvent<HTMLFormElement>) {
    e.preventDefault();
    try {
        const data = await login(username, password);
        localStorage.setItem('token', data.access_token);
        router.push('/dashboard');
    } catch (err) {
        setError('Invalid username or password');
    }
}
```

### Security Considerations

1. **Token Storage**
   - JWT tokens stored in localStorage
   - Tokens include expiration time
   - Automatic logout on token expiration

2. **Route Protection**
   - Client-side authentication checks
   - Server-side validation through API routes
   - Automatic redirection for unauthenticated users

3. **API Security**
   - CSRF protection through credentials inclusion
   - Token validation on every request
   - Secure error handling

### Testing Authentication

#### Manual Testing
1. Start the application
2. Navigate to http://localhost:3001
3. Test login with:
   - Valid credentials
   - Invalid credentials
   - Expired token
4. Verify protected route access
5. Test logout functionality

#### Common Auth Issues
1. **Token Issues**
   - Clear localStorage
   - Check token expiration
   - Verify token format

2. **Route Protection**
   - Check authentication redirects
   - Verify token validation
   - Test error handling
