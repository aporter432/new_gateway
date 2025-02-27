"""Element validation according to OGx-1.txt.

According to the specification:
Elements are indexed structures with:
- Index: Element's index
- Fields: Element's fields

Elements exist as part of fields, where a field can contain either:
- A name/value pair OR
- An array of elements

Implementation Notes:
    While OGx-1.txt defines elements minimally, this validator implements
    consistent structural validation across the codebase. We validate:
    1. Basic array structure (must be a list)
    2. Required element properties (Index and Fields)
    3. Fields property must be an array

    These implementation details ensure consistent element handling while
    maintaining compliance with OGx-1.txt's basic requirements.
"""

from typing import Any, Dict, List, Optional

from ...constants.ogx_message_format import REQUIRED_ELEMENT_PROPERTIES
from ..ogx_validation_exceptions import ValidationError
from .ogx_base_validator import OGxBaseValidator
from .ogx_type_validator import ValidationContext, ValidationResult


class OGxElementValidator(OGxBaseValidator):
    """Validates elements according to OGx-1.txt.

    This validator ensures both specification compliance and consistent
    implementation structure across the codebase.
    """

    def validate(self, data: Any, context: Optional[ValidationContext]) -> ValidationResult:
        """Validate element data according to OGx-1.txt.

        This is the abstract method implementation required by OGxBaseValidator.
        For element validation, this delegates to validate_array if data is a list,
        or _validate_element if it's a single element.

        Args:
            data: Element or array of elements to validate
            context: Optional validation context. Basic structure validation
                    is still performed even without context.

        Returns:
            ValidationResult indicating if the data is valid
        """
        if isinstance(data, list):
            return self.validate_array(data, context)
        elif isinstance(data, dict):
            return self._validate_element(data)
        else:
            return ValidationResult(False, ["Invalid element data type"])

    def validate_array(
        self, elements: List[Dict[str, Any]], context: Optional[ValidationContext]
    ) -> ValidationResult:
        """Validate an array of elements.

        Validates that:
        1. Input is an array (implementation requirement)
        2. Each element has required structure
        3. Each element's Fields is an array (OGx-1.txt requirement)

        Args:
            elements: List of element dictionaries to validate
            context: Validation context

        Returns:
            ValidationResult indicating if all elements are valid
        """
        self.context = context
        self._errors = []

        # First validate that input is a list
        if not isinstance(elements, list):
            return ValidationResult(False, ["Elements must be an array"])

        # Then validate each element's structure
        for element in elements:
            if not isinstance(element, dict):
                return ValidationResult(False, ["Elements must be an array of dictionaries"])

            # Check required fields before any other validation
            missing_fields = [
                field for field in REQUIRED_ELEMENT_PROPERTIES if field not in element
            ]
            if missing_fields:
                return ValidationResult(
                    False, [f"Missing required element fields: {', '.join(missing_fields)}"]
                )

            try:
                # OGx-1.txt requirement: Fields must be an array
                fields = element.get("Fields")
                if not isinstance(fields, list):
                    raise ValidationError("Element Fields must be an array")

                # Validate each field in the element
                if self.context is not None:
                    from .ogx_field_validator import OGxFieldValidator

                    field_validator = OGxFieldValidator()
                    field_validator.context = self.context
                    for field in fields:
                        result = field_validator.validate(field, self.context)
                        if not result.is_valid:
                            self._errors.extend(f"In field: {error}" for error in result.errors)

            except ValidationError as e:
                self._add_error(str(e))

        return self._get_validation_result()

    def _validate_element(self, element: Dict[str, Any]) -> ValidationResult:
        """Validate an individual element.

        Validates that an element:
        1. Has the minimum required structure (Index and Fields)
        2. Has Fields as an array (as specified in OGx-1.txt)
        3. Each field in Fields array is valid

        Implementation Note:
            While OGx-1.txt only specifies elements as "indexed structures
            containing fields", we validate specific properties to ensure
            consistent implementation.

        Args:
            element: The element dictionary to validate

        Returns:
            ValidationResult indicating if the element is valid
        """
        self._errors = []

        try:
            # Implementation detail: Validate standard element structure
            self._validate_required_fields(element, REQUIRED_ELEMENT_PROPERTIES, "element")

            # OGx-1.txt requirement: Fields must be an array
            fields = element.get("Fields")
            if not isinstance(fields, list):
                raise ValidationError("Element Fields must be an array")

            # Validate each field in the element
            if self.context is not None:
                from .ogx_field_validator import OGxFieldValidator

                field_validator = OGxFieldValidator()
                field_validator.context = self.context  # Set context on field validator
                for field in fields:
                    result = field_validator.validate(field, self.context)
                    if not result.is_valid:
                        self._errors.extend(f"In field: {error}" for error in result.errors)

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
