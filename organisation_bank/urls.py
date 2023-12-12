from django.urls import include, path
from rest_framework import routers
from .views import ()

from drf_spectacular.views import SpectacularJSONAPIView, SpectacularSwaggerView

router = routers.DefaultRouter()
router.register(r"", viewset=)

drf_routes = [
    # rest framework paths
    path("", include(router.urls)),
    
    # JSON Schema
    path("schema/", SpectacularJSONAPIView.as_view(), name="schema"),

    # Swagger UI
    path("swagger-ui/",
        SpectacularSwaggerView.as_view(),
        name="swagger-ui",
    ),
]

urlpatterns = []

urlpatterns += drf_routes
