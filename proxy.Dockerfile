ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} nginx:alpine

# Install curl for health checks
RUN apk add --no-cache curl

# Copy nginx configuration
COPY nginx.conf /etc/nginx/nginx.conf

EXPOSE 8080

# Use the default nginx command
CMD ["nginx", "-g", "daemon off;"]
