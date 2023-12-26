from django.urls import include, path
from rest_framework import routers
from .views import (
    GreenSpaceViewSet,
    UKIndexMultipleDeprivationView,
    UKIndexMultipleDeprivationQuantileView,
    # organisation bank viewsets
    OrganisationViewSet,
    IntegratedCareBoardViewSet,
    NHSEnglandRegionViewSet,
    TrustViewSet,
)

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"green_space", viewset=GreenSpaceViewSet)

# organisation bank views
router.register(r"organisations", viewset=OrganisationViewSet, basename="organisation")
router.register(
    r"trusts",
    viewset=TrustViewSet,
    basename="trust",
)
router.register(
    r"integrated_care_boards",
    viewset=IntegratedCareBoardViewSet,
    basename="integrated_care_board",
)
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
