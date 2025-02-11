"""Unit tests for validation utilities."""

from protocols.ogx.validation.utils import __version__


def test_version():
    """Test version is available."""
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3  # Should be semantic version
