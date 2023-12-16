from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

from .models.entities import (
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
                "boundary_identifier": "E92000001",
                "name": "England",
                "welsh_name": "Lloegr",
                "bng_e": "394883",
                "bng_n": "370883",
                "long": "-2.07811",
                "lat": "53.235",
                "globalid": "f6b76559-3626-49b8-b50b-bd15efcb0505",
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
                "boundary_identifier": "E54000030",
                "name": "NHS South East London Integrated Care Board",
                "bng_e": "541305",
                "bng_n": "168583",
                "long": "0.029892",
                "lat": "51.3987",
                "globalid": "39c8c149-5e5f-4bfa-87ae-9b5daf7f9e08",
                "geom": "",
                "ods_code": "QKK",
                "publication_date": "15/03/2023",
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
