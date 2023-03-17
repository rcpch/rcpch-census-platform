from rest_framework import viewsets
from rest_framework import permissions
from rest_framework.views import APIView, Response
from rest_framework import authentication, permissions

from requests import Request

from .models import (
    LocalAuthority,
    LSOA,
    IndexMultipleDeprivation,
    GreenSpace,
    WelshIndexMultipleDeprivation,
)
from .serializers import (
    LocalAuthorityDistrictSerializer,
    LSOASerializer,
    IndexMultipleDeprivationSerializer,
    GreenSpaceSerializer,
    WelshIndexMultipleDeprivationSerializer,
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


class IndexMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = IndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = IndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        lsoa_code = self.request.query_params.get("lsoa_code", None)
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            lsoa_object = lsoa_for_postcode(postcode=post_code)
        if lsoa_object["lsoa"]:
            lsoa = LSOA.objects.filter(lsoa_code=lsoa_code).get()
            if lsoa_object["country"] == "England":
                query_set = IndexMultipleDeprivation.objects.filter(lsoa=lsoa).all()
            return query_set
        return super().get_queryset()


class WelshMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = WelshIndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = WelshIndexMultipleDeprivationSerializer
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
    english_serializer_class = IndexMultipleDeprivationSerializer
    welsh_serializer_class = WelshIndexMultipleDeprivationSerializer

    def get(self, request):
        """
        Returns an IMD against a postcode, from either Wales or Scotland
        """
        lsoa_code = self.request.query_params.get("lsoa_code", None)
        post_code = self.request.query_params.get("postcode", None)
        if post_code:
            lsoa_object = lsoa_for_postcode(postcode=post_code)
        if lsoa_object["lsoa"]:
            lsoa = LSOA.objects.filter(lsoa_code=lsoa_object["lsoa"]).get()
            if lsoa_object["country"] == "England":
                imd = IndexMultipleDeprivation.objects.filter(lsoa=lsoa).get()
                response = self.english_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )
            elif lsoa_object["country"] == "Wales":
                imd = WelshIndexMultipleDeprivation.objects.filter(lsoa=lsoa).get()
                response = self.welsh_serializer_class(
                    instance=imd, context={"request": Request(request)}
                )

            return Response(response.data)
