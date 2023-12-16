from django_filters.filterset import FilterSet, CharFilter, NumberFilter
from .models.entities import *


class CountryFilter(FilterSet):
    name = CharFilter(
        field_name="local_authority__local_authority_name",
        lookup_expr="icontains",
    )

    class Meta:
        model = Country
        fields = (
            "boundary_identifier",
            "name",
        )
