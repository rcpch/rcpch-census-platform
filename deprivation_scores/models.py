from django.db import models


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


class Ward(models.Model):
    ward_code = models.CharField(
        "Ward Code", max_length=50, help_text="Ward code", unique=True
    )
    ward_name = models.CharField("Ward name", max_length=50, help_text="Ward name")
    year = models.IntegerField("Ward year")

    msoa = models.ForeignKey(MSOA, on_delete=models.CASCADE)


class IndexMultipleDeprivation(models.Model):
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


class DataZone(models.Model):
    data_zone_code = models.CharField("Data Zone Code", max_length=50, unique=True)
    data_zone_name = models.CharField(
        "Data Zone Name",
        max_length=50,
    )
    year = models.IntegerField("Data Zone Year")
    local_authority = models.ForeignKey(LocalAuthority, on_delete=models.CASCADE)


class GreenSpace(models.Model):
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

    local_authority = models.ForeignKey(LocalAuthority, on_delete=models.CASCADE)
