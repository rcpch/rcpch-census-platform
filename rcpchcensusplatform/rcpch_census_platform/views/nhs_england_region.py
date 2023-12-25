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
                    "/country/1/",
                    external_value="external value",
                    value={
                        "region_code": "",
                        "publication_date": "",
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
    `welsh_name`
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
        "welsh_name",
        "bng_e",
        "bng_n",
        "long",
        "lat",
        "globalid",
        "geom",
    ]
    filter_backends = [DjangoFilterBackend]
