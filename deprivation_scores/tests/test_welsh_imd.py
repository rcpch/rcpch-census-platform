# django imports
from rest_framework import status
from django.urls import reverse

# 3rd party imports
import pytest

# deprivation_scores imports
from ..constants import WELSH_IMD_TEST_DATA
from ..general_functions import (
    quantile_for_rank,
)

# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_data_fixture")
@pytest.mark.parametrize("welsh_test_data", WELSH_IMD_TEST_DATA)
def test_welsh_imd(api_client, welsh_test_data) -> None:
    """
    The IMD raw score returned is correct
    :param api_client
    :return
    """

    postcode = welsh_test_data["postcode"]
    imd_rank = welsh_test_data["WIMD 2019 Rank"]

    response = api_client.get(
        f"{reverse('imd_extended')}?postcode={postcode}",
        format="json",
    )

    assert (
        response.status_code == status.HTTP_200_OK
    ), f"{postcode} should have returned a {status.HTTP_200_OK}"
    assert (
        str(response.data["imd_rank"]) == imd_rank
    ), f"{postcode} should have returned a deprivation rank of {imd_rank}"


@pytest.mark.django_db
@pytest.mark.parametrize("welsh_test_data", WELSH_IMD_TEST_DATA)
def test_welsh_decile_calculation(welsh_test_data) -> None:
    """
    Should return the correct decile from the rank
    """
    expected_decile = int(welsh_test_data["WIMD 2019 Decile"])
    decile = quantile_for_rank(
        rank=int(welsh_test_data["WIMD 2019 Rank"]),
        requested_quantile=10,
        country="wales",
    )
    expected_quintile = int(welsh_test_data["WIMD 2019 Quintile"])
    quintile = quantile_for_rank(
        rank=int(welsh_test_data["WIMD 2019 Rank"]),
        requested_quantile=5,
        country="wales",
    )
    expected_quartile = int(welsh_test_data["WIMD 2019 Quartile"])
    quartile = quantile_for_rank(
        rank=int(welsh_test_data["WIMD 2019 Rank"]),
        requested_quantile=4,
        country="wales",
    )

    assert (
        decile["data_quantile"]
    ) == expected_decile, (
        f"{decile['data_quantile']} was calculated, but {expected_decile} was expected."
    )

    assert (
        quintile["data_quantile"]
    ) == expected_quintile, f"{quintile['data_quantile']} was calculated, but {expected_quintile} was expected."

    assert (
        quartile["data_quantile"]
    ) == expected_quartile, f"{quartile['data_quantile']} was calculated, but {expected_quartile} was expected."
