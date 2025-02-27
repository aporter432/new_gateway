# Consolidated UI Dockerfile for both development and production
# Supports:
# - Development with hot reloading
# - Production with optimized builds
# - TypeScript and Next.js configuration
# - Security best practices
# - Health monitoring

# Build argument for platform support
ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} node:18-alpine

# Set working directory
WORKDIR /app

# Install system dependencies
RUN apk add --no-cache curl

# Create necessary directories with proper permissions
RUN mkdir -p /app/.next /app/node_modules /app/.cache /app/src /app/public && \
    chown -R node:node /app

# Switch to non-root user for security
USER node

# Copy package files with correct ownership
COPY --chown=node:node package*.json ./

# Install dependencies
RUN npm install

# Install TypeScript and required types
RUN npm install --save-dev typescript @types/react @types/node @types/react-dom

# Copy configuration files with correct ownership
COPY --chown=node:node tsconfig.json next.config.js ./

# Copy the rest of the application with correct ownership
COPY --chown=node:node . .

# Setup script for TypeScript and Next.js environment
RUN echo '#!/bin/sh' > /app/setup.sh && \
    echo 'cd /app' >> /app/setup.sh && \
    echo 'rm -f /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'find /app/.next -mindepth 1 -delete 2>/dev/null || true' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next\" />" > /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next/image-types/global\" />" >> /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next/navigation-types/navigation\" />" >> /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'chmod 644 /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'npx next telemetry disable' >> /app/setup.sh && \
    echo 'if [ "$NODE_ENV" = "production" ]; then' >> /app/setup.sh && \
    echo '  npm run build' >> /app/setup.sh && \
    echo '  exec npm start' >> /app/setup.sh && \
    echo 'else' >> /app/setup.sh && \
    echo '  exec npm run dev' >> /app/setup.sh && \
    echo 'fi' >> /app/setup.sh && \
    chmod +x /app/setup.sh

# Expose port
EXPOSE 8081

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:8081/health || exit 1

# Environment variables
ENV PORT=8081
ENV HOST=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

# Use setup script as entrypoint
ENTRYPOINT ["/app/setup.sh"]
