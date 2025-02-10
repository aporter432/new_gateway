"""Element validation according to OGWS-1.txt Section 5.1."""

from typing import Any, Dict

from ...constants.message_format import REQUIRED_ELEMENT_PROPERTIES
from ..common.exceptions import ValidationError
from ..common.base_validator import BaseValidator
from ..common.types import ValidationContext, ValidationResult


class OGxElementValidator(BaseValidator):
    """Validates array elements according to OGWS-1.txt Section 5.1."""

    def validate(self, element: Dict[str, Any], context: ValidationContext) -> ValidationResult:
        """Validate an element's structure and content."""
        self.context = context
        self._errors = []

        try:
            # Validate required properties
            self._validate_required_fields(element, REQUIRED_ELEMENT_PROPERTIES, "element")

            # Validate Index is non-negative integer
            index = element.get("Index")
            if not isinstance(index, int) or index < 0:
                raise ValidationError("Element Index must be a non-negative integer")

            # Validate Fields is an array
            fields = element.get("Fields", [])
            if not isinstance(fields, list):
                raise ValidationError("Element Fields must be an array")

            return self._get_validation_result()

        except ValidationError as e:
            self._add_error(str(e))
            return self._get_validation_result()
