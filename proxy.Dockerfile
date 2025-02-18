# Use Nginx Alpine as base
ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Set environment variables for Nginx
ENV NGINX_HOST=0.0.0.0 \
    NGINX_PORT=8080

# Copy Nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

# Create log directory with proper permissions
RUN mkdir -p /var/log/nginx && \
    chown -R nginx:nginx /var/log/nginx

# Set working directory
WORKDIR /etc/nginx

# Healthcheck for Docker
HEALTHCHECK --interval=10s --timeout=5s --start-period=5s --retries=3 \
  CMD curl -f http://localhost:8080/health || exit 1

# Expose ports
EXPOSE 8080

# Set user for security
USER nginx

# Start Nginx
CMD ["nginx", "-g", "daemon off;"]

RUN mkdir -p /var/cache/nginx && \
    chown -R nginx:nginx /var/cache/nginx && \
    chmod -R 755 /var/cache/nginx
