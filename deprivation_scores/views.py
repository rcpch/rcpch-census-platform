from http import HTTPStatus
from rest_framework import (
    viewsets,
    serializers,  # serializers here required for drf-spectacular @extend_schema
    mixins,
)
from rest_framework.decorators import api_view
from rest_framework.exceptions import ParseError, NotFound
from rest_framework.response import Response
from rest_framework.views import APIView
from django_filters.rest_framework import DjangoFilterBackend

from drf_spectacular.utils import (
    extend_schema,
    extend_schema_view,
    OpenApiParameter,
    OpenApiExample,
    OpenApiResponse,
    PolymorphicProxySerializer,
)
from drf_spectacular.types import OpenApiTypes

from .general_functions import QUANTILE_NAMES, quantile_for_rank

from .filter_sets import (
    EnglishIndexMultipleDeprivationFilter,
    WelshIndexMultipleDeprivationFilter,
    ScottishIndexMultipleDeprivationFilter,
    NorthernIrelandIndexMultipleDeprivationFilter,
    GreenSpaceFilter,
)

from .models import (
    LocalAuthority,
    LSOA,
    GreenSpace,
    DataZone,
    SOA,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
    PopulationDensity,
)
from .serializers import (
    LocalAuthorityDistrictSerializer,
    LSOASerializer,
    GreenSpaceSerializer,
    DataZoneSerializer,
    SOASerializer,
    EnglishIndexMultipleDeprivationSerializer,
    WelshIndexMultipleDeprivationSerializer,
    ScottishIndexMultipleDeprivationSerializer,
    NorthernIrelandIndexMultipleDeprivationSerializer,
    PopulationDensitySerializer,
)
from .general_functions import (
    lsoa_for_postcode,
    regions_for_postcode,
)
import logging


logger = logging.getLogger(__name__)


@extend_schema(
    request=LocalAuthorityDistrictSerializer,
    parameters=[
        OpenApiParameter(
            name="year",
            description="Year (must be one of 2011, 2019, or 2024)",
            required=True,
            type=OpenApiTypes.INT,
        ),
    ],
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
class LocalAuthorityDistrictViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    This endpoint returns a list of Local Authority Districts across England, Scotland and Wales.
    It contains datasets for:
    2011 - 32 Scotland,
    2019 - 339 England and Wales (317 in England, 22 in Wales - the 11 Northern Irish Local Authorities are not included here)
    2024 - 318 England and Wales

    Filter Parameters:

    `year`

    `local_authority_district_code`

    `local_authority_district_name`

    The year parameter is mandatory.

    """

    queryset = LocalAuthority.objects.all().order_by("-local_authority_district_code")
    serializer_class = LocalAuthorityDistrictSerializer
    filterset_fields = [
        "local_authority_district_code",
        "local_authority_district_name",
        "year",
    ]
    filter_backends = [DjangoFilterBackend]

    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year")
        if year is not None:
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                raise ParseError("Year must be an integer.", code=400)
            if year_int not in (2011, 2019, 2024):
                raise ParseError("Year must be one of: 2011, 2019, 2024.", code=400)
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="year",
                description="Year (must be one of 2011 or 2021) - defaults to 2011 if not supplied",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ]
    )
)
@extend_schema(request=LSOASerializer)
class LSOAViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    This endpoint returns an LSOA against a given LSOA code.
    There are datasets for 2011 and 2021.

    Filter Parameters:

    `year`

    `lsoa_code`

    `lsoa_name`

    If none are passed, a list is returned.

    """

    queryset = LSOA.objects.all().order_by("-lsoa_code")
    serializer_class = LSOASerializer
    filterset_fields = ["lsoa_code", "lsoa_name", "year"]
    filter_backends = [DjangoFilterBackend]
    lookup_field = "lsoa_code"

    def retrieve(self, request, *args, **kwargs):
        # accept code from query param or URL (lookup_field)
        lsoa_code = request.query_params.get("lsoa_code") or kwargs.get(
            self.lookup_field
        )
        if not lsoa_code:
            return super().retrieve(request, *args, **kwargs)

        year = request.query_params.get("year")
        if year is not None:
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                raise ParseError("Year must be an integer.", code=400)
            if year_int not in (2011, 2021):
                raise ParseError("Year must be one of: 2011, 2021.", code=400)
            qs = self.filter_queryset(self.get_queryset()).filter(
                lsoa_code=lsoa_code, year=year_int
            )
            instance = qs.first()
        else:
            year = 2011
            qs = (
                self.filter_queryset(self.get_queryset())
                .filter(lsoa_code=lsoa_code, year=year)
                .order_by("-year")
            )
            instance = qs.first()

        if not instance:
            raise NotFound("LSOA not found for the supplied code/year.")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    request=SOASerializer,
    parameters=[
        OpenApiParameter("soa_code", type=OpenApiTypes.STR, required=False),
        OpenApiParameter("soa_name", type=OpenApiTypes.STR, required=False),
        OpenApiParameter("year", type=OpenApiTypes.INT, required=False),
    ],
)
class SOAViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    This endpoint returns a a Super Output Areas in Northern Ireland, by SOA code.
    This is a 2001 only dataset and is used for the Northern Ireland Index of Multiple Deprivation.
    NOTE: One of `soa_code` or `soa_name` query parameters must be provided.
    """

    queryset = SOA.objects.all().order_by("-soa_code")
    serializer_class = SOASerializer
    filterset_fields = ["year", "soa_code", "soa_name"]
    filter_backends = [DjangoFilterBackend]

    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year")
        soa_code = request.query_params.get("soa_code")
        soa_name = request.query_params.get("soa_name")
        if year is not None:
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                raise ParseError("Year must be an integer.", code=400)
            if year_int != 2001:
                raise ParseError("Year must be one of: 2001.", code=400)
        if not soa_code and not soa_name:
            raise ParseError(
                "One of `soa_code` or `soa_name` query parameters must be provided.",
                code=400,
            )
        return super().list(request, *args, **kwargs)


@extend_schema(
    request=GreenSpaceSerializer,
)
class GreenSpaceViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """

    This endpoint returns data relating to green space and access to green space against 2019 Local Authority Districts for England, Wales and Scotland.
    The data includes total addresses, addresses with private outdoor space, percentage of addresses with private outdoor space and average size of private outdoor space.
    """

    queryset = GreenSpace.objects.all().order_by("-total_addresses_count")
    serializer_class = GreenSpaceSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_class = GreenSpaceFilter


@extend_schema(
    request=DataZoneSerializer,
)
class DataZoneViewSet(mixins.ListModelMixin, viewsets.GenericViewSet):
    """
    This endpoint returns Scottish data zones (2011) and their associated local authority district by name or code. NOTE: One of `data_zone_code` or `data_zone_name` query parameters must be provided.

    Filter Parameters:

    `year`

    `data_zone_code`

    `data_zone_name`

    """

    queryset = DataZone.objects.all().order_by("data_zone_code")
    serializer_class = DataZoneSerializer
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["year", "data_zone_code", "data_zone_name"]

    def list(self, request, *args, **kwargs):
        year = request.query_params.get("year")
        data_zone_code = request.query_params.get("data_zone_code")
        data_zone_name = request.query_params.get("data_zone_name")
        if year is not None:
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                raise ParseError("Year must be an integer.", code=400)
            if year_int != 2011:
                raise ParseError("Year must be one of: 2011.", code=400)
        else:
            year_int = 2011
        if data_zone_code is None and data_zone_name is None:
            raise ParseError(
                "One of `data_zone_code` or `data_zone_name` query parameters must be provided.",
                code=400,
            )
        return super().list(request, *args, **kwargs)


@extend_schema_view(
    retrieve=extend_schema(
        parameters=[
            OpenApiParameter(
                name="year",
                description="Year of Index of Multiple Deprivation dataset to use (2019 or 2025) - defaults to 2019 if not supplied",
                required=False,
                type=OpenApiTypes.INT,
            ),
        ]
    )
)
@extend_schema(
    request=EnglishIndexMultipleDeprivationSerializer,
)
class EnglishIndexMultipleDeprivationViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    This endpoint returns the extended English Index of Multiple Deprivation data for a given LSOA.

    Filter Parameters:

    `lsoa_code`
    `year` (2019 or 2025 - defaults to 2019 if not supplied)

    If none are passed, a list is returned
    """

    queryset = EnglishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = EnglishIndexMultipleDeprivationSerializer
    filterset_class = EnglishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]
    lookup_field = "lsoa__lsoa_code"
    lookup_url_kwarg = "lsoa_code"

    def retrieve(self, request, *args, **kwargs):
        lsoa_code = kwargs.get(self.lookup_url_kwarg)
        year = request.query_params.get("year")
        if year is not None:
            try:
                year_int = int(year)
            except (TypeError, ValueError):
                raise ParseError("Year must be an integer.", code=400)
            if year_int not in (2019, 2025):
                raise ParseError("Year must be one of: 2019, 2025.", code=400)
            qs = self.filter_queryset(self.get_queryset()).filter(
                lsoa__lsoa_code=lsoa_code, year=year_int
            )
            instance = qs.first()
        else:
            year = 2019
            qs = self.filter_queryset(self.get_queryset()).filter(
                lsoa__lsoa_code=lsoa_code, year=year
            )
            instance = qs.first()

        if not instance:
            raise NotFound("LSOA not found for the supplied code/year.")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    request=WelshIndexMultipleDeprivationSerializer,
)
class WelshMultipleDeprivationViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    This endpoint returns the extended Welsh Index of Multiple Deprivation data for a given LSOA (2011).

    """

    queryset = WelshIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = WelshIndexMultipleDeprivationSerializer
    filterset_class = WelshIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]
    lookup_field = "lsoa__lsoa_code"
    lookup_url_kwarg = "lsoa_code"

    def retrieve(self, request, *args, **kwargs):
        lsoa_code = kwargs.get("lsoa_code")
        print(lsoa_code)
        qs = self.filter_queryset(self.get_queryset()).filter(
            lsoa__lsoa_code=lsoa_code, lsoa__year=2011
        )
        instance = qs.first()

        if not instance:
            raise NotFound("LSOA not found for the supplied code.")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    request=ScottishIndexMultipleDeprivationSerializer,
)
class ScottishMultipleDeprivationViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
    """
    This endpoint returns the extended Scottish Index of Multiple Deprivation subscore ranks for all the associated deprivation domains (2017) for a given data zone.

    Filter Parameters:

    `data_zone_code`
    """

    queryset = ScottishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = ScottishIndexMultipleDeprivationSerializer
    filterset_class = ScottishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]
    lookup_field = "data_zone__data_zone_code"
    lookup_url_kwarg = "data_zone_code"

    def retrieve(self, request, *args, **kwargs):
        data_zone_code = kwargs.get(self.lookup_url_kwarg)
        qs = self.filter_queryset(self.get_queryset()).filter(
            data_zone__data_zone_code=data_zone_code
        )
        instance = qs.first()

        if not instance:
            raise NotFound("Data Zone not found for the supplied code.")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    request=NorthernIrelandIndexMultipleDeprivationSerializer,
)
class NorthernIrelandMultipleDeprivationViewSet(
    mixins.RetrieveModelMixin, viewsets.GenericViewSet
):
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
    lookup_field = "soa__soa_code"
    lookup_url_kwarg = "soa_code"

    def retrieve(self, request, *args, **kwargs):
        soa_code = kwargs.get(self.lookup_url_kwarg)
        qs = self.filter_queryset(self.get_queryset()).filter(soa__soa_code=soa_code)
        instance = qs.first()

        if not instance:
            raise NotFound("SOA not found for the supplied code.")

        serializer = self.get_serializer(instance)
        return Response(serializer.data)


@extend_schema(
    request=PopulationDensitySerializer,
)
class PopulationDensityViewSet(mixins.RetrieveModelMixin, viewsets.GenericViewSet):
    """
    This endpoint returns a the population density (2019) against a 2011 LSOA code.
    """

    queryset = PopulationDensity.objects.all()
    serializer_class = PopulationDensitySerializer
    filter_backends = [DjangoFilterBackend]
    lookup_field = "lsoa__lsoa_code"
    lookup_url_kwarg = "lsoa_code"

    def get_queryset(self):
        qs = super().get_queryset()
        return qs.filter(lsoa__year=2011)


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
        request=None,
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Valid Response",
                examples=[
                    OpenApiExample(
                        "/postcode?postcode=SW1A1AA",
                        external_value="external value",
                        value={
                            "postcode": "SW1A 1AA",
                            "quality": 1,
                            "eastings": 530047,
                            "northings": 179951,
                            "country": "England",
                            "nhs_ha": "London",
                            "longitude": -0.141588,
                            "latitude": 51.501009,
                            "european_electoral_region": "London",
                            "primary_care_trust": "Westminster",
                            "region": "London",
                            "lsoa": "Westminster 018A",
                            "msoa": "Westminster 018",
                            "incode": "1AA",
                            "outcode": "SW1A",
                            "parliamentary_constituency": "Cities of London and Westminster",
                            "admin_district": "Westminster",
                            "admin_county": None,
                            "admin_ward": "St James's",
                            "ced": None,
                            "ccg": "NHS Central London (Westminster)",
                            "nuts": "Westminster",
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        This is a proxy for postcodes.io, an api that looks up a given postcode
        and returns LSOA code, CCG code and other important codes information
        """
        postcode = request.query_params.get("postcode")
        logger.info("PostcodeView.get called with postcode=%s", postcode)
        if postcode:

            data = regions_for_postcode(postcode=postcode)
            status = data["status"]

            response = data["response"]
            if status == "error":
                logger.warning("Postcode lookup error for %s: %s", postcode, response)
                raise ParseError(response, code=400)
            elif status == "terminated_postcode":
                logger.info("Postcode terminated for %s", postcode)
                return Response(response, status=HTTPStatus.GONE)

            logger.debug("Postcode lookup successful for %s", postcode)
            return Response(response)
        else:
            logger.warning("PostcodeView.get called without postcode")
            raise ParseError(detail="Postcode cannot be blank")


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
            OpenApiParameter(
                name="year",
                description="Year of Index of Multiple Deprivation dataset to use",
                required=False,
                type=OpenApiTypes.INT,
                examples=[
                    OpenApiExample(
                        name="2017",
                        description="Use 2017 dataset for Northern Ireland",
                        value=2017,
                    ),
                    OpenApiExample(
                        name="2019",
                        description="Use 2019 dataset for England and Wales",
                        value=2019,
                    ),
                    OpenApiExample(
                        name="2020",
                        description="Use 2020 dataset for Scotland",
                        value=2020,
                    ),
                    OpenApiExample(
                        name="2025",
                        description="Use 2025 dataset for England and Wales",
                        value=2025,
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
        year = self.request.query_params.get("year", None)
        if post_code:
            if year:
                if int(year) == 2025:
                    lsoa_year = 2021
                elif int(year) in [2019, 2017, 2020]:
                    lsoa_year = 2011
                else:
                    logger.warning("Invalid year supplied: %s", year)
                    raise ParseError("Invalid year supplied.", code=400)
            else:
                lsoa_year = 2011
            data = lsoa_for_postcode(
                postcode=post_code, lsoa_year=lsoa_year
            )  # this returns either the lsoa, soa or data zone code depending on country, though the key is called lsoa. the response also includes the country
            status = data["status"]
            response = data["response"]
            if status == "error":
                logger.warning("Postcode lookup error for %s: %s", post_code, response)
                raise ParseError(response, code=400)
            elif status == "terminated_postcode":
                logger.info("Postcode terminated for %s", post_code)
                return Response(response, status=HTTPStatus.GONE)

            lsoa_object = response

            if lsoa_object["lsoa"]:
                lsoa_code = lsoa_object["lsoa"]
                if lsoa_object["country"] == "England":
                    if year is None:
                        year = 2019
                    if int(year) in [2019, 2025]:
                        if int(year) == 2025:
                            lsoa = LSOA.objects.filter(
                                lsoa_code=lsoa_code, year=2021
                            ).get()
                        elif int(year) == 2019:
                            lsoa = LSOA.objects.filter(
                                lsoa_code=lsoa_code, year=2011
                            ).get()
                        else:
                            logger.warning("Invalid year supplied: %s", year)
                            raise ParseError(  # fallback, should not be hit
                                "Year must be 2019 or 2025 for England.", code=400
                            )
                        imd = EnglishIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa, year=int(year)
                        ).get()
                    else:
                        logger.warning("Invalid year supplied: %s", year)
                        raise ParseError(
                            "Year must be 2019 or 2025 for England.", code=400
                        )
                    response = self.english_serializer_class(
                        instance=imd, context={"request": request}
                    )
                elif lsoa_object["country"] == "Wales":
                    if year is None:
                        year = 2019
                    if int(year) != 2019:
                        logger.warning(
                            "Invalid year supplied for Wales IMD postcode request: %s",
                            year,
                        )
                        raise ParseError("Year must be 2019 for Wales.", code=400)
                    lsoa = LSOA.objects.filter(lsoa_code=lsoa_code, year=2011).get()
                    imd = WelshIndexMultipleDeprivation.objects.filter(
                        lsoa=lsoa, year=2019
                    ).get()
                    response = self.welsh_serializer_class(
                        instance=imd, context={"request": request}
                    )
                elif lsoa_object["country"] == "Scotland":
                    if year is None:
                        year = 2020
                    if int(year) != 2020:
                        raise ParseError("Year must be 2020 for Scotland.", code=400)
                    lsoa = DataZone.objects.filter(
                        data_zone_code=lsoa_code, year=2011
                    ).get()
                    imd = ScottishIndexMultipleDeprivation.objects.filter(
                        data_zone=lsoa, year=2020
                    ).get()
                    response = self.scottish_serializer_class(
                        instance=imd, context={"request": request}
                    )
                elif lsoa_object["country"] == "Northern Ireland":
                    if year is None:
                        year = 2017
                    if int(year) != 2017:
                        raise ParseError(
                            "Year must be 2017 for Northern Ireland.", code=400
                        )
                    lsoa = SOA.objects.filter(soa_code=lsoa_code, year=2001).get()
                    imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                        soa=lsoa, year=2017
                    ).get()
                    response = self.northern_ireland_serializer_class(
                        instance=imd, context={"request": request}
                    )
                else:
                    logger.warning("No valid country found for postcode: %s", post_code)
                    raise ParseError("No valid country supplied.", code=400)
            else:
                # postcode not valid
                logger.warning("Invalid postcode supplied: %s", post_code)
                raise ParseError("Invalid postcode supplied.", code=400)
        else:
            logger.warning("No postcode supplied in request")
            raise ParseError("Postcode not supplied.", code=400)

        return Response(response.data)


MAX_BATCH_POSTCODES = 100


class UKIndexMultipleDeprivationQuantileView(APIView):
    # Serializers used to embed the full deprivation indices when requested
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
                description=(
                    "One or more UK postcodes. Supply a single postcode, a comma-separated "
                    "list (postcode=SW1A1AA,M1 5AL) or repeated parameters "
                    "(postcode=SW1A1AA&postcode=M1 5AL). The country of each postcode is "
                    "detected automatically, so postcodes from different UK nations can be "
                    f"mixed in one request. Maximum of {MAX_BATCH_POSTCODES} postcodes per request."
                ),
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
            OpenApiParameter(
                name="year",
                description=(
                    "Year of Index of Multiple Deprivation dataset to use. If omitted, each "
                    "postcode uses the default year for its nation (2019 England and Wales, "
                    "2020 Scotland, 2017 Northern Ireland)."
                ),
                required=False,
                type=OpenApiTypes.INT,
                examples=[
                    OpenApiExample(
                        name="2019",
                        description="Use 2019 dataset for England and Wales",
                        value=2019,
                    ),
                    OpenApiExample(
                        name="2025",
                        description="Use 2025 dataset for England and Wales",
                        value=2025,
                    ),
                    OpenApiExample(
                        name="2020",
                        description="Use 2020 dataset for Scotland",
                        value=2020,
                    ),
                ],
            ),
            OpenApiParameter(
                name="include_full_indices",
                description=(
                    "When true, each result also includes the full deprivation indices for "
                    "the postcode's area under the 'indices' key."
                ),
                required=False,
                type=OpenApiTypes.BOOL,
            ),
        ],
        responses={
            200: OpenApiResponse(
                response=OpenApiTypes.OBJECT,
                description="Valid Response",
                examples=[
                    OpenApiExample(
                        "Single postcode",
                        value={
                            "result": {
                                "rank": 24862,
                                "requested_quantile": 10,
                                "requested_quantile_name": "decile",
                                "data_quantile": 8,
                                "country": "england",
                                "year": 2019,
                                "error": None,
                            }
                        },
                        response_only=True,
                    ),
                    OpenApiExample(
                        "Multiple postcodes",
                        value={
                            "results": [
                                {
                                    "postcode": "SE1 7PB",
                                    "rank": 21865,
                                    "requested_quantile": 10,
                                    "requested_quantile_name": "decile",
                                    "data_quantile": 7,
                                    "country": "england",
                                    "year": 2019,
                                    "error": None,
                                },
                                {
                                    "postcode": "CF10 3NQ",
                                    "rank": 833,
                                    "requested_quantile": 10,
                                    "requested_quantile_name": "decile",
                                    "data_quantile": 5,
                                    "country": "wales",
                                    "year": 2019,
                                    "error": None,
                                },
                                {
                                    "postcode": "XX1 1XX",
                                    "rank": None,
                                    "requested_quantile": 10,
                                    "requested_quantile_name": "decile",
                                    "data_quantile": None,
                                    "country": None,
                                    "year": None,
                                    "error": "Could not get LSOA from postcode.",
                                },
                            ]
                        },
                        response_only=True,
                    ),
                ],
            ),
        },
    )
    def get(self, request):
        """
        This endpoint returns Index of Multiple Deprivation quantiles against one or more postcodes, from England, Wales, Scotland or Northern Ireland.

        The country of each postcode is detected automatically, so the endpoint is country-agnostic: a single request can mix postcodes from different UK nations and each result is calculated against that nation's deprivation dataset.

        A single postcode returns the original `{"result": ...}` response shape. Multiple postcodes return `{"results": [...]}` with one item per postcode in the order supplied; postcodes that cannot be resolved are returned with an `error` message instead of failing the whole request.

        Parameters:

        `postcode`: string or list of strings **[Mandatory]** - a single postcode, a comma-separated list, or repeated `postcode` parameters (maximum 100 per request)

        `quantile`: integer **[Mandatory]**, one of [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]

        `year`: integer **[Optional]**, year of the Index of Multiple Deprivation dataset to use. If omitted, each postcode uses the default year for its nation (2019 England and Wales, 2020 Scotland, 2017 Northern Ireland). If supplied, postcodes from nations that do not publish that dataset year are returned with an error.

        `include_full_indices`: boolean **[Optional]** - when true, each result also includes the full deprivation indices for the postcode's area under `indices`.
        """
        postcodes = self._postcodes_from_request()
        requested_quantile = self.request.query_params.get("quantile", None)
        year_param = self.request.query_params.get("year", None)
        include_full_indices = self._boolean_param(request, "include_full_indices")

        # Validate quantile parameter
        if requested_quantile is None:
            logger.warning("Quantile parameter missing for quantile view")
            raise ParseError("Quantile parameter is required.", code=400)

        valid_quantiles = [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]
        try:
            quantile = int(requested_quantile)
            if quantile not in valid_quantiles:
                raise ValueError
        except (ValueError, TypeError):
            logger.warning("Invalid quantile supplied: %s", requested_quantile)
            raise ParseError(
                f"{requested_quantile} is not a valid quantile. Must be one of {valid_quantiles}.",
                code=400,
            )

        if not postcodes:
            logger.warning("Postcode not supplied in quantile request")
            raise ParseError("Postcode not supplied.", code=400)

        if len(postcodes) > MAX_BATCH_POSTCODES:
            logger.warning(
                "Too many postcodes supplied in quantile request: %s", len(postcodes)
            )
            raise ParseError(
                f"Too many postcodes supplied. A maximum of {MAX_BATCH_POSTCODES} postcodes can be processed per request.",
                code=400,
            )

        # Validate and normalize the year before any postcode lookups
        year = None
        if year_param is not None:
            try:
                year = int(year_param)
            except (ValueError, TypeError):
                logger.warning("Invalid year supplied for quantile view: %s", year_param)
                raise ParseError("Invalid year supplied.", code=400)
            if year not in (2019, 2017, 2020, 2025):
                logger.warning("Invalid year supplied for quantile view: %s", year)
                raise ParseError("Invalid year supplied.", code=400)

        if len(postcodes) == 1:
            return self._single_postcode_response(
                postcode=postcodes[0],
                year=year,
                quantile=quantile,
                include_full_indices=include_full_indices,
            )

        return self._batch_response(
            postcodes=postcodes,
            year=year,
            quantile=quantile,
            include_full_indices=include_full_indices,
        )

    def _postcodes_from_request(self):
        """
        Extract the list of postcodes from the request.

        Accepts a single `postcode` parameter, comma-separated postcodes
        (`postcode=A,B`) and/or repeated parameters (`postcode=A&postcode=B`).
        """
        postcodes = []
        for value in self.request.query_params.getlist("postcode"):
            for part in value.split(","):
                postcode = part.strip()
                if postcode:
                    postcodes.append(postcode)
        return postcodes

    @staticmethod
    def _boolean_param(request, name):
        value = request.query_params.get(name, None)
        if value is None:
            return False
        return value.strip().lower() in ("true", "1", "yes")

    def _single_postcode_response(
        self, postcode, year, quantile, include_full_indices
    ):
        """
        Preserve the original single-postcode response behaviour: lookup errors
        return 400, terminated postcodes return 410 with the terminated payload,
        and success wraps the quantile data in a "result" object.
        """
        outcome = self._quantile_outcome_for_postcode(
            postcode=postcode,
            year=year,
            quantile=quantile,
            include_full_indices=include_full_indices,
        )
        if outcome["status"] == "error":
            raise ParseError(outcome["error"], code=400)
        if outcome["status"] == "terminated_postcode":
            return Response(outcome["response"], status=HTTPStatus.GONE)
        return Response({"result": outcome["result"]})

    def _batch_response(self, postcodes, year, quantile, include_full_indices):
        """
        Resolve each postcode independently and return one result item per
        postcode, in the order supplied. Postcodes that cannot be resolved are
        returned with an error message rather than failing the whole request.
        """
        results = []
        for postcode in postcodes:
            try:
                outcome = self._quantile_outcome_for_postcode(
                    postcode=postcode,
                    year=year,
                    quantile=quantile,
                    include_full_indices=include_full_indices,
                )
            except Exception:
                logger.exception(
                    "Unexpected error resolving postcode %s in batch quantile request",
                    postcode,
                )
                results.append(
                    self._batch_error_item(
                        postcode,
                        quantile,
                        "Error processing postcode.",
                        include_full_indices,
                    )
                )
                continue

            if outcome["status"] == "ok":
                results.append({"postcode": postcode, **outcome["result"]})
            elif outcome["status"] == "terminated_postcode":
                results.append(
                    self._batch_error_item(
                        postcode,
                        quantile,
                        "Terminated postcode.",
                        include_full_indices,
                    )
                )
            else:
                results.append(
                    self._batch_error_item(
                        postcode, quantile, outcome["error"], include_full_indices
                    )
                )
        return Response({"results": results})

    @staticmethod
    def _batch_error_item(postcode, quantile, error_message, include_full_indices):
        """
        Build a uniform error item so every entry in a batch response has the
        same shape for tabular rendering.
        """
        item = {
            "postcode": postcode,
            "rank": None,
            "requested_quantile": quantile,
            "requested_quantile_name": QUANTILE_NAMES.get(quantile),
            "data_quantile": None,
            "country": None,
            "year": None,
            "error": error_message,
        }
        if include_full_indices:
            item["indices"] = None
        return item

    @staticmethod
    def _error_outcome(message):
        return {
            "status": "error",
            "error": message,
            "result": None,
            "response": None,
        }

    def _quantile_outcome_for_postcode(
        self, postcode, year, quantile, include_full_indices
    ):
        """
        Resolve the deprivation quantile outcome for a single postcode.

        Returns a dict describing the outcome so batch requests can continue
        past individual postcode failures:

        - status "ok": `result` holds the quantile data (plus `indices` when
          `include_full_indices` is set)
        - status "error": `error` holds the error message
        - status "terminated_postcode": `response` holds the terminated postcode payload

        Unexpected exceptions (e.g. a missing IMD row) propagate to the caller.
        """
        # England 2025 IMD data is mapped to 2021 LSOAs; all other datasets use 2011 boundaries
        lsoa_year = 2021 if year == 2025 else 2011

        data = lsoa_for_postcode(postcode=postcode, lsoa_year=lsoa_year)
        status = data["status"]
        response = data["response"]

        if status == "error":
            logger.warning(
                "Postcode lookup returned error for %s: %s", postcode, response
            )
            return self._error_outcome(response)
        if status == "terminated_postcode":
            logger.info("Postcode terminated for %s", postcode)
            return {
                "status": "terminated_postcode",
                "error": None,
                "result": None,
                "response": response,
            }

        lsoa_object = response

        if not lsoa_object["lsoa"]:
            # postcode not valid
            logger.warning("Invalid postcode supplied: %s", postcode)
            return self._error_outcome("Invalid postcode supplied.")

        lsoa_code = lsoa_object["lsoa"]
        country = lsoa_object["country"]

        if country == "England":
            imd_year = year if year is not None else 2019
            if imd_year not in (2019, 2025):
                logger.warning(
                    "Year must be 2019 or 2025 for England (supplied=%s, postcode=%s)",
                    imd_year,
                    postcode,
                )
                return self._error_outcome("Year must be 2019 or 2025 for England.")
            lsoa = LSOA.objects.filter(
                lsoa_code=lsoa_code, year=2021 if imd_year == 2025 else 2011
            ).get()
            imd = EnglishIndexMultipleDeprivation.objects.filter(
                lsoa=lsoa, year=imd_year
            ).get()
            result = quantile_for_rank(
                rank=imd.imd_rank,
                requested_quantile=quantile,
                country="england",
                year=imd_year,
            )
        elif country == "Wales":
            imd_year = year if year is not None else 2019
            if imd_year != 2019:
                logger.warning(
                    "Year must be 2019 for Wales (supplied=%s, postcode=%s)",
                    imd_year,
                    postcode,
                )
                return self._error_outcome("Year must be 2019 for Wales.")
            lsoa = LSOA.objects.filter(lsoa_code=lsoa_code, year=2011).get()
            imd = WelshIndexMultipleDeprivation.objects.filter(
                lsoa=lsoa, year=imd_year
            ).get()
            result = quantile_for_rank(
                rank=imd.imd_rank,
                requested_quantile=quantile,
                country="wales",
                year=imd_year,
            )
        elif country == "Scotland":
            imd_year = year if year is not None else 2020
            if imd_year != 2020:
                logger.warning(
                    "Year must be 2020 for Scotland (supplied=%s, postcode=%s)",
                    imd_year,
                    postcode,
                )
                return self._error_outcome("Year must be 2020 for Scotland.")
            data_zone = DataZone.objects.filter(
                data_zone_code=lsoa_code, year=2011
            ).get()
            imd = ScottishIndexMultipleDeprivation.objects.filter(
                data_zone=data_zone, year=imd_year
            ).get()
            result = quantile_for_rank(
                rank=imd.imd_rank,
                requested_quantile=quantile,
                country="scotland",
                year=imd_year,
            )
        elif country == "Northern Ireland":
            imd_year = year if year is not None else 2017
            if imd_year != 2017:
                logger.warning(
                    "Year must be 2017 for Northern Ireland (supplied=%s, postcode=%s)",
                    imd_year,
                    postcode,
                )
                return self._error_outcome("Year must be 2017 for Northern Ireland.")
            soa = SOA.objects.filter(soa_code=lsoa_code, year=2001).get()
            imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                soa=soa, year=imd_year
            ).get()
            result = quantile_for_rank(
                rank=imd.imd_rank,
                requested_quantile=quantile,
                country="northern_ireland",
                year=imd_year,
            )
        else:
            logger.warning("No valid country found for postcode: %s", postcode)
            return self._error_outcome("No valid country supplied.")

        if include_full_indices:
            serializer_class = {
                "England": self.english_serializer_class,
                "Wales": self.welsh_serializer_class,
                "Scotland": self.scottish_serializer_class,
                "Northern Ireland": self.northern_ireland_serializer_class,
            }[country]
            result["indices"] = serializer_class(
                instance=imd, context={"request": self.request}
            ).data

        return {
            "status": "ok",
            "error": None,
            "result": result,
            "response": None,
        }
