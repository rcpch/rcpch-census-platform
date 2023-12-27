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
Trust = apps.get_model("rcpch_census_platform", "Trust")
OPENUKNetwork = apps.get_model("rcpch_census_platform", "OPENUKNetwork")
PaediatricDiabetesUnit = apps.get_model(
    "rcpch_census_platform", "PaediatricDiabetesUnit"
)

from .country import CountrySerializer
from .integrated_care_board import IntegratedCareBoardSerializer
from .local_health_board import LocalHealthBoardSerializer
from .london_borough import LondonBoroughSerializer
from .nhs_england_region import NHSEnglandRegionSerializer
from .openuk_network import OPENUKNetworkSerializer
from .paediatric_diabetes_unit import PaediatricDiabetesUnitSerializer
from .trust import TrustSerializer


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
                "geocode_coordinates": "",
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
    # Serializes an organisation, nest in all related parent details
    trust = TrustSerializer()
    local_health_board = LocalHealthBoardSerializer()
    integrated_care_board = IntegratedCareBoardSerializer()
    nhs_england_region = NHSEnglandRegionSerializer()
    openuk_network = OPENUKNetworkSerializer()
    paediatric_diabetes_unit = PaediatricDiabetesUnitSerializer()
    london_borough = LondonBoroughSerializer()
    country = CountrySerializer()

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
            "geocode_coordinates",
            "active",
            "published_at",
            "paediatric_diabetes_unit",
            "trust",
            "local_health_board",
            "integrated_care_board",
            "nhs_england_region",
            "openuk_network",
            "london_borough",
            "country",
        ]
        depth = 1


class OrganisationNoParentsSerializer(serializers.ModelSerializer):
    # used to serialize all child organisations in the TrustSerializer
    # returns only ods_code and name
    class Meta:
        model = Organisation
        fields = ["ods_code", "name"]


class TrustWithNestedOrganisationsSerializer(serializers.ModelSerializer):
    # used to return all Trust fields as well as all related child organisations
    # nested in
    trust_organisations = OrganisationNoParentsSerializer(many=True, read_only=True)

    class Meta:
        model = Trust
        # depth = 1
        fields = [
            "ods_code",
            "name",
            "address_line_1",
            "address_line_2",
            "town",
            "postcode",
            "country",
            "telephone",
            "website",
            "active",
            "published_at",
            "trust_organisations",
        ]


class IntegratedCareBoardWithNestedOrganisationsSerializer(serializers.ModelSerializer):
    # used to return key ICB fields as well as all related child organisation names and ods_codes
    # nested in
    integrated_care_board_organisations = OrganisationNoParentsSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = IntegratedCareBoard
        # depth = 1
        fields = [
            "boundary_identifier",
            "name",
            "ods_code",
            "publication_date",
            "integrated_care_board_organisations",
        ]


class NHSEnglandRegionWithNestedOrganisationsSerializer(serializers.ModelSerializer):
    # used to return key ICB fields as well as all related child organisation names and ods_codes
    # nested in
    nhs_england_region_organisations = OrganisationNoParentsSerializer(
        many=True, read_only=True
    )

    class Meta:
        model = NHSEnglandRegion
        # depth = 1
        fields = [
            "region_code",
            "publication_date",
            "boundary_identifier",
            "name",
            "nhs_england_region_organisations",
        ]
