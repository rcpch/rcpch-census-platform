# django imports
from rest_framework import status

# 3rd party imports
import pytest

# rcpch_census_platform imports
from deprivation_scores.constants import SCOTTISH_IMD_TEST_DATA
from deprivation_scores.general_functions import quantile_for_rank


# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_data_fixture")
@pytest.mark.parametrize("scottish_test_data", SCOTTISH_IMD_TEST_DATA)
def test_scottish_imd(api_client, scottish_test_data) -> None:
    """
    The IMD raw score returned is correct
    :param api_client
    :return
    """

    postcode = scottish_test_data["postcode"]
    imd_rank = scottish_test_data["SIMD 2020 Rank"]

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


@pytest.mark.django_db
@pytest.mark.parametrize("scottish_test_data", SCOTTISH_IMD_TEST_DATA)
def test_scottish_decile_calculation(scottish_test_data) -> None:
    """
    Should return the correct decile from the rank
    """
    expected_decile = int(scottish_test_data["SIMD 2020 Decile"])
    decile = quantile_for_rank(
        rank=int(scottish_test_data['SIMD 2020 Rank']),
        requested_quantile=10,
        country="scotland",
    )
    expected_quintile = int(scottish_test_data["SIMD 2020 Quintile"])
    quintile = quantile_for_rank(
        rank=int(scottish_test_data['SIMD 2020 Rank']),
        requested_quantile=5,
        country="scotland",
    )

    assert (
        (decile["data_quantile"]) == expected_decile
    ), f"{decile['data_quantile']} was calculated, but {expected_decile} was expected."
    
    assert (
        (quintile["data_quantile"]) == expected_quintile
    ), f"{quintile['data_quantile']} was calculated, but {expected_quintile} was expected."
