# django imports
from rest_framework import status
from rest_framework.test import APIClient
from django.urls import reverse

# 3rd party imports
import pytest

# deprivation_scores imports
from ..constants import ENGLISH_IMD_TEST_DATA
from ..general_functions import (
    quantile_for_rank,
)

# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_data_fixture")
@pytest.mark.parametrize("english_test_data", ENGLISH_IMD_TEST_DATA)
def test_correctly_return_english_imd(api_client, english_test_data) -> None:
    """
    The IMD raw score returned is correct
    :param api_client
    :return
    """

    postcode = english_test_data["Postcode"]
    imd_rank = english_test_data["Index of Multiple Deprivation Rank"]
    imd_decile = english_test_data["Index of Multiple Deprivation Decile"]
    # expected Index of Multiple Deprivation Rank: 25265, Decile: 8

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
    assert (
        str(response.data["imd_decile"]) == imd_decile
    ), f"{postcode} should have returned a deprivation decile of {imd_decile}"


@pytest.mark.django_db
@pytest.mark.parametrize("english_test_data", ENGLISH_IMD_TEST_DATA)
def test_english_decile_calculation(english_test_data) -> None:
    """
    Should return the correct decile from the rank
    """
    expected_decile = int(english_test_data["Index of Multiple Deprivation Decile"])
    decile = quantile_for_rank(
        rank=int(english_test_data["Index of Multiple Deprivation Rank"]),
        requested_quantile=10,
        country="england",
    )

    assert (
        decile["data_quantile"] == expected_decile
    ), f"{decile['data_quantile']} was calculated, but {expected_decile} was expected."
