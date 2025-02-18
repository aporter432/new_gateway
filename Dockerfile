# Use Python 3.11-slim image as base
ARG TARGETPLATFORM=linux/arm64
FROM --platform=${TARGETPLATFORM} python:3.11-slim

# Set working directory
WORKDIR /app

# Set environment variables for Poetry 2.0.0
ENV PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    POETRY_VERSION=2.0.0 \
    POETRY_HOME="/opt/poetry" \
    POETRY_VIRTUALENVS_CREATE=true \
    POETRY_VIRTUALENVS_IN_PROJECT=true \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH="/app/src:/app/common" \
    no_proxy=localhost,127.0.0.1,db,redis,localstack

# Install system dependencies
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
    build-essential \
    curl \
    wget \
    libpq-dev \
    git \
    && rm -rf /var/lib/apt/lists/*

# Install Poetry 2.0.0
RUN curl -sSL https://install.python-poetry.org | python3 - \
    && cd /usr/local/bin \
    && ln -s /opt/poetry/bin/poetry

# Copy poetry files first for better caching
COPY pyproject.toml poetry.lock ./
COPY README.md alembic.ini ./

# ✅ Initialize Git and pull submodules (to get `common`)
COPY .git .git
COPY .gitmodules .gitmodules
RUN git submodule update --init --recursive

# ✅ Copy submodule directly into container for Poetry
COPY common/ ./common/

# Install dependencies from local submodule
RUN poetry lock

RUN poetry install --no-root
# Copy the source code
COPY src/ ./src/
COPY tests/ ./tests/

# Install the project (with submodule)
RUN poetry install

# Create non-root user and setup logging directories
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
