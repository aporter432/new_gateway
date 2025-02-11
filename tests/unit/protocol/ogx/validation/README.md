# OGx Protocol Validation Tests

This directory contains comprehensive unit tests for the OGx protocol validation components, ensuring robust message validation according to OGWS-1 specifications.

## Test Coverage

The validation test suite achieves 100% code coverage across all validation components, with thorough testing of edge cases, error conditions, and normal operation paths.

### Running Individual Test Suites

To run validation exception tests with coverage:
```bash
PYTHONPATH=src pytest tests/unit/protocol/ogx/validation/test_validation_exceptions.py -v --cov=protocols.ogx.validation.common.validation_exceptions --cov-branch --cov-report=term-missing
```

To run all validation tests with coverage:
```bash
poetry run pytest tests/unit/protocol/ogx/validation/test_{message,element,field,base,exception}_validation.py -v -s --log-cli-level=DEBUG --cov=src/protocols/ogx/validation --cov-report=term-missing
```

## Test Suite Components

### 1. Base Validation Tests (`test_base_validation.py`)
- Tests edge cases for `BaseValidator` implementation
- Covers field type validation, required field checks, and validation context handling
- Includes comprehensive testing of dynamic field type resolution

### 2. Element Validation Tests (`test_element_validation.py`)
- Validates element structure and content
- Tests array handling and nested element validation
- Covers error propagation and context preservation

### 3. Field Validation Tests (`test_field_validation.py`)
- Tests field type validation for all supported types
- Covers field value requirements and constraints
- Includes array and message field validation
- Tests dynamic field validation paths

### 4. Message Validation Tests (`test_message_validation.py`)
- Tests message structure validation
- Covers required message properties (Name, SIN, MIN)
- Tests field array validation
- Includes error handling for invalid message formats

### 5. Validation Exception Tests (`test_validation_exceptions.py`)
- Tests all validation exception classes:
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
- Covers exception inheritance, pickling support, and error code handling
- Tests string representation and error detail formatting

## Key Test Coverage Areas

1. **Error Handling**
   - Proper error message formatting
   - Error code assignment and inheritance
   - Exception chaining and cause tracking
   - Detailed error context preservation

2. **Validation Logic**
   - Field type validation for all supported types
   - Required field presence checks
   - Size limit validation
   - Message structure validation
   - Element array validation

3. **Edge Cases**
   - Empty/None values
   - Boundary conditions
   - Invalid type combinations
   - Malformed data structures

4. **Protocol Compliance**
   - OGWS-1 specification adherence
   - Message format requirements
   - Field type constraints
   - Error code standards

## Test Design Principles

1. **Comprehensive Coverage**
   - All code paths tested
   - Branch coverage for conditional logic
   - Exception handling paths verified

2. **Isolation**
   - Each test focuses on a specific functionality
   - Mock objects used where appropriate
   - Clear test case documentation

3. **Maintainability**
   - Organized test structure
   - Reusable fixtures
   - Clear test naming conventions

4. **Robustness**
   - Edge case handling
   - Error condition testing
   - Performance consideration

## Recent Coverage Analysis

The test suite currently achieves 100% code coverage with:
- 97 total statements
- 16 branches
- 0 missing statements
- 0 partial branches

All validation components are thoroughly tested, ensuring reliable message validation for the OGx protocol implementation. 