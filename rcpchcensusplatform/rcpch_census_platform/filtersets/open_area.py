from django_filters.filterset import FilterSet, CharFilter, NumberFilter
from django.apps import apps

DataZone = apps.get_model("rcpch_census_platform", "DataZone")


class DataZoneFilter(FilterSet):
    local_authority_code = CharFilter(
        field_name="local_authority__local_authority_district_code",
        lookup_expr="icontains",
    )
    local_authority_name = CharFilter(
        field_name="local_authority__local_authority_name",
        lookup_expr="icontains",
    )

    class Meta:
        model = DataZone
        fields = (
            "code",
            "name",
            "year",
        )
