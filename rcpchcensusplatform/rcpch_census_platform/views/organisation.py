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

from ..models import Organisation
from ..serializers import OrganisationSerializer


@extend_schema(
    request=OrganisationSerializer,
    responses={
        200: OpenApiResponse(
            response=OpenApiTypes.OBJECT,
            description="Valid Response",
            examples=[
                OpenApiExample(
                    "/organisation/1/",
                    external_value="external value",
                    value={
                        "ods_code": "RGT01",
                        "name": "ADDENBROOKE'S HOSPITAL",
                        "website": "https://www.cuh.nhs.uk/",
                        "address1": "HILLS ROAD",
                        "address2": "",
                        "address3": "",
                        "telephone": "01223 245151",
                        "city": "CAMBRIDGE",
                        "county": "CAMBRIDGESHIRE",
                        "latitude": "52.17513275",
                        "longitude": "0.140753239",
                        "postcode": "CB2 0QQ",
                        "active": "",
                        "published_at": "",
                        "trust": "",
                        "local_health_board": "",
                        "integrated_care_board": "",
                        "nhs_england_region": "",
                        "openuk_network": "",
                        "london_borough": "",
                        "country": "",
                    },
                    response_only=True,
                ),
            ],
        ),
    },
)
class OrganisationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of NHS Organisations (Acute or Community Hospitals) from the UK.

    Filter Parameters:

    `ods_code`
    `name`
    `website`
    `address1`
    `address2`
    `address3`
    `telephone`
    `city`
    `county`
    `latitude`
    `longitude`
    `postcode`
    `active`
    `published_at`
    `trust`
    `local_health_board`
    `integrated_care_board`
    `nhs_england_region`
    `openuk_network`
    `london_borough`
    `country`

    If none are passed, a list is returned.

    """

    queryset = Organisation.objects.all().order_by("name")
    serializer_class = OrganisationSerializer
    filterset_fields = [
        "ods_code",
        "name",
        "website",
        "address1",
        "address2",
        "address3",
        "telephone",
        "city",
        "county",
        "latitude",
        "longitude",
        "postcode",
        "active",
        "published_at",
        "paediatric_diabetes_unit",
        "trust",
        "local_health_board",
        "integrated_care_board",
        "nhs_england_region",
        "openuk_network",
        "london_borough",
        "country",
    ]
    filter_backends = [DjangoFilterBackend]
