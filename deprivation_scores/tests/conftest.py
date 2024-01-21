import pytest

from rest_framework.test import APIClient

from django.core.management import call_command
from django.apps import apps


@pytest.mark.django_db
@pytest.fixture(scope="session")
def seed_data_fixture(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Don't repeat seed
        LSOA = apps.get_model("deprivation_scores", "LSOA")
        ScottishIndexMultipleDeprivation = apps.get_model(
            "deprivation_scores", "ScottishIndexMultipleDeprivation"
        )
        EnglishIndexMultipleDeprivation = apps.get_model(
            "deprivation_scores", "EnglishIndexMultipleDeprivation"
        )
        WelshIndexMultipleDeprivation = apps.get_model(
            "deprivation_scores", "WelshIndexMultipleDeprivation"
        )
        NorthernIrelandIndexMultipleDeprivation = apps.get_model(
            "deprivation_scores", "NorthernIrelandIndexMultipleDeprivation"
        )
        if not LSOA.objects.exists():
            call_command("seed", mode="add_organisational_areas")
        if not EnglishIndexMultipleDeprivation.objects.exists():
            call_command("seed", mode="add_english_imds")
        if not WelshIndexMultipleDeprivation.objects.exists():
            call_command("seed", mode="add_welsh_imds")
        if not ScottishIndexMultipleDeprivation.objects.exists():
            call_command("seed", mode="add_scottish_imds")
        if not NorthernIrelandIndexMultipleDeprivation.objects.exists():
            call_command("seed", mode="add_northern_ireland_imds")


@pytest.fixture(scope="function")
def api_client() -> APIClient:
    """
    Fixture to provide an API client
    :return: APIClient
    """
    yield APIClient()
