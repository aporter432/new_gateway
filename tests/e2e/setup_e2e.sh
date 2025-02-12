#!/bin/bash

# Create e2e test directory structure
mkdir -p tests/e2e/protocol/ogx/{message_flow,services,validation}
mkdir -p tests/e2e/api
mkdir -p tests/e2e/scenarios
mkdir -p tests/e2e/assets

# Create necessary __init__.py files
touch tests/e2e/__init__.py
touch tests/e2e/protocol/__init__.py
touch tests/e2e/protocol/ogx/__init__.py
touch tests/e2e/protocol/ogx/message_flow/__init__.py
touch tests/e2e/protocol/ogx/services/__init__.py
touch tests/e2e/protocol/ogx/validation/__init__.py
touch tests/e2e/api/__init__.py
touch tests/e2e/scenarios/__init__.py

# Create placeholder test files
touch tests/e2e/protocol/ogx/message_flow/test_re_flow.py
touch tests/e2e/protocol/ogx/message_flow/test_error_flow.py
touch tests/e2e/protocol/ogx/services/test_auth_service.py
touch tests/e2e/protocol/ogx/services/test_state_service.py
touch tests/e2e/protocol/ogx/validation/test_field_validation.py
touch tests/e2e/api/test_health.py
touch tests/e2e/scenarios/test_message_retry.py

# Copy environment example if not exists
if [ ! -f tests/e2e/.env.e2e ]; then
    cp tests/e2e/.env.e2e.example tests/e2e/.env.e2e
fi

echo "✅ E2E test environment setup complete" 