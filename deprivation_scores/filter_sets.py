from django_filters.filterset import FilterSet, CharFilter, NumberFilter
from .models import (
    DataZone,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
)


class DataZoneFilter(FilterSet):
    local_authority_code = CharFilter(
        field_name="local_authority__local_authority_district_code",
        lookup_expr="icontains",
    )
    local_authority_name = CharFilter(
        field_name="local_authority__local_authority_name",
        lookup_expr="icontains",
    )

    class Meta:
        model = DataZone
        fields = (
            "data_zone_code",
            "data_zone_name",
            "year",
        )


class EnglishIndexMultipleDeprivationFilter(FilterSet):
    lsoa_code = CharFilter(
        field_name="lsoa__lsoa_code",
        lookup_expr="icontains",
    )
    lsoa_name = CharFilter(
        field_name="lsoa__lsoa_name",
        lookup_expr="icontains",
    )
    local_authority_code = CharFilter(
        field_name="lsoa__local_authority__local_authority_district_code",
        lookup_expr="icontains",
    )
    local_authority_name = CharFilter(
        field_name="lsoa__local_authority__local_authority_district_name",
        lookup_expr="icontains",
    )

    class Meta:
        model = EnglishIndexMultipleDeprivation
        fields = (
            "imd_score",
            "imd_rank",
            "imd_decile",
            "income_score",
            "income_score_exponentially_transformed",
            "income_rank",
            "income_decile",
            "employment_score",
            "employment_score_exponentially_transformed",
            "employment_rank",
            "employment_decile",
            "education_skills_training_score_exponentially_transformed",
            "education_skills_training_score",
            "education_skills_training_rank",
            "education_skills_training_decile",
            "children_young_people_sub_domain_score",
            "children_young_people_sub_domain_rank",
            "children_young_people_sub_domain_decile",
            "adult_skills_sub_domain_score",
            "adult_skills_sub_domain_rank",
            "adult_skills_sub_domain_decile",
            "health_deprivation_disability_score_exponentially_transformed",
            "health_deprivation_disability_score",
            "health_deprivation_disability_rank",
            "health_deprivation_disability_decile",
            "crime_score_exponentially_transformed",
            "crime_score",
            "crime_rank",
            "crime_decile",
            "barriers_to_housing_services_score_exponentially_transformed",
            "barriers_to_housing_services_score",
            "barriers_to_housing_services_rank",
            "barriers_to_housing_services_decile",
            "geographical_barriers_sub_domain_score",
            "geographical_barriers_sub_domain_rank",
            "geographical_barriers_sub_domain_decile",
            "wider_barriers_sub_domain_score",
            "wider_barriers_sub_domain_rank",
            "wider_barriers_sub_domain_decile",
            "living_environment_score",
            "living_environment_score_exponentially_transformed",
            "living_environment_rank",
            "living_environment_decile",
            "indoors_sub_domain_score",
            "indoors_sub_domain_decile",
            "outdoors_sub_domain_score",
            "outdoors_sub_domain_rank",
            "outdoors_sub_domain_decile",
            "idaci_score",
            "idaci_rank",
            "idaci_decile",
            "idaopi_score",
            "idaopi_rank",
            "idaopi_decile",
        )


class WelshIndexMultipleDeprivationFilter(FilterSet):
    lsoa_code = CharFilter(
        field_name="lsoa__lsoa_code",
        lookup_expr="icontains",
    )
    lsoa_name = CharFilter(
        field_name="lsoa__lsoa_name",
        lookup_expr="icontains",
    )
    local_authority_code = CharFilter(
        field_name="lsoa__local_authority__local_authority_district",
        lookup_expr="icontains",
    )

    class Meta:
        model = WelshIndexMultipleDeprivation
        fields = (
            "imd_rank",
            "imd_quartile",
            "imd_quintile",
            "imd_decile",
            "imd_score",
            "income_rank",
            "income_quartile",
            "income_quintile",
            "income_decile",
            "income_score",
            "employment_rank",
            "employment_quartile",
            "employment_quintile",
            "employment_decile",
            "employment_score",
            "health_rank",
            "health_quartile",
            "health_quintile",
            "health_decile",
            "health_score",
            "education_rank",
            "education_quartile",
            "education_quintile",
            "education_decile",
            "education_score",
            "access_to_services_rank",
            "access_to_services_quartile",
            "access_to_services_quintile",
            "access_to_services_decile",
            "access_to_services_score",
            "housing_rank",
            "housing_quartile",
            "housing_quintile",
            "housing_decile",
            "housing_score",
            "community_safety_rank",
            "community_safety_quartile",
            "community_safety_quintile",
            "community_safety_decile",
            "community_safety_score",
            "physical_environment_rank",
            "physical_environment_quartile",
            "physical_environment_quintile",
            "physical_environment_decile",
            "physical_environment_score",
            "lsoa",
            "year",
        )
        exclude = "id"


class ScottishIndexMultipleDeprivationFilter(FilterSet):
    data_zone_code = CharFilter(
        field_name="data_zone__data_zone_code",
        lookup_expr="icontains",
    )
    data_zone_name = CharFilter(
        field_name="data_zone__data_zone_name",
        lookup_expr="icontains",
    )
    local_authority_code = CharFilter(
        field_name="data_zone__local_authority",
        lookup_expr="icontains",
    )

    class Meta:
        model = ScottishIndexMultipleDeprivation
        fields = (
            "year",
            "version",
            "imd_rank",
            "income_rank",
            "employment_rank",
            "education_rank",
            "health_rank",
            "access_rank",
            "crime_rank",
            "housing_rank",
            "data_zone",
        )
        exclude = "id"


class NorthernIrelandIndexMultipleDeprivationFilter(FilterSet):
    soa_zone_code = CharFilter(
        field_name="soa__soa_code",
        lookup_expr="icontains",
    )
    soa_zone_name = CharFilter(
        field_name="soa__soa_name",
        lookup_expr="icontains",
    )
    local_authority_code = CharFilter(
        field_name="soa__local_authority",
        lookup_expr="icontains",
    )

    class Meta:
        model = NorthernIrelandIndexMultipleDeprivation
        fields = (
            "imd_rank",
            "year",
            "income_rank",
            "employment_rank",
            "health_deprivation_and_disability_rank",
            "education_skills_and_training_rank",
            "access_to_services_rank",
            "living_environment_rank",
            "crime_and_disorder_rank",
        )
        exclude = "id"
