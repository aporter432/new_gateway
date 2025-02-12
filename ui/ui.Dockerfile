# Development image for MVP
FROM node:18-alpine

WORKDIR /app

# Install dependencies needed for development
RUN apk add --no-cache curl

# Install dependencies when building the image
COPY package.json package-lock.json* ./
RUN npm install

# Copy the rest of the application
COPY . .

# Expose port
EXPOSE 3001

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=30s --retries=3 \
    CMD curl -f http://localhost:3001/health || exit 1

# Start development server
CMD ["npm", "run", "dev"] 