import pytest
import os
from unittest.mock import patch
from tests.postcode_mock_data import get_mock_postcode_response


@pytest.fixture(scope="session")
def django_db_setup():
    """
    Override the default django_db_setup fixture to use the existing database
    instead of creating a fresh test database. This allows integration tests
    to run against the seeded development database.
    """
    # Don't create a new database - use the existing one
    pass


class MockResponse:
    """Mock requests.Response object."""

    def __init__(self, json_data, status_code):
        self.json_data = json_data
        self.status_code = status_code

    def json(self):
        return self.json_data

    def raise_for_status(self):
        if self.status_code >= 400:
            from requests.exceptions import HTTPError

            raise HTTPError(f"HTTP Error: {self.status_code}")


def mock_requests_get(url, **kwargs):
    """
    Mock implementation of requests.get for postcodes.io API.
    Extracts postcode from URL and returns mock data.
    """
    # Extract postcode from URL
    # URL format: https://api.postcodes.io/postcodes/{postcode}
    # or: https://api.postcodes.io/terminated_postcodes/{postcode}
    if "/postcodes/" in url:
        postcode = url.split("/postcodes/")[-1]
    elif "/terminated_postcodes/" in url:
        postcode = url.split("/terminated_postcodes/")[-1]
    else:
        return MockResponse(None, 404)

    # Get mock response
    mock_data = get_mock_postcode_response(postcode)

    if mock_data is None:
        return MockResponse({"status": 404, "error": "Postcode not found"}, 404)

    return MockResponse(mock_data, 200)


@pytest.fixture(autouse=True)
def mock_postcodes_io(request):
    """
    Mock postcodes.io API calls in tests.

    By default, mocking is DISABLED to allow integration tests to hit the real API.

    To enable mocking:
    - Set environment variable MOCK_POSTCODES_IO=1
    - Or use the @pytest.mark.mock_postcodes_io marker on individual tests

    This allows CI to run tests against the real postcodes.io API while
    local development can optionally use mocks for faster iteration.
    """
    # Default: use mocked postcodes.io responses for all tests.
    # To opt out and hit the real API set the env var `REAL_POSTCODES_IO=1`
    # or use the pytest marker `@pytest.mark.real_postcodes_io` on a test.
    real_enabled = os.environ.get("REAL_POSTCODES_IO", "").lower() in (
        "1",
        "true",
        "yes",
    )
    has_real_marker = request.node.get_closest_marker("real_postcodes_io") is not None

    if not (real_enabled or has_real_marker):
        # Patch requests.get in the postcode helper so tests use mock data
        with patch(
            "deprivation_scores.general_functions.postcode.requests.get",
            side_effect=mock_requests_get,
        ):
            yield
    else:
        # Opted out: use real postcodes.io API
        yield


@pytest.fixture
def api_client():
    """Return a DRF API client for testing."""
    from rest_framework.test import APIClient

    return APIClient()
