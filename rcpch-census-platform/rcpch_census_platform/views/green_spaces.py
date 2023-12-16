from django.apps import apps
from rest_framework.decorators import api_view
from rest_framework.views import APIView, Response
from rest_framework.exceptions import ParseError
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    serializers,  # serializers here required for drf-spectacular @extend_schema
)
from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)

GreenSpace = apps.get_model("rcpch_census_platform", "GreenSpace")

from ..serializers import GreenSpaceSerializer


@extend_schema(
    request=GreenSpaceSerializer,
)
class GreenSpaceViewSet(viewsets.ReadOnlyModelViewSet):
    """

    This endpoint returns a list of local authorities in the UK with data relating to green space and access to green space.

    """

    queryset = GreenSpace.objects.all().order_by("-total_addresses_count")
    serializer_class = GreenSpaceSerializer
