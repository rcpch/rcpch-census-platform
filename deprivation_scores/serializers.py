from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import (
    LSOA,
    LocalAuthority,
    GreenSpace,
    DataZone,
    SOA,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "Swansea",
            value={
                "lsoa_code": "W01001958",
                "lsoa_name": "Swansea 025H",
                "year": 2011,
                "total_population_mid_2015": None,
                "dependent_children_mid_2015": None,
                "population_16_59_mid_2015": None,
                "older_population_over_16_mid_2015": None,
                "working_age_population_over_18_mid_2015": None,
            },
            response_only=True,
        )
    ]
)
class LSOASerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LSOA
        fields = [
            "lsoa_code",
            "lsoa_name",
            "year",
            "total_population_mid_2015",
            "dependent_children_mid_2015",
            "population_16_59_mid_2015",
            "older_population_over_16_mid_2015",
            "working_age_population_over_18_mid_2015",
        ]


class LocalAuthorityDistrictSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = LocalAuthority
        fields = [
            "local_authority_district_code",
            "local_authority_district_name",
            "year",
        ]


class GreenSpaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GreenSpace
        # depth = 1
        fields = [
            "houses_address_count",
            "houses_addresses_with_private_outdoor_space_count",
            "houses_outdoor_space_total_area",
            "houses_outdoor_space_total_area",
            "houses_percentage_of_addresses_with_private_outdoor_space",
            "houses_average_size_private_outdoor_space",
            "houses_median_size_private_outdoor_space",
            "flats_address_count",
            "flats_addresses_with_private_outdoor_space_count",
            "flats_outdoor_space_total_area",
            "flats_outdoor_space_count",
            "flats_percentage_of_addresses_with_private_outdoor_space",
            "flats_average_size_private_outdoor_space",
            "flats_average_number_of_flats_sharing_a_garden",
            "total_addresses_count",
            "total_addresses_with_private_outdoor_space_count",
            "total_percentage_addresses_with_private_outdoor_space",
            "total_average_size_private_outdoor_space",
            "local_authority",
        ]


class DataZoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataZone
        fields = ["data_zone_code", "data_zone_name", "year", "local_authority"]


class SOASerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SOA
        fields = ["year", "soa_code", "soa_name"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "LSOA 15014",
            value={
                "imd_score": "10.908",
                "imd_rank": 23438,
                "imd_decile": 8,
                "income_score": "0.061",
                "income_score_exponentially_transformed": "7.683",
                "income_rank": 23396,
                "income_decile": 8,
                "employment_score": "0.053",
                "employment_score_exponentially_transformed": "7.492",
                "employment_rank": 23595,
                "employment_decile": 8,
                "education_skills_training_score_exponentially_transformed": "33.459",
                "education_skills_training_score": "33.331",
                "education_skills_training_rank": 7339,
                "education_skills_training_decile": 3,
                "children_young_people_sub_domain_score": "0.528",
                "children_young_people_sub_domain_rank": 8508,
                "children_young_people_sub_domain_decile": 3,
                "adult_skills_sub_domain_score": "0.406",
                "adult_skills_sub_domain_rank": 6398,
                "adult_skills_sub_domain_decile": 2,
                "health_deprivation_disability_score_exponentially_transformed": "5.537",
                "health_deprivation_disability_score": "-0.681",
                "health_deprivation_disability_rank": 25726,
                "health_deprivation_disability_decile": 8,
                "crime_score_exponentially_transformed": "2.248",
                "crime_score": "-1.090",
                "crime_rank": 29747,
                "crime_decile": 10,
                "barriers_to_housing_services_score_exponentially_transformed": "21.124",
                "barriers_to_housing_services_score": "23.332",
                "barriers_to_housing_services_rank": 12852,
                "barriers_to_housing_services_decile": 4,
                "geographical_barriers_sub_domain_score": "0.654",
                "geographical_barriers_sub_domain_rank": 6287,
                "geographical_barriers_sub_domain_decile": 2,
                "wider_barriers_sub_domain_score": "-1.095",
                "wider_barriers_sub_domain_rank": 21245,
                "wider_barriers_sub_domain_decile": 7,
                "living_environment_score": "2.029",
                "living_environment_score_exponentially_transformed": "0.602",
                "living_environment_rank": 31986,
                "living_environment_decile": 10,
                "indoors_sub_domain_score": "-1.089",
                "indoors_sub_domain_rank": 29674,
                "indoors_sub_domain_decile": 10,
                "outdoors_sub_domain_score": "-1.180",
                "outdoors_sub_domain_rank": 30773,
                "outdoors_sub_domain_decile": 10,
                "idaci_score": "0.071",
                "idaci_rank": 23801,
                "idaci_decile": 8,
                "idaopi_score": "0.081",
                "idaopi_rank": 23219,
                "idaopi_decile": 8,
                "lsoa": "http://localhost:8001/england_wales_lower_layer_super_output_areas/15014/",
            },
            response_only=True,
        )
    ]
)
class EnglishIndexMultipleDeprivationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = EnglishIndexMultipleDeprivation
        fields = [
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
            "indoors_sub_domain_rank",
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
            "lsoa",
        ]


class WelshIndexMultipleDeprivationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = WelshIndexMultipleDeprivation
        fields = [
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
        ]


class ScottishIndexMultipleDeprivationSerializer(
    serializers.HyperlinkedModelSerializer
):
    class Meta:
        model = ScottishIndexMultipleDeprivation
        fields = [
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
        ]


class NorthernIrelandIndexMultipleDeprivationSerializer(
    serializers.HyperlinkedModelSerializer
):
    class Meta:
        model = NorthernIrelandIndexMultipleDeprivation
        fields = [
            "imd_rank",
            "year",
            "income_rank",
            "employment_rank",
            "health_deprivation_and_disability_rank",
            "education_skills_and_training_rank",
            "access_to_services_rank",
            "living_environment_rank",
            "crime_and_disorder_rank",
            "soa",
        ]
