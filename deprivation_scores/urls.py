from django.urls import include, path
from rest_framework import routers
from .views import (
    GreenSpaceViewSet,
    UKIndexMultipleDeprivationView,
    UKIndexMultipleDeprivationQuantileView,
)

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"green_space", viewset=GreenSpaceViewSet)


drf_routes = [
    # rest framework paths
    path("", include(router.urls)),
    path(
        "index_of_multiple_deprivation/extended",
        view=UKIndexMultipleDeprivationView.as_view(),
        name="imd_extended",
    ),
    path(
        "index_of_multiple_deprivation/quantile",
        view=UKIndexMultipleDeprivationQuantileView.as_view(),
        name="imd_quantile",
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
