# Use Python 3.11-slim image as base
ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH="/app/src" \
    no_proxy=localhost,127.0.0.1,db,redis,localstack

# Install system dependencies
# Note: Added --no-install-recommends to minimize image size
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    libpq-dev \
    postgresql-client \
    dnsutils \
    iputils-ping \
    net-tools \
    && rm -rf /var/lib/apt/lists/* \
    && apt-get clean

# Install Poetry
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry

# Copy only dependency files first
COPY pyproject.toml poetry.lock ./
COPY README.md ./
COPY alembic.ini ./

# Install dependencies
RUN poetry install --no-root --no-interaction --no-ansi --with test

# Copy source code and tests
COPY src/ ./src/
COPY tests/ ./tests/

# Install the project
RUN poetry install --no-interaction --no-ansi --with test

# Create non-root user and set up logging directory
RUN useradd -m -u 1000 gateway \
    && mkdir -p /app/logs/auth /app/logs/api /app/logs/system \
    && chown -R gateway:gateway /app \
    && chmod -R 755 /app/logs
USER gateway

# Expose port
EXPOSE 8000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD wget -qO- http://localhost:8000/health || exit 1

# Default command
CMD ["poetry", "run", "uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--log-level", "debug"]
