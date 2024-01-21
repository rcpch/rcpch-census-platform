from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema_serializer,
    OpenApiExample,
)

LSOA = apps.get_model("deprivation_scores", "LSOA")
LocalAuthority = apps.get_model("deprivation_scores", "LocalAuthority")
DataZone = apps.get_model("deprivation_scores", "DataZone")
SOA = apps.get_model("deprivation_scores", "SOA")


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
class LSOASerializer(serializers.ModelSerializer):
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


class LocalAuthorityDistrictSerializer(serializers.ModelSerializer):
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
            "/scotland_data_zones/1/",
            value={
                "code": "S01006506",
                "name": "Culter - 01",
                "year": 2011,
                "local_authority": "{BASE_URL}/local_authority_districts/340/",
            },
            response_only=True,
        )
    ]
)
class DataZoneSerializer(serializers.ModelSerializer):
    class Meta:
        model = DataZone
        fields = ["code", "name", "year", "local_authority"]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/northern_ireland_small_output_areas/1/",
            value={"year": 2001, "soa_code": "95AA01S1", "soa_name": "Aldergrove_1"},
            response_only=True,
        )
    ]
)
class SOASerializer(serializers.ModelSerializer):
    class Meta:
        model = SOA
        fields = ["year", "soa_code", "soa_name"]
