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

from ..models import Trust
from ..serializers import TrustSerializer


@extend_schema(
    request=TrustSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/trust/1/",
                    external_value="external value",
                    value={
                        "ods_code": "",
                        "name": "",
                        "address_line_1": "",
                        "address_line_2": "",
                        "town": "",
                        "postcode": "",
                        "country": "",
                        "telephone": "",
                        "website": "",
                        "active": "",
                        "published_at": "",
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
class TrustViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Countries from the UK.

    Filter Parameters:

    `ods_code`
    `name`
    `address_line_1`
    `address_line_2`
    `town`
    `postcode`
    `country`
    `telephone`
    `website`
    `active`
    `published_at`

    If none are passed, a list is returned.

    """

    queryset = Trust.objects.all().order_by("-name")
    serializer_class = TrustSerializer
    filterset_fields = [
        "name",
        "address_line_1",
        "address_line_2",
        "town",
        "postcode",
        "country",
        "telephone",
        "website",
        "active",
        "published_at",
        "ods_code",
    ]
    filter_backends = (DjangoFilterBackend,)
