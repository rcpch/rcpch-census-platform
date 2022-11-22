from rest_framework import serializers
from .models import LSOA, LocalAuthority, IndexMultipleDeprivation, GreenSpace


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


class IndexMultipleDeprivationSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IndexMultipleDeprivation
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


class GreenSpaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GreenSpace
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
            "total_percentage_addresses_with_private_outdoor_space_count",
            "total_average_size_private_outdoor_space_count",
            "local_authority",
        ]
