# Authentication System Components

This document outlines the components and flow of the authentication system in the gateway application.

## Core Components and Locations

### API Routes and Endpoints
- **Location**: `src/api/routes/auth/user.py`
- **Key Endpoints**:
  - `/auth/register`: New user registration
  - `/auth/login`: User authentication and token generation

### Data Models and Schemas
- **Database Models**
  - **Location**: `src/infrastructure/database/models/user.py`
  - **Components**:
    - `User`: SQLAlchemy model for user data
    - `UserRole`: Enum for user roles (USER/ADMIN)

- **API Schemas**
  - **Location**: `src/api/schemas/user.py`
  - **Components**:
    - `UserBase`: Base user attributes
    - `UserCreate`: Registration request validation
    - `UserResponse`: API response formatting
    - `UserInDB`: Internal database representation
    - `Token`: JWT token response structure

### Security Components
- **Password Handling**
  - **Location**: `src/api/security/password.py`
  - **Functions**:
    - `get_password_hash()`: Password hashing
    - `verify_password()`: Password verification
    - `validate_password()`: Password strength validation

- **JWT Token Management**
  - **Location**: `src/api/security/jwt.py`
  - **Functions**:
    - `create_access_token()`: JWT token generation
    - `verify_token()`: Token validation and verification

- **OAuth2 Implementation**
  - **Location**: `src/api/security/oauth2.py`
  - **Components**:
    - `oauth2_scheme`: OAuth2 password flow configuration
    - `get_current_user()`: Current user extraction
    - `get_current_active_user()`: Active user validation
    - `get_current_admin_user()`: Admin role validation

### Database Layer
- **Repository**
  - **Location**: `src/infrastructure/database/repositories/user_repository.py`
  - **Operations**:
    - User creation
    - User retrieval by email/ID
    - User updates
    - User deletion

- **Database Dependencies**
  - **Location**: `src/infrastructure/database/dependencies.py`
  - **Components**:
    - Database session management
    - Connection pooling
    - Transaction handling

### Middleware
- **Auth Middleware**
  - **Location**: `src/api/middleware/OGx_auth.py`
  - **Features**:
    - Token refresh handling
    - Request retry logic
    - Error handling
    - Authentication failure recovery

## Authentication Flow

1. **User Registration**:
   ```
   Client → /auth/register
   ↓
   UserCreate Schema Validation
   ↓
   Password Hashing
   ↓
   User Repository (Create)
   ↓
   UserResponse
   ```

2. **User Login**:
   ```
   Client → /auth/login
   ↓
   OAuth2 Password Flow
   ↓
   User Repository (Lookup)
   ↓
   Password Verification
   ↓
   JWT Token Generation
   ↓
   Token Response
   ```

3. **Protected Route Access**:
   ```
   Client → Protected Endpoint
   ↓
   Auth Middleware
   ↓
   JWT Verification
   ↓
   User Lookup
   ↓
   Role Validation
   ↓
   Route Handler
   ```

## Future RBAC Considerations

The authentication system is designed to support future Role-Based Access Control (RBAC) enhancements:

- Role hierarchy implementation
- Permission-based access control
- Custom authorization rules
- Department/team-based access
- Administrative interfaces
- Audit logging

## Security Features

- Secure password hashing (bcrypt)
- JWT token-based authentication
- OAuth2 password flow
- Role-based authorization
- Active user validation
- Automatic token refresh
- Secure error handling
- Request retry mechanism

## Related Documentation

- JWT Implementation: `src/api/security/jwt.py`
- Password Security: `src/api/security/password.py`
- Database Schema: `src/infrastructure/database/models/user.py`
- API Documentation: Generated OpenAPI schema
