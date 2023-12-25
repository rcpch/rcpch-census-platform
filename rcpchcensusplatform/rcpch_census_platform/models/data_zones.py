from django.contrib.gis.db import models

from .output_areas import LocalAuthority


class DataZone(models.Model):
    """
    Scotland only
    """

    code = models.CharField("Data Zone Code", max_length=50, unique=True)
    name = models.CharField(
        "Data Zone Name",
        max_length=100,
    )
    year = models.IntegerField("Data Zone Year")
    local_authority = models.ForeignKey(
        to=LocalAuthority,
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Data Zone"
        verbose_name_plural = "Data Zones"
        ordering = ("name",)
