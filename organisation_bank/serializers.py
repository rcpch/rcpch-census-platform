from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models import (
    Country,
    GeneralPractice,
    IntegratedCareBoard,
    LondonBorough,
    NHSEnglandRegion,
    OPENUKNetwork,
    Organisation,
    PaediatricDiabetesUnit,
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/country/1/",
            value={
                "boundary_identifier": "",
                "name": "",
                "welsh_name": "",
                "bng_e": "",
                "bng_n": "",
                "long": "",
                "lat": "",
                "globalid": "",
                "geom": "",
            },
            response_only=True,
        )
    ]
)
class CountrySerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = Country
        fields = [
            "boundary_identifier",
            "name",
            "welsh_name",
            "bng_e",
            "bng_n",
            "long",
            "lat",
            "globalid",
            "geom",
        ]


class GeneralPracticeSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GeneralPractice
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
        ]


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/integrated_care_board/1/",
            value={
                "boundary_identifier": "",
                "name": "",
                "bng_e": "",
                "bng_n": "",
                "long": "",
                "lat": "",
                "globalid": "",
                "geom": "",
                "ods_code": "",
                "publication_date": "",
            },
            response_only=True,
        )
    ]
)
class IntegratedCareBoardSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = IntegratedCareBoard
        # depth = 1
        fields = [
            "boundary_identifier",
            "name",
            "bng_e",
            "bng_n",
            "long",
            "lat",
            "globalid",
            "geom",
            "ods_code",
            "publication_date",
        ]
