"""
This file deliberately violates multiple project rules to test enforcement
"""

# Violation 1: Local constants instead of importing
MAX_SIZE = 1000
DEFAULT_TIMEOUT = 30
ERROR_CODES = {"INVALID": 400, "NOT_FOUND": 404}


# Violation 2: Standalone class without extension
class MessageHandler:
    """Handles messages without extending existing handlers"""

    def process(self, msg):
        if len(msg) > MAX_SIZE:
            return False
        return True


# Violation 3: Duplicate functionality that exists in OGxFieldValidator
class DataValidator:
    """Duplicates existing validation logic"""

    def validate_field(self, field_type, value):
        if not isinstance(value, (int, str)):
            raise ValueError(f"Invalid type for field {field_type}")
        return True


# Violation 4: Hardcoded values instead of using constants
class ConfigManager:
    """Uses hardcoded values instead of constants"""

    def __init__(self):
        self.max_retries = 3
        self.timeout = 30
        self.buffer_size = 1024


# Violation 5: Non-compliant method signatures
def validate_message(msg_data, strict=False):
    """Doesn't match existing validation patterns"""
    return isinstance(msg_data, dict)


# Violation 6: Missing docstrings and type hints
def process_data(data):
    if not data:
        return None
    return {"processed": data}
