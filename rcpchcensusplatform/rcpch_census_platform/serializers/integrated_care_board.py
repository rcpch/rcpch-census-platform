from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

IntegratedCareBoard = apps.get_model("rcpch_census_platform", "IntegratedCareBoard")


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
class IntegratedCareBoardSerializer(serializers.ModelSerializer):
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