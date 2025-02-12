#!/bin/bash

# Set project root
PROJECT_ROOT="/Users/aaronporter/Desktop/Projects/new_gateway"

# Ensure the project directory exists
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit

# Create Core Folders
mkdir -p src/{api,devices,protocols,message_queue,notifications,infrastructure,core,tests,ui}
mkdir -p src/api/{routes,middleware,models}
mkdir -p src/devices/{st6100,st9100,common}
mkdir -p src/protocols/{mtws,mtbp,ogx}/{services,validation,models,constants}
mkdir -p src/protocols/ogx/validation/{common,format,message}
mkdir -p src/message_queue/{handlers,models}
mkdir -p src/notifications/channels
mkdir -p src/infrastructure/{redis,dynamodb,aws}
mkdir -p src/core/{logging,security,config}
mkdir -p src/ui/{dashboard,assets,components,services,state,pages}

# Create Test Structure
mkdir -p tests/{unit,integration,performance}/protocol/ogx
mkdir -p tests/integration/api/auth

# Create Development Directories
mkdir -p logs/{protocol,system,auth,api,metrics}  # Development logs
mkdir -p .vscode  # IDE settings

# Create Essential Files
touch src/api/main.py
touch src/core/{config.py,logging.py,security.py}
touch src/infrastructure/{database.py,redis.py,localstack.py}
touch src/main.py

# Create Development Config Files
touch .env.example
touch .pre-commit-config.yaml
touch .flake8
touch pyproject.toml
touch README.md

echo "✅ Project structure created in $PROJECT_ROOT"

