from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import (
    OpenApiExample,
    extend_schema_serializer,
    OpenApiExample,
)

Country = apps.get_model("rcpch_census_platform", "Country")
Organisation = apps.get_model("rcpch_census_platform", "Organisation")
IntegratedCareBoard = apps.get_model("rcpch_census_platform", "IntegratedCareBoard")
LocalHealthBoard = apps.get_model("rcpch_census_platform", "LocalHealthBoard")
LondonBorough = apps.get_model("rcpch_census_platform", "LondonBorough")
NHSEnglandRegion = apps.get_model("rcpch_census_platform", "NHSEnglandRegion")
OPENUKNetwork = apps.get_model("rcpch_census_platform", "OPENUKNetwork")
PaediatricDiabetesUnit = apps.get_model(
    "rcpch_census_platform", "PaediatricDiabetesUnit"
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/organisation/1/",
            value={
                "ods_code": "RGT01",
                "name": "ADDENBROOKE'S HOSPITAL",
                "website": "https://www.cuh.nhs.uk/",
                "address1": "HILLS ROAD",
                "address2": "",
                "address3": "",
                "telephone": "01223 245151",
                "city": "CAMBRIDGE",
                "county": "CAMBRIDGESHIRE",
                "latitude": "52.17513275",
                "longitude": "0.140753239",
                "postcode": "CB2 0QQ",
                # "geocode_coordinates": "",
                "active": "",
                "published_at": "",
                "paediatric_diabetes_unit": "",
                "trust": "",
                "local_health_board": "",
                "integrated_care_board": "",
                "nhs_england_region": "",
                "openuk_network": "",
                "london_borough": "",
                "country": "",
            },
            response_only=True,
        )
    ]
)
class OrganisationSerializer(serializers.ModelSerializer):
    # paediatric_diabetes_unit = serializers.SlugRelatedField(
    #     many=True, read_only=True, slug_field="pz_code"
    # )
    trust = serializers.SlugRelatedField(many=False, read_only=True, slug_field="name")
    local_health_board = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    integrated_care_board = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    nhs_england_region = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    openuk_network = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    london_borough = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )
    country = serializers.SlugRelatedField(
        many=False, read_only=True, slug_field="name"
    )

    class Meta:
        model = Organisation
        fields = [
            "ods_code",
            "name",
            "website",
            "address1",
            "address2",
            "address3",
            "telephone",
            "city",
            "county",
            "latitude",
            "longitude",
            "postcode",
            # "geocode_coordinates",
            "active",
            "published_at",
            # "paediatric_diabetes_unit",
            "trust",
            "local_health_board",
            "integrated_care_board",
            "nhs_england_region",
            "openuk_network",
            "london_borough",
            "country",
        ]
