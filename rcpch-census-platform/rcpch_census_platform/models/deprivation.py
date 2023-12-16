from django.contrib.gis.db import models

from .output_areas import SOA, LSOA
from .data_zones import DataZone


class EnglishIndexMultipleDeprivation(models.Model):
    imd_score = models.DecimalField(
        "Index of Multiple Deprivation (IMD) Score",
        help_text="Index of Multiple Deprivation (IMD) Score",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    imd_rank = models.IntegerField(
        "Index of Multiple Deprivation",
        help_text="Index of Multiple Deprivation (IMD) Rank (where 1 is most deprived)",
    )
    imd_decile = models.IntegerField(
        "Index of Multiple Deprivation (IMD) Decile",
        help_text="Index of Multiple Deprivation (IMD) Decile (where 1 is most deprived 10% of LSOAs)",
    )
    income_score = models.DecimalField(
        "Income Score (rate)",
        help_text="Income Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    income_score_exponentially_transformed = models.DecimalField(
        "Income Score exponentially tranformed",
        help_text="Income Score exponentially tranformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    income_rank = models.IntegerField(
        "Income Rank",
        help_text="Income Rank (where 1 is most deprived)",
    )
    income_decile = models.IntegerField(
        "Income Decile",
        help_text="Income Decile (where 1 is most deprived 10% of LSOAs)",
    )
    employment_score = models.DecimalField(
        "Employment Score (rate)",
        help_text="Employment Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    employment_score_exponentially_transformed = models.DecimalField(
        "Employment Score exponentially transformed",
        help_text="Employment Score exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    employment_rank = models.IntegerField(
        "Employment Rank",
        help_text="Employment Rank (where 1 is most deprived)",
    )
    employment_decile = models.IntegerField(
        "Employment Decile",
        help_text="Employment Decile (where 1 is most deprived 10% of LSOAs)",
    )
    education_skills_training_score_exponentially_transformed = models.DecimalField(
        "Education, Skills and Training Score exponentially transformed",
        help_text="Education, Skills and Training Score exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    education_skills_training_score = models.DecimalField(
        "Education, Skills and Training Score (rate)",
        help_text="Education, Skills and Training Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    education_skills_training_rank = models.IntegerField(
        "Education, Skills and Training Rank",
        help_text="Education, Skills and Training Rank (where 1 is most deprived)",
    )
    education_skills_training_decile = models.IntegerField(
        "Education, Skills and Training Decile",
        help_text="Education, Skills and Training Decile (where 1 is most deprived 10% of LSOAs)",
    )
    children_young_people_sub_domain_score = models.DecimalField(
        "Children and Young People Sub-domain Score (rate)",
        help_text="Children and Young People Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    children_young_people_sub_domain_rank = models.IntegerField(
        "Children and Young People Sub-domain Rank (where 1 is most deprived)",
        help_text="Children and Young People Sub-domain Rank (where 1 is most deprived)",
        null=True,
    )
    children_young_people_sub_domain_decile = models.IntegerField(
        "Children and Young People Sub-domain Decile (where 1 is most deprived) Decile",
        help_text="Children and Young People Sub-domain Decile (where 1 is most deprived) Decile",
        null=True,
    )
    adult_skills_sub_domain_score = models.DecimalField(
        "Adult Skills Sub-domain Score (rate)",
        help_text="Adult Skills Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    adult_skills_sub_domain_rank = models.IntegerField(
        "Adult Skills Sub-domain Rank (where 1 is most deprived)",
        help_text="Adult Skills Sub-domain Rank (where 1 is most deprived)",
        null=True,
    )
    adult_skills_sub_domain_decile = models.IntegerField(
        "Adult Skills Sub-domain Decile (where 1 is most deprived) Decile",
        help_text="Adult Skills Sub-domain Decile (where 1 is most deprived) Decile",
        null=True,
    )
    health_deprivation_disability_score_exponentially_transformed = models.DecimalField(
        "Health Deprivation and Disability Score exponentially transformed",
        help_text="Health Deprivation and Disability Score exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    health_deprivation_disability_score = models.DecimalField(
        "Health Deprivation and Disability Score (rate)",
        help_text="Health Deprivation and Disability Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    health_deprivation_disability_rank = models.IntegerField(
        "Health Deprivation and Disability Rank",
        help_text="Health Deprivation and Disability Rank (where 1 is most deprived)",
    )
    health_deprivation_disability_decile = models.IntegerField(
        "Health Deprivation and Disability Decile",
        help_text="Health Deprivation and Disability Decile (where 1 is most deprived 10% of LSOAs)",
    )
    crime_score_exponentially_transformed = models.DecimalField(
        "Crime Score exponentially transformed",
        help_text="Crime Score exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    crime_score = models.DecimalField(
        "Crime Score (rate)",
        help_text="Crime Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    crime_rank = models.IntegerField(
        "Crime Rank",
        help_text="Crime Rank (where 1 is most deprived)",
    )
    crime_decile = models.IntegerField(
        "Crime Decile",
        help_text="Crime Decile (where 1 is most deprived 10% of LSOAs)",
    )
    barriers_to_housing_services_score_exponentially_transformed = models.DecimalField(
        "Barriers to Housing and Services Score Exponentially transformed",
        help_text="Barriers to Housing and Services Score Exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    barriers_to_housing_services_score = models.DecimalField(
        "Barriers to Housing and Services Score (rate)",
        help_text="Barriers to Housing and Services Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    barriers_to_housing_services_rank = models.IntegerField(
        "Barriers to Housing and Services Rank",
        help_text="Barriers to Housing and Services Rank (where 1 is most deprived)",
    )
    barriers_to_housing_services_decile = models.IntegerField(
        "Barriers to Housing and Services Decile",
        help_text="Barriers to Housing and Services Decile (where 1 is most deprived 10% of LSOAs)",
    )
    geographical_barriers_sub_domain_score = models.DecimalField(
        "Geographical Barriers Sub-domain Score",
        help_text="Geographical Barriers Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    geographical_barriers_sub_domain_rank = models.IntegerField(
        "Geographical Barriers Sub-domain Rank",
        help_text="Geographical Barriers Sub-domain Rank (where 1 is most deprived)",
        null=True,
    )
    geographical_barriers_sub_domain_decile = models.IntegerField(
        "Geographical Barriers Sub-domain Decile",
        help_text="Geographical Barriers Sub-domain Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )
    wider_barriers_sub_domain_score = models.DecimalField(
        "Wider Barriers Sub-domain Score (rate)",
        help_text="Wider Barriers Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    wider_barriers_sub_domain_rank = models.IntegerField(
        "Wider Barriers Sub-domain Rank",
        help_text="Wider Barriers Sub-domain Rank (where 1 is most deprived)",
        null=True,
    )
    wider_barriers_sub_domain_decile = models.IntegerField(
        "Wider Barriers Sub-domain Decile",
        help_text="Wider Barriers Sub-domain Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )
    living_environment_score = models.DecimalField(
        "Living Environment Score (rate)",
        help_text="Living Environment Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    living_environment_score_exponentially_transformed = models.DecimalField(
        "Living Environment Score exponentially transformed",
        help_text="Living Environment Score exponentially transformed",
        null=True,
        max_digits=6,
        decimal_places=3,
    )
    living_environment_rank = models.IntegerField(
        "Living Environment Rank",
        help_text="Living Environment Rank (where 1 is most deprived)",
    )
    living_environment_decile = models.IntegerField(
        "Living Environment Decile",
        help_text="Living Environment Decile (where 1 is most deprived 10% of LSOAs)",
    )
    indoors_sub_domain_score = models.DecimalField(
        "Indoors Sub-domain Score (rate)",
        help_text="Indoors Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    indoors_sub_domain_rank = models.IntegerField(
        "Indoors Sub-domain Rank",
        help_text="Indoors Sub-domain Rank (where 1 is most deprived)",
        null=True,
    )
    indoors_sub_domain_decile = models.IntegerField(
        "Indoors Sub-domain Decile",
        help_text="Indoors Sub-domain Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )
    outdoors_sub_domain_score = models.DecimalField(
        "Outdoors Sub-domain Score (rate)",
        help_text="Outdoors Sub-domain Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    outdoors_sub_domain_rank = models.IntegerField(
        "Outdoors Sub-domain Rank",
        help_text="Outdoors Sub-domain Rank(where 1 is most deprived)",
        null=True,
    )
    outdoors_sub_domain_decile = models.IntegerField(
        "Outdoors Sub-domain Decile",
        help_text="Outdoors Sub-domain Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )
    idaci_score = models.DecimalField(
        "Income Deprivation Affecting Children Index Score (rate)",
        help_text="Income Deprivation Affecting Children Index (IDACI) Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    idaci_rank = models.IntegerField(
        "Income Deprivation Affecting Children Index Rank",
        help_text="Income Deprivation Affecting Children Index (IDACI) Rank (where 1 is most deprived)",
        null=True,
    )
    idaci_decile = models.IntegerField(
        "Income Deprivation Affecting Children Index Decile",
        help_text="Income Deprivation Affecting Children Index (IDACI) Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )
    idaopi_score = models.DecimalField(
        "Income Deprivation Affecting Older People Index Score (rate)",
        help_text="Income Deprivation Affecting Older People Index (IDAOPI) Score (rate)",
        null=True,
        max_digits=5,
        decimal_places=3,
    )
    idaopi_rank = models.IntegerField(
        "Income Deprivation Affecting Older People Index Rank",
        help_text="Income Deprivation Affecting Older People Index (IDAOPI) Rank (where 1 is most deprived)",
        null=True,
    )
    idaopi_decile = models.IntegerField(
        "Income Deprivation Affecting Older People Index Decile",
        help_text="Income Deprivation Affecting Older People Index (IDAOPI) Decile (where 1 is most deprived 10% of LSOAs)",
        null=True,
    )

    lsoa = models.ForeignKey(LSOA, on_delete=models.CASCADE)

    class Meta:
        verbose_name = "English Index of Multiple Deprivation"
        verbose_name_plural = "English Indices of Multiple Deprivation"
        ordering = ("imd_rank",)


class WelshIndexMultipleDeprivation(models.Model):
    imd_rank = models.IntegerField()
    imd_quartile = models.SmallIntegerField()
    imd_quintile = models.SmallIntegerField()
    imd_decile = models.SmallIntegerField()
    imd_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    income_rank = models.IntegerField()
    income_quartile = models.SmallIntegerField()
    income_quintile = models.SmallIntegerField()
    income_decile = models.SmallIntegerField()
    income_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    employment_rank = models.IntegerField()
    employment_quartile = models.SmallIntegerField()
    employment_quintile = models.SmallIntegerField()
    employment_decile = models.SmallIntegerField()
    employment_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    health_rank = models.IntegerField()
    health_quartile = models.SmallIntegerField()
    health_quintile = models.SmallIntegerField()
    health_decile = models.SmallIntegerField()
    health_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    education_rank = models.IntegerField()
    education_quartile = models.SmallIntegerField()
    education_quintile = models.SmallIntegerField()
    education_decile = models.SmallIntegerField()
    education_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    access_to_services_rank = models.IntegerField()
    access_to_services_quartile = models.SmallIntegerField()
    access_to_services_quintile = models.SmallIntegerField()
    access_to_services_decile = models.SmallIntegerField()
    access_to_services_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    housing_rank = models.IntegerField()
    housing_quartile = models.SmallIntegerField()
    housing_quintile = models.SmallIntegerField()
    housing_decile = models.SmallIntegerField()
    housing_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    community_safety_rank = models.IntegerField()
    community_safety_quartile = models.SmallIntegerField()
    community_safety_quintile = models.SmallIntegerField()
    community_safety_decile = models.SmallIntegerField()
    community_safety_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    physical_environment_rank = models.IntegerField()
    physical_environment_quartile = models.SmallIntegerField()
    physical_environment_quintile = models.SmallIntegerField()
    physical_environment_decile = models.SmallIntegerField()
    physical_environment_score = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True
    )
    lsoa = models.ForeignKey(LSOA, on_delete=models.CASCADE)
    year = models.IntegerField()

    class Meta:
        verbose_name = "Welsh Index of Multiple Deprivation"
        verbose_name_plural = "Welsh Indices of Multiple Deprivation"
        ordering = ("imd_rank",)


class ScottishIndexMultipleDeprivation(models.Model):
    year = models.IntegerField()
    version = models.SmallIntegerField()
    imd_rank = models.IntegerField()
    income_rank = models.IntegerField()
    employment_rank = models.IntegerField()
    education_rank = models.IntegerField()
    health_rank = models.IntegerField()
    access_rank = models.IntegerField()
    crime_rank = models.IntegerField()
    housing_rank = models.IntegerField()
    data_zone = models.ForeignKey(to=DataZone, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Scottish Index of Multiple Deprivation"
        verbose_name_plural = "Scottish Indices of Multiple Deprivation"
        ordering = ("imd_rank",)


class NorthernIrelandIndexMultipleDeprivation(models.Model):
    imd_rank = models.IntegerField()
    year = models.IntegerField()
    income_rank = models.IntegerField()
    employment_rank = models.IntegerField()
    health_deprivation_and_disability_rank = models.IntegerField()
    education_skills_and_training_rank = models.IntegerField()
    access_to_services_rank = models.IntegerField()
    living_environment_rank = models.IntegerField()
    crime_and_disorder_rank = models.IntegerField()
    soa = models.ForeignKey(to=SOA, on_delete=models.PROTECT)

    class Meta:
        verbose_name = "Northern Ireland Index of Multiple Deprivation"
        verbose_name_plural = "Northern Ireland Indices of Multiple Deprivation"
        ordering = ("imd_rank",)
