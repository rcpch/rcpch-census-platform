import pytest


@pytest.fixture(scope="session")
def django_db_setup():
    """
    Override the default django_db_setup fixture to use the existing database
    instead of creating a fresh test database. This allows integration tests
    to run against the seeded development database.
    """
    # Don't create a new database - use the existing one
    pass


@pytest.fixture
def api_client():
    """Return a DRF API client for testing."""
    from rest_framework.test import APIClient

    return APIClient()
