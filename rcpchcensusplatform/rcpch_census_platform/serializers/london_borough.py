from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

LondonBorough = apps.get_model("rcpch_census_platform", "LondonBorough")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/london_borough/1/",
            value={
                "name": "",
                "gss_code": "",
                "hectares": "",
                "nonld_area": "",
                "ons_inner": "",
                "sub_2009": "",
                "sub_2006": "",
                "geom": "",
            },
            response_only=True,
        )
    ]
)
class LondonBoroughSerializer(serializers.ModelSerializer):
    class Meta:
        model = LondonBorough
        # depth = 1
        fields = [
            "name",
            "gss_code",
            "hectares",
            "nonld_area",
            "ons_inner",
            "sub_2009",
            "sub_2006",
            "geom",
        ]
