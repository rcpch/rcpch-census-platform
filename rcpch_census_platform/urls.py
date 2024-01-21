"""rcpch-census-platform URL Configuration
"""
from django.urls import include, path


urlpatterns = [
    path(
        "rcpch-census-platform/api/v1/",
        include("deprivation_scores.urls"),
    )
]
