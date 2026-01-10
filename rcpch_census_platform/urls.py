"""rcpch_census_platform URL Configuration
"""
from django.contrib import admin
from django.http import JsonResponse
from django.urls import include, path

def health_check(request):
    return JsonResponse({"status": "ok"})


urlpatterns = [
    path("health/", health_check, name="health_check"),
    path("admin/", admin.site.urls),
    path("", include("deprivation_scores.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]
