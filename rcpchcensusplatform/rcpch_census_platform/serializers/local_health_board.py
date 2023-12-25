from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


LocalHealthBoard = apps.get_model("rcpch_census_platform", "LocalHealthBoard")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/local_health_board/1/",
            value={
                "ods_code": "",
                "publication_date": "",
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
class LocalHealthBoardSerializer(serializers.ModelSerializer):
    class Meta:
        model = LocalHealthBoard
        # depth = 1
        fields = [
            "ods_code",
            "publication_date",
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