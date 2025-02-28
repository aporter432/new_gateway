"""Unit tests for token validation utilities."""

import pytest

from Protexis_Command.api.common.auth.token_utils import verify_token_format


@pytest.mark.parametrize(
    "token,expected",
    [
        # Valid JWT format cases
        ("header.payload.signature", True),
        (
            "eyJhbGciOiJIUzI1NiJ9.eyJzdWIiOiIxMjM0NTY3ODkwIn0.dozjgNryP4J3jVmNHl0w5N_XgL0n3I9PlFUP0THsR8U",
            True,
        ),
        ("abc.def.ghi", True),
        ("A-Z_a-z0-9.A-Z_a-z0-9.A-Z_a-z0-9", True),
        # Invalid JWT format cases
        ("", False),
        ("header", False),
        ("header.payload", False),
        ("header.payload.signature.extra", False),
        ("header..signature", False),
        (".payload.signature", False),
        ("header.payload.", False),
        ("!@#.payload.signature", False),
        ("header.$%^.signature", False),
        ("header.payload.@#$", False),
        ("header payload signature", False),
        ("header/payload/signature", False),
    ],
)
def test_verify_token_format(token: str, expected: bool):
    """Test token format verification with various test cases.

    Args:
        token: Input token string to verify
        expected: Expected verification result
    """
    assert verify_token_format(token) == expected


def test_verify_token_format_none():
    """Test token format verification with None input."""
    with pytest.raises(TypeError, match="expected string or bytes-like object"):
        verify_token_format(None)  # type: ignore


def test_verify_token_format_non_string():
    """Test token format verification with non-string input."""
    with pytest.raises(TypeError, match="expected string or bytes-like object"):
        verify_token_format(123)  # type: ignore
