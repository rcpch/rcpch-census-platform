from django.contrib.gis.db import models

class LocalAuthority(models.Model):
    local_authority_district_code = models.CharField(
        "Local Authority District code (2019)", max_length=50, unique=True
    )
    local_authority_district_name = models.CharField(
        "Local Authority District name (2019)", max_length=50
    )
    year = models.IntegerField(
        "Local Authority District Year",
    )

    class Meta:
        verbose_name = ("Local Authority",)
        verbose_name_plural = "Local Authorities"


class MSOA(models.Model):
    msoa_code = models.CharField(
        "MSOA Code",
        max_length=50,
        help_text="Middle Layer Super Output Layer code",
        unique=True,
    )
    msoa_name = models.CharField(
        "MSOA name",
        max_length=50,
        help_text="Middle Layer Super Output Layer name",
    )
    year = models.IntegerField("Middle Layer Super Output Layer Year")

    local_authority_district = models.ForeignKey(
        LocalAuthority, on_delete=models.CASCADE
    )


class LSOA(models.Model):
    lsoa_code = models.CharField("LSOA code (2011)", unique=True, max_length=50)
    lsoa_name = models.CharField("LSOA name (2011)", max_length=50)
    year = models.IntegerField("Year LSOA calculated")
    total_population_mid_2015 = models.IntegerField(
        "Total population: mid 2015 (excluding prisoners)",
        help_text="Total population: mid 2015 (excluding prisoners)",
        null=True,
    )
    dependent_children_mid_2015 = models.IntegerField(
        "Dependent Children aged 0-15: mid 2015 (excluding prisoners)",
        help_text="Dependent Children aged 0-15: mid 2015 (excluding prisoners)",
        null=True,
    )
    population_16_59_mid_2015 = models.IntegerField(
        "Population aged 16-59: mid 2015 (excluding prisoners)",
        help_text="Population aged 16-59: mid 2015 (excluding prisoners)",
        null=True,
    )
    older_population_over_16_mid_2015 = models.IntegerField(
        "Older population aged 60 and over: mid 2015 (excluding prisoners)",
        help_text="Older population aged 60 and over: mid 2015 (excluding prisoners)",
        null=True,
    )
    working_age_population_over_18_mid_2015 = models.IntegerField(
        "Working age population 18-59/64: for use with Employment Deprivation Domain (excluding prisoners)",
        help_text="Working age population 18-59/64: for use with Employment Deprivation Domain (excluding prisoners)",
        null=True,
    )

    local_authority_district = models.ForeignKey(
        to=LocalAuthority, on_delete=models.CASCADE
    )

    class Meta:
        verbose_name = ("LSOA",)
        verbose_name_plural = "LSOAs"

class SOA(models.Model):
    """
    Northern Ireland
    """
    year = models.IntegerField()
    soa_code = models.CharField(max_length=50, unique=True)
    soa_name = models.CharField(max_length=50)