# standard library imports

# Django imports
from django.db import migrations


from ..management.commands.seed import seed_all_imds_and_dependencies


def seed_imds_and_dependencies(apps, schema_editor):
    """
    Seed function which populates the Organisation table from JSON.
    This instead uses a list provided by RCPCH of all organisations in England
    and Wales that care for children - community paediatrics and hospital paediatrics.
    """
    seed_all_imds_and_dependencies()


class Migration(migrations.Migration):
    dependencies = [
        ("deprivation_scores", "0001_initial"),
    ]

    operations = [migrations.RunPython(seed_imds_and_dependencies)]
