from django.apps import apps

from rest_framework import serializers

from drf_spectacular.utils import extend_schema_serializer, OpenApiExample

GreenSpace = apps.get_model("deprivation_scores", "GreenSpace")


@extend_schema_serializer(
    examples=[
        OpenApiExample(
            "/green_space/1/",
            value={
                "houses_address_count": 53082,
                "houses_addresses_with_private_outdoor_space_count": 51390,
                "houses_outdoor_space_total_area": 14593876,
                "houses_percentage_of_addresses_with_private_outdoor_space": 0,
                "houses_average_size_private_outdoor_space": 284,
                "houses_median_size_private_outdoor_space": 204,
                "flats_address_count": 65346,
                "flats_addresses_with_private_outdoor_space_count": 46221,
                "flats_outdoor_space_total_area": 2953183,
                "flats_outdoor_space_count": 9280,
                "flats_percentage_of_addresses_with_private_outdoor_space": 0,
                "flats_average_size_private_outdoor_space": 318,
                "flats_average_number_of_flats_sharing_a_garden": 5,
                "total_addresses_count": 118428,
                "total_addresses_with_private_outdoor_space_count": 97611,
                "total_percentage_addresses_with_private_outdoor_space": 17547060,
                "total_average_size_private_outdoor_space": 0,
                "local_authority": "{BASE_URL}/local_authority_districts/340/",
            },
            response_only=True,
        )
    ]
)
class GreenSpaceSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = GreenSpace
        # depth = 1
        fields = [
            "houses_address_count",
            "houses_addresses_with_private_outdoor_space_count",
            "houses_outdoor_space_total_area",
            "houses_outdoor_space_total_area",
            "houses_percentage_of_addresses_with_private_outdoor_space",
            "houses_average_size_private_outdoor_space",
            "houses_median_size_private_outdoor_space",
            "flats_address_count",
            "flats_addresses_with_private_outdoor_space_count",
            "flats_outdoor_space_total_area",
            "flats_outdoor_space_count",
            "flats_percentage_of_addresses_with_private_outdoor_space",
            "flats_average_size_private_outdoor_space",
            "flats_average_number_of_flats_sharing_a_garden",
            "total_addresses_count",
            "total_addresses_with_private_outdoor_space_count",
            "total_percentage_addresses_with_private_outdoor_space",
            "total_average_size_private_outdoor_space",
            "local_authority",
        ]
