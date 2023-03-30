from django.urls import include, path
from rest_framework import routers
from .views import (
    LocalAuthorityDistrictViewSet,
    LSOAViewSet,
    SOAViewSet,
    DataZoneViewSet,
    GreenSpaceViewSet,
    EnglishIndexMultipleDeprivationViewSet,
    WelshMultipleDeprivationViewSet,
    ScottishMultipleDeprivationViewSet,
    NorthernIrelandMultipleDeprivationViewSet,
    PostcodeView,
    UKIndexMultipleDeprivationView,
    UKIndexMultipleDeprivationQuantileView,
)

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"local_authority_districts", viewset=LocalAuthorityDistrictViewSet)
router.register(r"england_wales_lower_layer_super_output_areas", viewset=LSOAViewSet)
router.register(r"northern_ireland_small_output_areas", viewset=SOAViewSet)
router.register(r"scotland_data_zones", viewset=DataZoneViewSet)
router.register(r"green_space", viewset=GreenSpaceViewSet)
router.register(
    r"english_indices_of_multiple_deprivation",
    viewset=EnglishIndexMultipleDeprivationViewSet,
)
router.register(
    r"welsh_indices_of_multiple_deprivation", viewset=WelshMultipleDeprivationViewSet
)
router.register(
    r"scottish_indices_of_multiple_deprivation",
    viewset=ScottishMultipleDeprivationViewSet,
)
router.register(
    r"northern_ireland_indices_of_multiple_deprivation",
    viewset=NorthernIrelandMultipleDeprivationViewSet,
)

drf_routes = [
    # rest framework paths
    path("/", include(router.urls)),
    path("boundaries", view=PostcodeView.as_view()),
    path(
        "indices_of_multiple_deprivation",
        view=UKIndexMultipleDeprivationView.as_view(),
    ),
    path("index_of_multiple_deprivation_quantile",
        view=UKIndexMultipleDeprivationQuantileView.as_view(),
    ),

    # JSON Schema
    path("", SpectacularJSONAPIView.as_view(), name="json"),

    # Swagger UI
    path("swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
]

urlpatterns = []

urlpatterns += drf_routes
