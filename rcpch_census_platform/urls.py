"""rcpch_census_platform URL Configuration
"""
from django.urls import include, path
from django.contrib import admin


urlpatterns = [
    path("admin/", admin.site.urls),
    path("deprivation_scores/", include("deprivation_scores.urls")),
    path("organisation_bank/", include("deprivation_scores.urls")),
    path("accounts/", include("django.contrib.auth.urls")),
]
