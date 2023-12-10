# python imports

# import django
from django.apps import apps

# third party libraries
import pytest
from django.core.management import call_command


@pytest.mark.django_db
@pytest.fixture(scope="session")
def seed_data_fixture(django_db_setup, django_db_blocker):
    with django_db_blocker.unblock():
        # Don't repeat seed
        LSOA = apps.get_model("deprivation_scores", "LSOA")
        if not LSOA.objects.exists():
            call_command("seed", mode="add_organisational_areas")
            call_command("seed", mode="add_english_imds")
            # call_command("seed", mode="add_welsh_imds")
            # call_command("seed", mode="add_scottish_imds")
        else:
            print("Test database already seeded. Skipping...")
