from django.urls import include, path
from rest_framework import routers
from .views import (
    GreenSpaceViewSet,
    UKIndexMultipleDeprivationView,
    UKIndexMultipleDeprivationQuantileView,
    # organisation bank viewsets
    OrganisationViewSet,
    IntegratedCareBoardViewSet,
    IntegratedCareBoardOrganisationViewSet,
    NHSEnglandRegionViewSet,
    TrustViewSet,
)

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"green_space", viewset=GreenSpaceViewSet)

"""
organisation bank views
"""
# returns a list of organisations and their nested parent details
router.register(r"organisations", viewset=OrganisationViewSet, basename="organisation")
# returns a list of trusts and their details with their child organisations (ods_code and name only)
router.register(
    r"trusts",
    viewset=TrustViewSet,
    basename="trust",
)
# returns a list of ICBS and their boundary data
router.register(
    r"integrated_care_boards/extended",
    viewset=IntegratedCareBoardViewSet,
    basename="integrated_care_board",
)
# returns a list of ICBS with name, ods_code and nested organisations
router.register(
    r"integrated_care_boards",
    viewset=IntegratedCareBoardOrganisationViewSet,
    basename="integrated_care_board",
)
# returns a list of NHS England regions and their boundary data
router.register(
    r"nhs_england_regions",
    viewset=NHSEnglandRegionViewSet,
    basename="nhs_england_region",
)


drf_routes = [
    # rest framework paths
    path("", include(router.urls)),
    path(
        "index_of_multiple_deprivation/extended",
        view=UKIndexMultipleDeprivationView.as_view(),
    ),
    path(
        "index_of_multiple_deprivation/quantile",
        view=UKIndexMultipleDeprivationQuantileView.as_view(),
    ),
    # JSON Schema
    path("schema/", SpectacularJSONAPIView.as_view(), name="schema"),
    # Swagger UI
    path(
        "swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
]

urlpatterns = []

urlpatterns += drf_routes
