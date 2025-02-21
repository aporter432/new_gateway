"""Unit tests for validation utilities."""

from Protexis_Command.api_ogx import __version__


def test_version():
    """Test version is available."""
    assert isinstance(__version__, str)
    assert len(__version__.split(".")) == 3  # Should be semantic version
    assert __version__.startswith("0.1.")  # Should be in the 0.1.x series
