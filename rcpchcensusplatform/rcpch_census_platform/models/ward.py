from django.contrib.gis.db import models

from .output_areas import MSOA


class Ward(models.Model):
    ward_code = models.CharField(
        "Ward Code", max_length=50, help_text="Ward code", unique=True
    )
    ward_name = models.CharField("Ward name", max_length=50, help_text="Ward name")
    year = models.IntegerField("Ward year")

    msoa = models.ForeignKey(MSOA, on_delete=models.CASCADE)
