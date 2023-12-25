from django.apps import apps
from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample


PaediatricDiabetesUnit = apps.get_model(
    "rcpch_census_platform", "PaediatricDiabetesUnit"
)


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/paediatric_diabetes_unit/1/",
            value={
                "pz_code": "",
            },
            response_only=True,
        )
    ]
)
class PaediatricDiabetesUnitSerializer(serializers.ModelSerializer):
    class Meta:
        model = PaediatricDiabetesUnit
        # depth = 1
        fields = [
            "pz_code",
        ]
