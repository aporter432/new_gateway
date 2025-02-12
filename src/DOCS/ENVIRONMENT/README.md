# Environment Documentation

## Overview
This directory contains comprehensive documentation for all environment configurations in the Smart Gateway project.

## Directory Structure
- `/development` - Development environment setup and configuration
- `/production` - Production deployment and security guidelines
- `/testing` - Test environment setup and management

## Environment Files
### Core Files (Project Root)
- `.env` - Active development environment configuration
- `.env.example` - Template with safe default values
- `docker-compose.yml` - Container orchestration configuration
- `nginx.conf` - OGWS proxy configuration

### Environment-Specific Documentation
Each environment type has its own dedicated documentation:

1. **Development Environment**
   - Local setup procedures
   - Docker development configuration
   - Debug and testing settings

2. **Production Environment**
   - Deployment procedures
   - Security requirements
   - Scaling considerations
   - Monitoring setup

3. **Testing Environment**
   - Test configuration
   - Mock services setup
   - Integration test environment
   - End-to-end test setup

## Environment Variables
See each environment's README for specific variable requirements and configurations.

## Security Notes
- Never commit sensitive credentials to version control
- Use `.env.example` for documentation, not actual values
- Production credentials should be managed via secure key stores
- Test credentials should be isolated from production 