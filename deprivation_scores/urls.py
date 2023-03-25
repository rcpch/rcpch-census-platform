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
)

from drf_spectacular.views import SpectacularAPIView, SpectacularSwaggerView

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
    path("api/v1/", include(router.urls)),
    path("api/v1/boundaries", view=PostcodeView.as_view()),
    path(
        "api/v1/indices_of_multiple_deprivation",
        view=UKIndexMultipleDeprivationView.as_view(),
    ),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
    
    #SWAGGERUI PATHS
    #path to download schema
    path('api/v1/schema/', SpectacularAPIView.as_view(), name='schema'),
    # path to ui
    path('api/v1/schema/swagger-ui/', SpectacularSwaggerView.as_view(url_name='schema'), name='swagger-ui'),

]

urlpatterns = []

urlpatterns += drf_routes
