from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

from ..general_functions import (
    lsoa_for_postcode,
    regions_for_postcode,
    is_valid_postcode,
)

from rest_framework.decorators import api_view
from rest_framework.views import APIView, Response
from rest_framework.exceptions import ParseError


# custom views / endpoints
class PostcodeView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="postcode",
                description="Postcode for postcodes.io",
                required=True,
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample(
                        name="Buckingham Palace",
                        value="SW1A 1AA",
                    ),
                    OpenApiExample(
                        name="Great Ormond Street Hospital",
                        value="WC1N 3JH",
                    ),
                ],
            ),
        ],
    )
    def get(self, request):
        """
        This is a proxy for postcodes.io, an api that looks up a given postcode
        and returns LSOA code, CCG code and other important codes information
        """
        postcode = request.query_params.get("postcode")
        if postcode:
            response = regions_for_postcode(postcode=postcode)
            return Response(response)
        else:
            raise ParseError(detail="Postcode cannot be blank")
