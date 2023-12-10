# django imports
from rest_framework import status

# 3rd party imports
import pytest

# rcpch_census_platform imports
from deprivation_scores.constants import ENGLISH_IMD_TEST_DATA


# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_data_fixture")
@pytest.mark.parametrize("english_test_data", ENGLISH_IMD_TEST_DATA)
def test_correctly_return_imd_raw_score(api_client, english_test_data) -> None:
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
        f"/indices_of_multiple_deprivation?postcode={postcode}",
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
