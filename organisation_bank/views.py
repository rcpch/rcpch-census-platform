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

from .filter_sets import (
)

from .models import (
    Country,
    GeneralPractice,
    IntegratedCareBoard,
    LondonBorough,
    NHSEnglandRegion,
    OPENUKNetwork,
    Organisation,
    PaediatricDiabetesUnit
)
from .serializers import (
    CountrySerializer
)


@extend_schema(
    request=CountrySerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/country/1/",
                    external_value="external value",
                    value={
                        "boundary_identifier":""
                        "name":""
                        "welsh_name":""
                        "bng_e":""
                        "bng_n":""
                        "long":""
                        "lat":""
                        "globalid":""
                        "geom":""
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
class CountryViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Countries from the UK.

    Filter Parameters:

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

    queryset = Country.objects.all().order_by("-name")
    serializer_class = CountrySerializer
    filterset_fields = [
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