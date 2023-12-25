"""rcpch-census-platform URL Configuration
"""
from django.urls import include, path
from django.contrib import admin


urlpatterns = [
    path("admin/", admin.site.urls),
    path(
        "rcpch-census-platform/api/v1/",
        include("rcpchcensusplatform.rcpch_census_platform.urls"),
    ),
    path("accounts/", include("django.contrib.auth.urls")),
]
