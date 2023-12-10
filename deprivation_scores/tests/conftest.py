import pytest

from rest_framework.test import APIClient

from django.core.management import call_command
from django.apps import apps


@pytest.mark.django_db
@pytest.fixture(scope="session")
def seed_data_fixture(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Don't repeat seed
        # LSOA = apps.get_model("deprivation_scores", "LSOA")
        ScottishIndexMultipleDeprivation = apps.get_model("deprivation_scores", "ScottishIndexMultipleDeprivation")
        # if not LSOA.objects.exists():
        call_command("seed", mode="add_organisational_areas")
        call_command("seed", mode="add_english_imds")
        call_command("seed", mode="add_welsh_imds")
        if not ScottishIndexMultipleDeprivation.objects.exists():
            call_command("seed", mode="add_scottish_imds")
        else:
            print("Test database already seeded. Skipping...")


@pytest.fixture(scope="function")
def api_client() -> APIClient:
    """
    Fixture to provide an API client
    :return: APIClient
    """
    yield APIClient()
