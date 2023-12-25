from rest_framework import (
    viewsets,
    serializers,  # serializers here required for drf-spectacular @extend_schema
)
from rest_framework.decorators import api_view
from rest_framework.views import APIView, Response
from rest_framework.exceptions import ParseError
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

from ..models import NHSEnglandRegion
from ..serializers import NHSEnglandRegionSerializer


@extend_schema(
    request=NHSEnglandRegionSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/nhs_england_region/1/",
                    external_value="external value",
                    value={
                        "region_code": "Y58",
                        "publication_date": "2022-07-30",
                        "boundary_identifier": "E40000006",
                        "name": "South West",
                        "bng_e": 285015,
                        "bng_n": 102567,
                        "long": -3.63343,
                        "lat": 50.8112,
                        "globalid": "4e8906ed-a19e-49ac-a111-3474937655e9",
                        "geom": "SRID=27700;MULTIPOLYGON (((87767.5686999997 8868.28480000049, 89125.5478999997 ...",
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
class NHSEnglandRegionViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Countries from the UK.

    Filter Parameters:

    `region_code`
    `publication_date`
    `boundary_identifier`
    `name`
    `bng_e`
    `bng_n`
    `long`
    `lat`
    `globalid`
    `geom`

    If none are passed, a list is returned.

    """

    queryset = NHSEnglandRegion.objects.all().order_by("-name")
    serializer_class = NHSEnglandRegionSerializer
    filterset_fields = [
        "region_code",
        "publication_date",
        "boundary_identifier",
        "name",
        "bng_e",
        "bng_n",
        "long",
        "lat",
        "globalid",
    ]
    filter_backends = (DjangoFilterBackend,)
