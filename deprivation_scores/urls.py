from django.urls import include, path
from rest_framework import routers
from .views import (
    LocalAuthorityDistrictViewSet,
    LSOAViewSet,
    SOAViewSet,
    DataZoneViewSet,
    GreenSpaceViewSet,
    EnglishIndexMultipleDeprivationViewSet,
    MapDataView,
    WelshMultipleDeprivationViewSet,
    ScottishMultipleDeprivationViewSet,
    NorthernIrelandMultipleDeprivationViewSet,
    PopulationDensityViewSet,
    PostcodeView,
    UKIndexMultipleDeprivationView,
    UKIndexMultipleDeprivationQuantileView,
)

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

from rcpch_census_platform.build_info import get_build_info


class RouterWithBuildInfo(routers.DefaultRouter):
    def get_api_root_view(self, *args, **kwargs):
        view = super().get_api_root_view(*args, **kwargs)

        def view_with_build_info(request, *args, **kwargs):
            response = view(request, *args, **kwargs)

            build_info = get_build_info()
            response.headers["X-Git-Revision"] = build_info.get(
                "latest_git_commit", "[latest commit hash not found]"
            )

            return response

        return view_with_build_info


router = RouterWithBuildInfo()

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

router.register(
    "uk_population_density",
    viewset=PopulationDensityViewSet,
    basename="uk_population_density",
)

drf_routes = [
    # rest framework paths
    path("", include(router.urls)),
    path("boundaries", view=PostcodeView.as_view()),
    path(
        "indices_of_multiple_deprivation",
        view=UKIndexMultipleDeprivationView.as_view(),
    ),
    path(
        "index_of_multiple_deprivation_quantile",
        view=UKIndexMultipleDeprivationQuantileView.as_view(),
    ),
    path("map-data/", MapDataView.as_view(), name="map-data-optimized"),
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
