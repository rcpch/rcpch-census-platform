from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.views import APIView, Response
from rest_framework import authentication, permissions
from rest_framework.exceptions import NotFound

from requests import Request

from pprint import pprint

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
    local_authority_district_code_for_postcode,
)


class LocalAuthorityDistrictViewSet(viewsets.ModelViewSet):
    queryset = LocalAuthority.objects.all().order_by("-local_authority_district_code")
    serializer_class = LocalAuthorityDistrictSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        local_authority_district_code = self.request.query_params.get(
            "local_authority_district_code", None
        )
        if local_authority_district_code:
            query_set = LocalAuthority.objects.filter(
                local_authority_district_code=local_authority_district_code
            ).all()
            return query_set
        return super().get_queryset()


class LSOAViewSet(viewsets.ModelViewSet):
    queryset = LSOA.objects.all().order_by("-lsoa_code")
    serializer_class = LSOASerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lsoa_code = self.request.query_params.get("lsoa_code", None)
        if lsoa_code:
            try:
                return LSOA.objects.filter(lsoa_code=lsoa_code).all()
            except Exception as e:
                print(e)
                return
        query_set = LSOA.objects.all()
        return query_set


class SOAViewSet(viewsets.ModelViewSet):
    queryset = SOA.objects.all().order_by("-soa_code")
    serializer_class = SOASerializer
    permission_classes = [permissions.IsAuthenticated]


class GreenSpaceViewSet(viewsets.ModelViewSet):
    queryset = GreenSpace.objects.all().order_by("-total_addresses_count")
    serializer_class = GreenSpaceSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        local_authority_district_code = self.request.query_params.get(
            "local_authority_district_code", None
        )
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            local_authority_district_code = local_authority_district_code_for_postcode(
                postcode=post_code
            )
            local_authority = LocalAuthority.objects.get(
                local_authority_district_code=local_authority_district_code
            )
            query_set = GreenSpace.objects.filter(local_authority=local_authority).all()
            return query_set
        if local_authority_district_code:
            local_authority = LocalAuthority.objects.get(
                local_authority_district_code=local_authority_district_code
            )
            query_set = GreenSpace.objects.filter(local_authority=local_authority).all()
            return query_set
        return super().get_queryset()


class DataZoneViewSet(viewsets.ModelViewSet):
    queryset = DataZone.objects.all().order_by("data_zone_code")
    serializer_class = DataZoneSerializer
    permission_classes = [permissions.IsAuthenticated]


class EnglishIndexMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = EnglishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = EnglishIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lsoa_code = self.request.query_params.get("lsoa_code", None)
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            lsoa_object = lsoa_for_postcode(postcode=post_code)
        if lsoa_object["lsoa"]:
            lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
            if lsoa_object["country"] == "England":
                query_set = EnglishIndexMultipleDeprivation.objects.filter(
                    lsoa=lsoa
                ).all()
            return query_set
        return super().get_queryset()


class WelshMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = WelshIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = WelshIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]


class ScottishMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = ScottishIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = ScottishIndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]


class NorthernIrelandMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = NorthernIrelandIndexMultipleDeprivation.objects.all().order_by(
        "-imd_rank"
    )
    serializer_class = NorthernIrelandIndexMultipleDepricationSerializer
    permission_classes = [permissions.IsAuthenticated]


# custom views / endpoints
class PostcodeView(APIView):
    def get(self, request):
        """
        This is a proxy for postcodes.io, an api that looks up a given postcode
        and returns lsoa code, ccg code and so on information
        """
        postcode = request.query_params.get("postcode")
        if postcode:
            response = regions_for_postcode(postcode=postcode)
            return Response(response)


class EnglishWalesIndexMultipleDeprivationView(APIView):
    authentication_classes = [authentication.TokenAuthentication]
    permission_classes = [permissions.IsAdminUser]
    english_serializer_class = EnglishIndexMultipleDeprivationSerializer
    welsh_serializer_class = WelshIndexMultipleDeprivationSerializer
    scottish_serializer_class = ScottishIndexMultipleDeprivationSerializer
    northern_ireland_serializer_class = (
        NorthernIrelandIndexMultipleDepricationSerializer
    )

    def get(self, request):
        """
        Returns an IMD against a postcode, from either Wales or Scotland
        """
        lsoa_code = self.request.query_params.get("lsoa_code", None)
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            lsoa_object = lsoa_for_postcode(postcode=post_code)
        else:
            raise NotFound("No postcode supplied.")

        if lsoa_object["lsoa"]:
            if lsoa_object["country"] == "England":
                lsoa = LSOA.objects.filter(lsoa_code=lsoa_object["lsoa"]).get()
                imd = EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa).get()
                response = self.english_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )
            elif lsoa_object["country"] == "Wales":
                lsoa = LSOA.objects.filter(lsoa_code=lsoa_object["lsoa"]).get()
                imd = WelshIndexMultipleDeprivation.objects.filter(lsoa=lsoa).get()
                response = self.welsh_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )
            elif lsoa_object["country"] == "Scotland":
                lsoa = DataZone.objects.filter(data_zone_code=lsoa_object["lsoa"]).get()
                imd = ScottishIndexMultipleDeprivation.objects.filter(
                    data_zone=lsoa
                ).get()
                response = self.scottish_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )
            elif lsoa_object["country"] == "Northern Ireland":
                lsoa = SOA.objects.filter(soa_code=lsoa_object["lsoa"]).get()
                imd = NorthernIrelandIndexMultipleDeprivation.objects.filter(
                    soa=lsoa
                ).get()
                response = self.northern_ireland_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )
            else:
                raise NotFound(f"LSOA {lsoa} not found,.")
        else:
            raise NotFound("No valid LSOA found.")

        return Response(response.data)
