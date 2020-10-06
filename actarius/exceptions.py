"""Exceptions for actarius."""


class MockDatabricksInvalidConfigurationError(Exception):
    """A mock exception to gracefully handle when databricks_cli is not
    installed."""
