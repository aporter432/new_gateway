#!/bin/bash
# Script to rebuild and test the Gateway service

set -e  # Exit on any error

echo "===== STOPPING ALL CONTAINERS ====="
docker-compose down

echo "===== CLEANING DOCKER CACHE ====="
docker system prune -f

echo "===== BUILDING CONTAINERS (NO CACHE) ====="
docker-compose build --no-cache

echo "===== STARTING SERVICES ====="
docker-compose up -d

echo "===== WAITING FOR SERVICES TO BE HEALTHY ====="
sleep 15  # Give services time to start

echo "===== RUNNING AUTHENTICATION TESTS ====="
docker-compose run --rm ogx_gateway_tests poetry run pytest tests/integration/api/auth -v

echo "===== TEST COMPLETED ====="
