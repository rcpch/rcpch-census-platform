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
            "/england_wales_lower_layer_super_output_areas/1/",
            value={
                "lsoa_code": "E01012057",
                "lsoa_name": "Middlesbrough 009E",
                "year": 2011,
                "total_population_mid_2015": "null",
                "dependent_children_mid_2015": "null",
                "population_16_59_mid_2015": "null",
                "older_population_over_16_mid_2015": "null",
                "working_age_population_over_18_mid_2015": "null",
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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/green_space/1/",
            value={
                "houses_address_count": 53082,
                "houses_addresses_with_private_outdoor_space_count": 51390,
                "houses_outdoor_space_total_area": 14593876,
                "houses_percentage_of_addresses_with_private_outdoor_space": 0,
                "houses_average_size_private_outdoor_space": 284,
                "houses_median_size_private_outdoor_space": 204,
                "flats_address_count": 65346,
                "flats_addresses_with_private_outdoor_space_count": 46221,
                "flats_outdoor_space_total_area": 2953183,
                "flats_outdoor_space_count": 9280,
                "flats_percentage_of_addresses_with_private_outdoor_space": 0,
                "flats_average_size_private_outdoor_space": 318,
                "flats_average_number_of_flats_sharing_a_garden": 5,
                "total_addresses_count": 118428,
                "total_addresses_with_private_outdoor_space_count": 97611,
                "total_percentage_addresses_with_private_outdoor_space": 17547060,
                "total_average_size_private_outdoor_space": 0,
                "local_authority": "{BASE_URL}/local_authority_districts/340/",
            },
            response_only=True,
        )
    ]
)
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


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/scotland_data_zones/1/",
            value={
                "data_zone_code": "S01006506",
                "data_zone_name": "Culter - 01",
                "year": 2011,
                "local_authority": "{BASE_URL}/local_authority_districts/340/",
            },
            response_only=True,
        )
    ]
)
class DataZoneSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = DataZone
        fields = ["data_zone_code", "data_zone_name", "year", "local_authority"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/northern_ireland_small_output_areas/1/",
            value={"year": 2001, "soa_code": "95AA01S1", "soa_name": "Aldergrove_1"},
            response_only=True,
        )
    ]
)
class SOASerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = SOA
        fields = ["year", "soa_code", "soa_name"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/english_indices_of_multiple_deprivation/1/",
            value={
                "imd_score": "6.208",
                "imd_rank": 29199,
                "imd_decile": 9,
                "income_score": "0.007",
                "income_score_exponentially_transformed": "0.010",
                "income_rank": 32831,
                "income_decile": 10,
                "employment_score": "0.010",
                "employment_score_exponentially_transformed": "0.071",
                "employment_rank": 32742,
                "employment_decile": 10,
                "education_skills_training_score_exponentially_transformed": "0.002",
                "education_skills_training_score": "0.024",
                "education_skills_training_rank": 32842,
                "education_skills_training_decile": 10,
                "children_young_people_sub_domain_score": "-2.107",
                "children_young_people_sub_domain_rank": 32777,
                "children_young_people_sub_domain_decile": 10,
                "adult_skills_sub_domain_score": "0.032",
                "adult_skills_sub_domain_rank": 32843,
                "adult_skills_sub_domain_decile": 10,
                "health_deprivation_disability_score_exponentially_transformed": "0.512",
                "health_deprivation_disability_score": "-1.654",
                "health_deprivation_disability_rank": 32113,
                "health_deprivation_disability_decile": 10,
                "crime_score_exponentially_transformed": "0.127",
                "crime_score": "-2.012",
                "crime_rank": 32662,
                "crime_decile": 10,
                "barriers_to_housing_services_score_exponentially_transformed": "33.518",
                "barriers_to_housing_services_score": "29.472",
                "barriers_to_housing_services_rank": 7319,
                "barriers_to_housing_services_decile": 3,
                "geographical_barriers_sub_domain_score": "-0.430",
                "geographical_barriers_sub_domain_rank": 22985,
                "geographical_barriers_sub_domain_decile": 7,
                "wider_barriers_sub_domain_score": "3.587",
                "wider_barriers_sub_domain_rank": 3216,
                "wider_barriers_sub_domain_decile": 1,
                "living_environment_score": "31.873",
                "living_environment_score_exponentially_transformed": "32.163",
                "living_environment_rank": 7789,
                "living_environment_decile": 3,
                "indoors_sub_domain_score": "0.006",
                "indoors_sub_domain_rank": 16364,
                "indoors_sub_domain_decile": 5,
                "outdoors_sub_domain_score": "1.503",
                "outdoors_sub_domain_rank": 1615,
                "outdoors_sub_domain_decile": 1,
                "idaci_score": "0.006",
                "idaci_rank": 32806,
                "idaci_decile": 10,
                "idaopi_score": "0.012",
                "idaopi_rank": 32820,
                "idaopi_decile": 10,
                "lsoa": "http://localhost:8001/england_wales_lower_layer_super_output_areas/28110/",
            },
            response_only=True,
        )
    ]
)
class EnglishIndexMultipleDeprivationSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SerializerMethodField()

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
            "type",  # for PolymorphicProxySerializer
        ]

    def get_type(self, obj) -> str:
        return "English"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/welsh_indices_of_multiple_deprivation/1/",
            value={
                "imd_rank": 885,
                "imd_quartile": 2,
                "imd_quintile": 3,
                "imd_decile": 5,
                "imd_score": "19.2",
                "income_rank": 898,
                "income_quartile": 2,
                "income_quintile": 3,
                "income_decile": 5,
                "income_score": "17.0",
                "employment_rank": 659,
                "employment_quartile": 2,
                "employment_quintile": 2,
                "employment_decile": 4,
                "employment_score": "23.9",
                "health_rank": 1213,
                "health_quartile": 3,
                "health_quintile": 4,
                "health_decile": 7,
                "health_score": "10.3",
                "education_rank": 1057,
                "education_quartile": 3,
                "education_quintile": 3,
                "education_decile": 6,
                "education_score": "13.4",
                "access_to_services_rank": 221,
                "access_to_services_quartile": 1,
                "access_to_services_quintile": 1,
                "access_to_services_decile": 2,
                "access_to_services_score": "47.5",
                "housing_rank": 935,
                "housing_quartile": 2,
                "housing_quintile": 3,
                "housing_decile": 5,
                "housing_score": "16.1",
                "community_safety_rank": 914,
                "community_safety_quartile": 2,
                "community_safety_quintile": 3,
                "community_safety_decile": 5,
                "community_safety_score": "16.6",
                "physical_environment_rank": 1859,
                "physical_environment_quartile": 4,
                "physical_environment_quintile": 5,
                "physical_environment_decile": 10,
                "physical_environment_score": "0.6",
                "lsoa": "{BASE_URL}/england_wales_lower_layer_super_output_areas/33054/",
                "year": 2019,
                "type": "English",
            },
            response_only=True,
        )
    ]
)
class WelshIndexMultipleDeprivationSerializer(serializers.HyperlinkedModelSerializer):
    type = serializers.SerializerMethodField()

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
            "type",
        ]

    def get_type(self, obj) -> str:
        return "English"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/scottish_indices_of_multiple_deprivation/1/",
            value={
                "year": 2020,
                "version": 2,
                "imd_rank": 4691,
                "income_rank": 3936,
                "employment_rank": 3220,
                "education_rank": 5887,
                "health_rank": 5174,
                "access_rank": 4724,
                "crime_rank": 4664,
                "housing_rank": 3248,
                "data_zone": "{BASE_URL}/scotland_data_zones/1/",
                "type": "Scottish",
            },
            response_only=True,
        )
    ]
)
class ScottishIndexMultipleDeprivationSerializer(
    serializers.HyperlinkedModelSerializer
):
    type = serializers.SerializerMethodField()

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
            "type",
        ]

    def get_type(self, obj) -> str:
        return "English"


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/northern_ireland_indices_of_multiple_deprivation/1/",
            value={
                "imd_rank": 516,
                "year": 2017,
                "income_rank": 790,
                "employment_rank": 888,
                "health_deprivation_and_disability_rank": 890,
                "education_skills_and_training_rank": 254,
                "access_to_services_rank": 17,
                "living_environment_rank": 75,
                "crime_and_disorder_rank": 874,
                "soa": "http://localhost:8001/northern_ireland_small_output_areas/1/",
                "type": "English",
            },
            response_only=True,
        )
    ]
)
class NorthernIrelandIndexMultipleDeprivationSerializer(
    serializers.HyperlinkedModelSerializer
):
    type = serializers.SerializerMethodField()

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
            "type",
        ]

    def get_type(self, obj) -> str:
        return "English"
