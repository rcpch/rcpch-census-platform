# django
from django.contrib.gis.db import models
from django.contrib.gis.db.models import (
    PointField,
    CharField,
    FloatField,
    BooleanField,
)

# 3rd party
from ..time_and_user_abstract_base_classes import TimeStampAbstractBaseClass


class GeneralPractice(TimeStampAbstractBaseClass):
    """
    This class details information about organisations.
    It represents a list of organisations that can be looked up
    """

    ods_code = CharField(max_length=100, null=True, blank=True, default=None)
    name = CharField(max_length=100, null=True, blank=True, default=None)
    website = CharField(max_length=100, null=True, blank=True, default=None)
    address1 = CharField(max_length=100, null=True, blank=True, default=None)
    address2 = CharField(max_length=100, null=True, blank=True, default=None)
    address3 = CharField(max_length=100, null=True, blank=True, default=None)
    telephone = CharField(max_length=100, null=True, blank=True, default=None)
    city = CharField(max_length=100, null=True, blank=True, default=None)
    county = CharField(max_length=100, null=True, blank=True, default=None)
    latitude = FloatField(max_length=100, null=True, blank=True, default=None)
    longitude = FloatField(null=True, blank=True, default=None)
    postcode = CharField(max_length=10, null=True, blank=True, default=None)
    geocode_coordinates = PointField(null=True, blank=True, default=None, srid=27700)

    active = BooleanField(
        default=True
    )  # a boolean representing if this Organisation is still operational

    published_at = models.DateField(
        null=True, blank=True, default=None
    )  # date this Organisation was last amended according to the ORD

    trust = models.ForeignKey(
        to="organisation_bank.Trust",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    local_health_board = models.ForeignKey(
        to="organisation_bank.LocalHealthBoard",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    integrated_care_board = models.ForeignKey(
        to="organisation_bank.IntegratedCareBoard",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    nhs_england_region = models.ForeignKey(
        to="organisation_bank.NHSEnglandRegion",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )
    # administrative regions
    london_borough = models.ForeignKey(
        to="organisation_bank.LondonBorough",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        default=None,
    )

    country = models.ForeignKey(
        to="organisation_bank.Country", on_delete=models.PROTECT, null=True, blank=True
    )

    class Meta:
        indexes = [models.Index(fields=["name"])]
        verbose_name = "GeneralPractice"
        verbose_name_plural = "GeneralPractices"
        ordering = ("name",)

    def __str__(self) -> str:
        return self.name
