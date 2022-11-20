from rest_framework import viewsets
from rest_framework import permissions

from .models import LocalAuthority, LSOA, IndexMultipleDeprivation
from .serializers import (
    LocalAuthorityDistrictSerializer,
    LSOASerializer,
    IndexMultipleDeprivationSerializer,
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


class IndexMultipleDeprivationViewSet(viewsets.ModelViewSet):
    queryset = IndexMultipleDeprivation.objects.all().order_by("-imd_rank")
    serializer_class = IndexMultipleDeprivationSerializer
    permission_classes = [permissions.IsAuthenticated]
