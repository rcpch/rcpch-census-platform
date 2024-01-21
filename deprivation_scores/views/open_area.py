from django.apps import apps
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    serializers,  # serializers here required for drf-spectacular @extend_schema
)

from rest_framework.views import APIView, Response

from ..filtersets import DataZoneFilter

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

LSOA = apps.get_model("deprivation_scores", "LSOA")
LocalAuthority = apps.get_model("deprivation_scores", "LocalAuthority")
DataZone = apps.get_model("deprivation_scores", "DataZone")
SOA = apps.get_model("deprivation_scores", "SOA")

from ..serializers import LocalAuthorityDistrictSerializer
from ..serializers import LSOASerializer
from ..serializers import SOASerializer
from ..serializers import DataZoneSerializer


@extend_schema(
    request=LocalAuthorityDistrictSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/local_authority_districts/1/",
                    external_value="external value",
                    value={
                        "local_authority_district_code": "E06000002",
                        "local_authority_district_name": "Middlesbrough",
                        "year": 2019,
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
class LocalAuthorityDistrictViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Local Authority Districts (2019) across England, Scotland and Wales.

    Filter Parameters:

    `year`

    `local_authority_district_code`

    `local_authority_district_name`

    If none are passed, a list is returned.

    """

    queryset = LocalAuthority.objects.all().order_by("-local_authority_district_code")
    serializer_class = LocalAuthorityDistrictSerializer
    filterset_fields = [
        "local_authority_district_code",
        "local_authority_district_name",
        "year",
    ]
    filter_backends = (DjangoFilterBackend,)


@extend_schema(request=LSOASerializer)
class LSOAViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of LSOAs in England and Wales.

    Filter Parameters:

    `year`

    `lsoa_code`

    `lsoa_name`

    If none are passed, a list is returned.

    """

    queryset = LSOA.objects.all().order_by("-lsoa_code")
    serializer_class = LSOASerializer
    filterset_fields = ["lsoa_code", "lsoa_name", "year"]
    filter_backends = (DjangoFilterBackend,)


@extend_schema(
    request=SOASerializer,
)
class SOAViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of SOAs in Northern Ireland.

    Filter Parameters:

    `year`

    `soa_code`

    `soa_name`

    If none are passed, a list is returned.
    """

    queryset = SOA.objects.all().order_by("-soa_code")
    serializer_class = SOASerializer
    filterset_fields = ["year", "soa_code", "soa_name"]
    filter_backends = (DjangoFilterBackend,)


@extend_schema(
    request=DataZoneSerializer,
)
class DataZoneViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of all Scottish data zones (2011) and their associated local authority district.

    Filter Parameters:

    `year`

    `code`

    `name`

    If none are passed, a list is returned.
    """

    queryset = DataZone.objects.all().order_by("code")
    serializer_class = DataZoneSerializer
    filterset_class = DataZoneFilter
    filter_backends = (DjangoFilterBackend,)
