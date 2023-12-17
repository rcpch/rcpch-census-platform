from django.apps import apps
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import (
    viewsets,
    serializers,  # serializers here required for drf-spectacular @extend_schema
)
from rest_framework.views import APIView, Response
from rest_framework.exceptions import ParseError

from drf_spectacular.utils import (
    extend_schema,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

from ..filtersets import (
    EnglishIndexMultipleDeprivationFilter,
    WelshIndexMultipleDeprivationFilter,
    ScottishIndexMultipleDeprivationFilter,
    NorthernIrelandIndexMultipleDeprivationFilter,
)

from ..general_functions import (
    lsoa_for_postcode,
    regions_for_postcode,
    is_valid_postcode,
    quantile_for_rank,
)

EnglishIndexMultipleDeprivation = apps.get_model(
    "rcpch_census_platform", "EnglishIndexMultipleDeprivation"
)
WelshIndexMultipleDeprivation = apps.get_model(
    "rcpch_census_platform", "WelshIndexMultipleDeprivation"
)
ScottishIndexMultipleDeprivation = apps.get_model(
    "rcpch_census_platform", "ScottishIndexMultipleDeprivation"
)
NorthernIrelandIndexMultipleDeprivation = apps.get_model(
    "rcpch_census_platform", "NorthernIrelandIndexMultipleDeprivation"
)

LSOA = apps.get_model("rcpch_census_platform", "LSOA")
DataZone = apps.get_model("rcpch_census_platform", "DataZone")
SOA = apps.get_model("rcpch_census_platform", "SOA")

from ..serializers import (
    EnglishIndexMultipleDeprivationSerializer,
    WelshIndexMultipleDeprivationSerializer,
    ScottishIndexMultipleDeprivationSerializer,
    NorthernIrelandIndexMultipleDeprivationSerializer,
)


class EnglishIndexMultipleDeprivationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of all English LSOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2019).

    Filter Parameters:

    `lsoa_code`

    If none are passed, a list is returned
    """

    queryset = EnglishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = EnglishIndexMultipleDeprivationSerializer
    filterset_class = EnglishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


@extend_schema(
    request=WelshIndexMultipleDeprivationSerializer,
)
class WelshMultipleDeprivationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Welsh LSOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2019).

    Filter Parameters:

    `lsoa_code`

    If none are passed, a list is returned.
    """

    queryset = WelshIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = WelshIndexMultipleDeprivationSerializer
    filterset_class = WelshIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


@extend_schema(
    request=ScottishIndexMultipleDeprivationSerializer,
)
class ScottishMultipleDeprivationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of Scottish data zones with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2017).

    Filter Parameters:

    `data_zone_code`

    If none are passed, a list is returned.
    """

    queryset = ScottishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = ScottishIndexMultipleDeprivationSerializer
    filterset_class = ScottishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


@extend_schema(
    request=NorthernIrelandIndexMultipleDeprivationSerializer,
)
class NorthernIrelandMultipleDeprivationViewSet(viewsets.ReadOnlyModelViewSet):
    """
    This endpoint returns a list of all Northern Ireland SOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2020).

    Filter Parameters:

    `soa_code`

    If none are passed, a list is returned.
    """

    queryset = NorthernIrelandIndexMultipleDeprivation.objects.all().order_by(
        "-imd_rank"
    )
    serializer_class = NorthernIrelandIndexMultipleDeprivationSerializer
    filterset_class = NorthernIrelandIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


class UKIndexMultipleDeprivationView(APIView):
    english_serializer_class = EnglishIndexMultipleDeprivationSerializer
    welsh_serializer_class = WelshIndexMultipleDeprivationSerializer
    scottish_serializer_class = ScottishIndexMultipleDeprivationSerializer
    northern_ireland_serializer_class = (
        NorthernIrelandIndexMultipleDeprivationSerializer
    )

    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="postcode",
                description="Postcode",
                required=True,
                type=OpenApiTypes.STR,
                examples=[
                    OpenApiExample(
                        name="Low Deprivation",
                        description="Example low deprivation postcode",
                        value="SW1A 1AA",
                    ),
                    OpenApiExample(
                        name="High Deprivation",
                        description="Example high deprivation postcode",
                        value="CO15 2DQ",
                    ),
                ],
            ),
        ],
        responses=PolymorphicProxySerializer(
            component_name="UKIndexofMultipleDeprivation",
            # on 200 one of the UK Serializers is returned
            serializers=[
                EnglishIndexMultipleDeprivationSerializer,
                WelshIndexMultipleDeprivationSerializer,
                ScottishIndexMultipleDeprivationSerializer,
                NorthernIrelandIndexMultipleDeprivationSerializer,
            ],
            resource_type_field_name="type",
        ),
    )
    def get(self, request):
        """
        This endpoint returns an index of multiple deprivations against a postcode, from either England, Wales, Scotland or Northern Ireland.

        Parameters:

        `postcode`: string **[Mandatory]**

        """
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            if is_valid_postcode(postcode=post_code):
                lsoa_object = lsoa_for_postcode(postcode=post_code)

                if lsoa_object["lsoa"]:
                    lsoa_code = lsoa_object["lsoa"]
                    if lsoa_object["country"] == "England":
                        lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
                        imd = EnglishIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa
                        ).get()
                        response = self.english_serializer_class(
                            instance=imd, context={"request": request}
                        )
                    elif lsoa_object["country"] == "Wales":
                        lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
                        imd = WelshIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa
                        ).get()
                        response = self.welsh_serializer_class(
                            instance=imd, context={"request": request}
                        )
                    elif lsoa_object["country"] == "Scotland":
                        lsoa = DataZone.objects.filter(data_zone_code=lsoa_code).get()
                        imd = ScottishIndexMultipleDeprivation.objects.filter(
                            data_zone=lsoa
                        ).get()
                        response = self.scottish_serializer_class(
                            instance=imd, context={"request": request}
                        )
                    elif lsoa_object["country"] == "Northern Ireland":
                        lsoa = SOA.objects.filter(soa_code=lsoa_code).get()
                        imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                            soa=lsoa
                        ).get()
                        response = self.northern_ireland_serializer_class(
                            instance=imd, context={"request": request}
                        )
                    else:
                        raise ParseError("No valid country supplied.", code=400)
            else:
                # postcode not valid
                raise ParseError("Invalid postcode supplied.", code=400)
        else:
            raise ParseError("Postcode not supplied.", code=400)

        return Response(response.data)


class UKIndexMultipleDeprivationQuantileView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(
                name="postcode",
                description="Postcode",
                required=True,
                type=OpenApiTypes.STR,
            ),
            OpenApiParameter(
                name="quantile",
                description="Quantile",
                required=True,
                type=OpenApiTypes.INT,  # Literal[2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20],
                enum=[2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20],
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Valid Response",
                examples=[
                    OpenApiExample(
                        "/index_of_multiple_deprivation_quantile?postcode=SW1A1AA&quantile=10",
                        external_value="external value",
                        value={
                            "rank": 24862,
                            "requested_quantile": 10,
                            "requested_quantile_name": "decile",
                            "data_quantile": 8,
                            "country": "england",
                            "error": None,
                        },
                        response_only=True,
                    ),
                    OpenApiExample(
                        "/index_of_multiple_deprivation_quantile?postcode=B346DX&quantile=2",
                        external_value="external value",
                        value={
                            "result": {
                                "rank": 9304,
                                "requested_quantile": 2,
                                "requested_quantile_name": "median",
                                "data_quantile": 1,
                                "country": "england",
                                "error": None,
                            }
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        This endpoint returns an Index of Multiple Deprivations against a postcode, from either England, Wales, Scotland or Northern Ireland.

        Parameters:

        `postcode`: string **[Mandatory]**

        `quantile`: integer **[Mandatory]**, one of [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]
        """
        post_code = self.request.query_params.get("postcode", None)
        requested_quantile = self.request.query_params.get("quantile", None)
        if post_code:
            if is_valid_postcode(postcode=post_code):
                lsoa_object = lsoa_for_postcode(postcode=post_code)
                if lsoa_object["lsoa"]:
                    lsoa_code = lsoa_object["lsoa"]
                    if lsoa_object["country"] == "England":
                        lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
                        imd = EnglishIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa
                        ).get()
                        data = quantile_for_rank(
                            rank=imd.imd_rank,
                            requested_quantile=requested_quantile,
                            country="england",
                        )
                        response = Response({"result": data})
                    elif lsoa_object["country"] == "Wales":
                        lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
                        imd = WelshIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa
                        ).get()
                        data = quantile_for_rank(
                            rank=imd.imd_rank,
                            requested_quantile=requested_quantile,
                            country="wales",
                        )
                        response = Response({"result": data})
                    elif lsoa_object["country"] == "Scotland":
                        lsoa = DataZone.objects.filter(data_zone_code=lsoa_code).get()
                        imd = ScottishIndexMultipleDeprivation.objects.filter(
                            data_zone=lsoa
                        ).get()
                        data = quantile_for_rank(
                            rank=imd.imd_rank,
                            requested_quantile=requested_quantile,
                            country="scotland",
                        )
                        response = Response({"result": data})
                    elif lsoa_object["country"] == "Northern Ireland":
                        lsoa = SOA.objects.filter(soa_code=lsoa_code).get()
                        imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                            soa=lsoa
                        ).get()
                        data = quantile_for_rank(
                            rank=imd.imd_rank,
                            requested_quantile=requested_quantile,
                            country="northern_ireland",
                        )
                        response = Response({"result": data})
                    else:
                        raise ParseError("No valid country supplied.", code=400)
            else:
                # postcode not valid
                raise ParseError("Invalid postcode supplied.", code=400)
        else:
            raise ParseError("Postcode not supplied.", code=400)

        return Response(response.data)
