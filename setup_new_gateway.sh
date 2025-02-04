#!/bin/bash

# Set project root
PROJECT_ROOT="/Users/aaronporter/Desktop/Projects/new_gateway"

# Ensure the project directory exists
mkdir -p "$PROJECT_ROOT"
cd "$PROJECT_ROOT" || exit

# Create Core Folders
mkdir -p src/{api,devices,protocols,message_queue,notifications,infrastructure,core,tests,ui}
mkdir -p src/api/routes
mkdir -p src/devices/{st6100,st9100}
mkdir -p src/protocols/{mtws,mtbp,ogx}
mkdir -p src/message_queue
mkdir -p src/notifications/channels
mkdir -p src/ui/{dashboard,assets,components,services,state,pages}

# Create Essential Files
touch src/api/main.py

touch src/core/{config.py,logging.py,security.py}
touch src/infrastructure/{database.py,redis.py,localstack.py}
touch src/main.py

echo "✅ Project structure created in $PROJECT_ROOT"

