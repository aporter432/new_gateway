
# CI/CD Pipeline for new_gateway

This repository includes a complete CI/CD pipeline using GitHub Actions for `new_gateway`.

## 🏗️ CI/CD Stages
1. **Linting and Pre-Commit Checks:** Using `pre-commit` hooks (`black`, `flake8`, `isort`)
2. **Unit and Integration Tests:** With `pytest` and `alembic` migrations
3. **Docker Build and Push:** Builds and pushes images to DockerHub
4. **AWS Deployment (Placeholder):** AWS steps are marked as TODO until setup is complete

## 🚀 Quick Start

### 1. Set Up GitHub Secrets
Add the following secrets in GitHub:
- `DOCKER_USERNAME` and `DOCKER_PASSWORD` (for DockerHub)
- `JWT_SECRET_KEY` and `JWT_ALGORITHM` (for JWT security)
- AWS secrets (once AWS is ready)

### 2. Run Locally
```bash
docker-compose up --build
```

### 3. Deploy Manually to AWS (Once Configured)
```bash
bash aws-deploy.sh
```

### 4. View Test Coverage
```bash
poetry run pytest --cov=src --cov-report=term-missing
```

## 📂 File Overview
- `.github/workflows/cicd.yml` - CI/CD Pipeline
- `.env.example` - Environment Variable Example
- `.dockerignore` - Docker Ignore Rules
- `aws-deploy.sh` - AWS Deployment Script (Placeholder)
- `.github/secrets.example.md` - Secrets Guide

---

✨ **Created with guidance for simplicity and scalability.** ✨
