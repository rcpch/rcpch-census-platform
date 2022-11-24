from django.urls import include, path
from rest_framework import routers
from .views import (
    IndexMultipleDeprivationViewSet,
    LocalAuthorityDistrictViewSet,
    LSOAViewSet,
    PostcodeView,
    GreenSpaceViewSet,
)

router = routers.DefaultRouter()
router.register(r"local_authority_districts", viewset=LocalAuthorityDistrictViewSet)
router.register(r"lower_layer_super_output_areas", viewset=LSOAViewSet)
router.register(
    r"indices_of_multiple_deprivation", viewset=IndexMultipleDeprivationViewSet
)
router.register(r"green_space", viewset=GreenSpaceViewSet)

drf_routes = [
    # rest framework paths
    path("api/v1/", include(router.urls)),
    path("api/v1/boundaries", view=PostcodeView.as_view()),
    path("api-auth/", include("rest_framework.urls", namespace="rest_framework")),
]

urlpatterns = []

urlpatterns += drf_routes
