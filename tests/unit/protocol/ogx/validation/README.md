# OGx Protocol Validation Tests

This directory contains comprehensive unit tests for the OGx protocol validation components, ensuring robust message validation according to OGx-1 specifications.

## Test Coverage

The validation test suite achieves 97% code coverage across all validation components, with thorough testing of edge cases, error conditions, and normal operation paths.

### Current Coverage Analysis

Component-wise coverage:
- `field_validator.py`: 94% coverage (168 statements, 88 branches)
- `message_validator.py`: 98% coverage (37 statements, 14 branches)
- `network_validator.py`: 96% coverage (35 statements, 18 branches)
- `size_validator.py`: 93% coverage (30 statements, 12 branches)
- `transport_validator.py`: 100% coverage (42 statements, 24 branches)
- Base components and utilities: 100% coverage

### Running Tests

To run all validation tests with coverage:
```bash
PYTHONPATH=. python -m pytest tests/unit/protocol/ogx/validation/ -v --cov=src/protocols/ogx/validation --cov-report=term-missing
```

To run specific test files:
```bash
PYTHONPATH=. python -m pytest tests/unit/protocol/ogx/validation/test_field_validation_basic.py -v
```

## Test Suite Components

### 1. Basic Field Validation (`test_field_validation_basic.py`)
- String fields
- Integer fields (signed/unsigned)
- Boolean fields
- Enum fields
- Data (base64) fields

### 2. Array Field Validation (`test_field_validation_array.py`)
- No Value attribute allowed
- Optional Elements array
- Element structure validation
- Index validation (sequential, unique)
- Nested field validation

### 3. Message Field Validation (`test_field_validation_message.py`)
- No Value attribute allowed
- Message attribute required
- Message content validation
- Required fields (SIN, MIN, Fields)
- Context requirements

### 4. Dynamic Field Validation (`test_field_validation_dynamic.py`)
- TypeAttribute required
- TypeAttribute must be valid basic type
- Value must match TypeAttribute type
- Property fields (same rules as dynamic)

### 5. Edge Cases (`test_field_validation_edge.py`)
- Required field validation
- Invalid field types
- Error propagation
- Null/empty values
- Complex error scenarios

### 6. Protocol Validation (`test_protocol_validation.py`)
- Network type validation
- Transport type validation
- Size limit validation
- Error handling

### 7. Exception Handling (`test_validation_exceptions.py`)
Tests all validation exception classes:
- `OGxProtocolError`
- `ProtocolError`
- `ValidationError`
- `MessageValidationError`
- `ElementValidationError`
- `FieldValidationError`
- `MessageFilterValidationError`
- `SizeValidationError`
- `AuthenticationError`
- `EncodingError`
- `RateLimitError`

## Key Test Coverage Areas

1. **Field Validation**
   - All field types from OGx-1.txt Table 3
   - Type-specific validation rules
   - Error handling for each type
   - Nested field structures

2. **Message Validation**
   - Structure validation
   - Required fields
   - Field array validation
   - Context handling

3. **Protocol Compliance**
   - Network type validation
   - Transport validation
   - Size limits
   - Error codes per OGx-1.txt

4. **Error Handling**
   - Exception hierarchy
   - Error message formatting
   - Error code assignment
   - Error propagation

## Test Design Principles

1. **Comprehensive Coverage**
   - Core functionality tested
   - Edge cases covered
   - Error paths verified
   - Branch coverage optimized

2. **Isolation**
   - Independent test cases
   - Clear test boundaries
   - Minimal dependencies
   - Mock objects where needed

3. **Maintainability**
   - Organized structure
   - Clear naming
   - Shared fixtures
   - Documented purpose

4. **Performance**
   - Fast execution
   - Resource efficient
   - No unnecessary repetition
   - Focused test scope

## Remaining Coverage Gaps

Minor coverage gaps exist in error handling paths:

1. `field_validator.py` (94%):
   - Some error condition branches
   - Dynamic field edge cases
   - Complex error propagation paths

2. `message_validator.py` (98%):
   - One branch condition in error handling

3. `network_validator.py` (96%):
   - One error path

4. `size_validator.py` (93%):
   - Error handling paths

These gaps represent defensive error handling code that is difficult to trigger in normal testing conditions.
