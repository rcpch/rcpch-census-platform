from django.db import models


class GreenSpace(models.Model):
    """
    England and Wales
    """

    houses_address_count = models.IntegerField("Houses - Address Count")
    houses_addresses_with_private_outdoor_space_count = models.IntegerField(
        "Houses - Addresses with private outdoor space Count"
    )
    houses_outdoor_space_total_area = models.IntegerField(
        "Houses - Outdoor space total area (m2)"
    )
    houses_outdoor_space_total_area = models.IntegerField(
        "Houses - Outdoor space total area (m2)"
    )
    houses_percentage_of_addresses_with_private_outdoor_space = models.IntegerField(
        "Houses - Percentage of addresses with private outdoor space"
    )
    houses_average_size_private_outdoor_space = models.IntegerField(
        "Houses - Average size of private outdoor space (m2)"
    )
    houses_median_size_private_outdoor_space = models.IntegerField(
        "Houses - Median size of private outdoor space (m2)"
    )
    flats_address_count = models.IntegerField("Flats - Address Count")
    flats_addresses_with_private_outdoor_space_count = models.IntegerField(
        "Flats - Addresses with private outdoor space Count"
    )
    flats_outdoor_space_total_area = models.IntegerField(
        "Flats - Outdoor space total area (m2)"
    )
    flats_outdoor_space_count = models.IntegerField(
        "Flats - Count of flats with outdoor space"
    )
    flats_percentage_of_addresses_with_private_outdoor_space = models.IntegerField(
        "Flats - Percentage of addresses with private outdoor space"
    )
    flats_average_size_private_outdoor_space = models.IntegerField(
        "Flats - Average size of private outdoor space (m2)"
    )
    flats_average_number_of_flats_sharing_a_garden = models.IntegerField(
        "Flats - Average number of flats sharing a garden"
    )
    total_addresses_count = models.IntegerField("Total - count of all addresses")
    total_addresses_with_private_outdoor_space_count = models.IntegerField(
        "Total - count of all addresses with private outdoor space"
    )
    total_percentage_addresses_with_private_outdoor_space = models.IntegerField(
        "Total - percentage of all addresses with private outdoor space"
    )
    total_average_size_private_outdoor_space = models.IntegerField(
        "Total - average size of all private outdoor space"
    )

    local_authority = models.ForeignKey(
        to="deprivation_scores.LocalAuthority",
        on_delete=models.CASCADE,
    )

    class Meta:
        verbose_name = "Access to Green Space"
        verbose_name_plural = "Access to Green Spaces"
