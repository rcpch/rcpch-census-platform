from rest_framework import viewsets, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.views import APIView, Response
from rest_framework import authentication, permissions
from rest_framework.exceptions import ParseError
from django_filters.rest_framework import DjangoFilterBackend
from requests import Request

from drf_spectacular.utils import extend_schema, OpenApiParameter

from .filter_sets import (
    DataZoneFilter,
    EnglishIndexMultipleDeprivationFilter,
    WelshIndexMultipleDeprivationFilter,
    ScottishIndexMultipleDeprivationFilter,
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
    NorthernIrelandIndexMultipleDepricationSerializer,
)
from .general_functions import (
    lsoa_for_postcode,
    regions_for_postcode,
    is_valid_postcode,
)


class LocalAuthorityDistrictViewSet(viewsets.ModelViewSet):
    """
    Returns a list of Local Authority Districts (2019) across England, Scotland and Wales
    Filter params include: "year","local_authority_district_code","local_authority_district_name"
    If none are passed, a list is returned
    """

    queryset = LocalAuthority.objects.all().order_by("-local_authority_district_code")
    serializer_class = LocalAuthorityDistrictSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = [
        "local_authority_district_code",
        "local_authority_district_name",
        "year",
    ]
    filter_backends = [DjangoFilterBackend]


class LSOAViewSet(viewsets.ModelViewSet):
    """
    Returns a list of LSOAs in England and Wales
    Filter params include: "year","lsoa_code","lsoa_name"
    If none are passed, a list is returned
    """

    queryset = LSOA.objects.all().order_by("-lsoa_code")
    serializer_class = LSOASerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["lsoa_code", "lsoa_name", "year"]
    filter_backends = [DjangoFilterBackend]


class SOAViewSet(viewsets.ModelViewSet):
    """
    Returns a list of SOAs in Northern Ireland
    Filter params include: "year","soa_code","soa_name"
    If none are passed, a list is returned
    """

    queryset = SOA.objects.all().order_by("-soa_code")
    serializer_class = SOASerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["year", "soa_code", "soa_name"]
    filter_backends = [DjangoFilterBackend]


class GreenSpaceViewSet(viewsets.ModelViewSet):
    """
    Returns a list of local authorities in the UK with data relating to green space and access to green space,
    """

    queryset = GreenSpace.objects.all().order_by("-total_addresses_count")
    serializer_class = GreenSpaceSerializer
    permission_classes = [permissions.IsAuthenticated]


class DataZoneViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all Scottish data zones (2011) and their associated local authority district
    Filter params include: "year","data_zone_code","data_zone_name"
    If none are passed, a list is returned
    """

    queryset = DataZone.objects.all().order_by("data_zone_code")
    serializer_class = DataZoneSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_class = DataZoneFilter
    filter_backends = [DjangoFilterBackend]


class EnglishIndexMultipleDeprivationViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all English LSOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2019).
    Filter params include: "lsoa_code"
    If none are passed, a list is returned
    """

    queryset = EnglishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = EnglishIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_class = EnglishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


class WelshMultipleDeprivationViewSet(viewsets.ModelViewSet):
    """
    Returns a list of Welsh LSOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2019).
    Filter params include: "lsoa_code"
    If none are passed, a list is returned
    """

    queryset = WelshIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = WelshIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_class = WelshIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


class ScottishMultipleDeprivationViewSet(viewsets.ModelViewSet):
    """
    Returns a list of Scottish data zones with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2017).
    Filter params include: "data_zone_code"
    If none are passed, a list is returned
    """

    queryset = ScottishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = ScottishIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_class = ScottishIndexMultipleDeprivationFilter
    filter_backends = [DjangoFilterBackend]


class NorthernIrelandMultipleDeprivationViewSet(viewsets.ModelViewSet):
    """
    Returns a list of all Northern Ireland SOAs with the associated deprivation rank and quintiles, as well as the rank and quintile of all the associated deprivation domains (2020).
    Filter params include: "soa_code"
    If none are passed, a list is returned
    """

    queryset = NorthernIrelandIndexMultipleDeprivation.objects.all().order_by(
        "-imd_rank"
    )
    serializer_class = NorthernIrelandIndexMultipleDepricationSerializer
    permission_classes = [permissions.IsAuthenticated]
    filterset_fields = ["soa__soa_code", "soa__soa_name"]
    filter_backends = [DjangoFilterBackend]


# custom views / endpoints
@permission_classes((permissions.AllowAny,))
class PostcodeView(APIView):
    @extend_schema(
        parameters=[
            OpenApiParameter(name='postcode', description='Postcode for postcodes.io', required=True, type=str),
        ]
    )
    def get(self, request):
        """
        This is a proxy for postcodes.io, an api that looks up a given postcode
        and returns lsoa code, ccg code and other important codes information
        """
        postcode = request.query_params.get("postcode")
        if postcode:
            response = regions_for_postcode(postcode=postcode)
            return Response(response)


class UKIndexMultipleDeprivationView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    english_serializer_class = EnglishIndexMultipleDeprivationSerializer
    welsh_serializer_class = WelshIndexMultipleDeprivationSerializer
    scottish_serializer_class = ScottishIndexMultipleDeprivationSerializer
    northern_ireland_serializer_class = (
        NorthernIrelandIndexMultipleDepricationSerializer
    )

    @extend_schema(
        parameters=[
            OpenApiParameter(name='postcode', description='Postcode for postcodes.io', required=True, type=str),
        ]
    )
    def get(self, request):
        """
        Returns an index of multiple deprivations against a postcode, from either England, Wales, Scotland or Northern Ireland
        It accepts a UK postcode
        Parameters:
        postcode: string [Mandatory]
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
                            instance=imd, context={"request": Request(request)}
                        )
                    elif lsoa_object["country"] == "Wales":
                        lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
                        imd = WelshIndexMultipleDeprivation.objects.filter(
                            lsoa=lsoa
                        ).get()
                        response = self.welsh_serializer_class(
                            instance=imd, context={"request": Request(request)}
                        )
                    elif lsoa_object["country"] == "Scotland":
                        lsoa = DataZone.objects.filter(data_zone_code=lsoa_code).get()
                        imd = ScottishIndexMultipleDeprivation.objects.filter(
                            data_zone=lsoa
                        ).get()
                        response = self.scottish_serializer_class(
                            instance=imd, context={"request": Request(request)}
                        )
                    elif lsoa_object["country"] == "Northern Ireland":
                        lsoa = SOA.objects.filter(soa_code=lsoa_code).get()
                        imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                            soa=lsoa
                        ).get()
                        response = self.northern_ireland_serializer_class(
                            instance=imd, context={"request": Request(request)}
                        )
                    else:
                        raise ParseError("No valid country supplied.", code=400)
            else:
                # postcode not valid
                raise ParseError("Invalid postcode supplied.", code=400)
        else:
            raise ParseError("Postcode not supplied.", code=400)

        return Response(response.data)
