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

# Field Validation Tests

This directory contains unit tests for field validation according to OGWS-1.txt Section 5.1 Table 3.

## Test Organization

The tests are organized into focused files based on functionality:

### Basic Field Types (`test_field_validation_basic.py`)
- String fields
- Integer fields (signed/unsigned)
- Boolean fields
- Enum fields
- Data (base64) fields

### Array Fields (`test_field_validation_array.py`)
- No Value attribute allowed
- Optional Elements array
- Element structure validation
- Index validation (sequential, unique)
- Nested field validation

### Message Fields (`test_field_validation_message.py`)
- No Value attribute allowed
- Message attribute required
- Message content validation
- Required fields (SIN, MIN, Fields)
- Context requirements

### Dynamic Fields (`test_field_validation_dynamic.py`)
- TypeAttribute required
- TypeAttribute must be valid basic type
- Value must match TypeAttribute type
- Property fields (same rules as dynamic)

### Edge Cases (`test_field_validation_edge.py`)
- Required field validation
- Invalid field types
- Error propagation
- Null/empty values
- Complex error scenarios

## Common Test Fixtures

Each test file uses common fixtures:
- `field_validator`: Instance of `OGxFieldValidator`
- `validation_context`: Instance of `ValidationContext` with standard settings

## Test Coverage

The tests cover:
1. Valid cases for each field type
2. Invalid cases and error handling
3. Nested field validation
4. Error message format and content
5. Context requirements
6. Edge cases and complex scenarios

## Running Tests

Run all validation tests:
```bash
PYTHONPATH=. python -m pytest tests/unit/protocol/ogx/validation/ -v
```

Run specific test file:
```bash
PYTHONPATH=. python -m pytest tests/unit/protocol/ogx/validation/test_field_validation_basic.py -v
```

## Adding New Tests

When adding new tests:
1. Choose the appropriate file based on functionality
2. Follow the existing test structure
3. Include both valid and invalid cases
4. Verify error messages match OGWS-1.txt specifications
5. Add docstrings explaining test purpose

## Test Design Principles

1. **Single Responsibility**: Each test file focuses on one aspect of validation
2. **Comprehensive Coverage**: Test both valid and invalid cases
3. **Clear Organization**: Tests are grouped by functionality
4. **Maintainable**: Small, focused test files
5. **Well-Documented**: Clear docstrings and comments 