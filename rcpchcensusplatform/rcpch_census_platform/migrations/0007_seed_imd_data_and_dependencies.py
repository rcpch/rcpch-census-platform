# standard library imports

# Django imports
from django.db import migrations


from ..management.commands.seed import seed_all_imds_and_dependencies


def seed_imds_and_dependencies(apps, schema_editor):
    """
    Seed function which populates the Organisation table from JSON.
    This instead uses a list provided by RCPCH E12 team of all organisations in England
    and Wales that care for children with Epilepsy - community paediatrics and hospital paediatrics
    in the same trust are counted as one organisation.
    """
    seed_all_imds_and_dependencies()


class Migration(migrations.Migration):
    dependencies = [
        ("rcpch_census_platform", "0006_seed_pdus"),
    ]

    operations = [migrations.RunPython(seed_imds_and_dependencies)]
