import pytest

from rest_framework.test import APIClient


@pytest.fixture
def api_client():
    """
    Fixture required to test views
    """
    return APIClient()
