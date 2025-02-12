# Development image for Next.js
ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} node:18-alpine

WORKDIR /app

# Install dependencies needed for development
RUN apk add --no-cache curl

# Create necessary directories and set permissions
RUN mkdir -p /app/.next /app/node_modules /app/.cache /app/src /app/public && \
    chown -R node:node /app

# Switch to non-root user
USER node

# Copy package files with correct ownership
COPY --chown=node:node package*.json ./

# Install dependencies
RUN npm install

# Install TypeScript and types
RUN npm install --save-dev typescript @types/react @types/node @types/react-dom

# Copy config files with correct ownership
COPY --chown=node:node tsconfig.json ./
COPY --chown=node:node next.config.js ./

# Copy the rest of the application with correct ownership
COPY --chown=node:node . .

# Create TypeScript setup script
RUN echo '#!/bin/sh' > /app/setup.sh && \
    echo 'cd /app' >> /app/setup.sh && \
    echo 'rm -f /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'find /app/.next -mindepth 1 -delete 2>/dev/null || true' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next\" />" > /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next/image-types/global\" />" >> /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'echo "/// <reference types=\"next/navigation-types/navigation\" />" >> /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'chmod 644 /app/next-env.d.ts' >> /app/setup.sh && \
    echo 'npx next telemetry disable' >> /app/setup.sh && \
    echo 'exec "$@"' >> /app/setup.sh && \
    chmod +x /app/setup.sh

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Start development server
ENV PORT=3001
ENV HOST=0.0.0.0
ENV NEXT_TELEMETRY_DISABLED=1

ENTRYPOINT ["/app/setup.sh"]
CMD ["npm", "run", "dev"] 