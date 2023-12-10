# django imports
from rest_framework import status

# 3rd party imports
import pytest

# rcpch_census_platform imports
from deprivation_scores.constants import NORTHERN_IRELAND_IMD_DATA
from deprivation_scores.general_functions import quantile_for_rank


# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank


@pytest.mark.django_db
@pytest.mark.usefixtures("seed_data_fixture")
@pytest.mark.parametrize("northern_ireland_test_data", NORTHERN_IRELAND_IMD_DATA)
def test_northern_ireland_imd(api_client, northern_ireland_test_data) -> None:
    """
    The IMD raw score returned is correct
    :param api_client
    :return
    """

    postcode = northern_ireland_test_data["postcode"]
    imd_rank = northern_ireland_test_data["imd_rank"]

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


# @pytest.mark.django_db
# @pytest.mark.parametrize("northern_ireland_test_data", NORTHERN_IRELAND_IMD_DATA)
# def test_northern_ireland_decile_calculation(northern_ireland_test_data) -> None:
#     """
#     Should return the correct decile from the rank
#     """
#     expected_decile = int(northern_ireland_test_data["WIMD 2019 Decile"])
#     decile = quantile_for_rank(
#         rank=int(northern_ireland_test_data['WIMD 2019 Rank']),
#         requested_quantile=10,
#         country="wales",
#     )
#     expected_quintile = int(northern_ireland_test_data["WIMD 2019 Quintile"])
#     quintile = quantile_for_rank(
#         rank=int(northern_ireland_test_data['WIMD 2019 Rank']),
#         requested_quantile=5,
#         country="wales",
#     )
#     expected_quartile = int(northern_ireland_test_data["WIMD 2019 Quartile"])
#     quartile = quantile_for_rank(
#         rank=int(northern_ireland_test_data['WIMD 2019 Rank']),
#         requested_quantile=4,
#         country="wales",
#     )

#     assert (
#         (decile["data_quantile"]) == expected_decile
#     ), f"{decile['data_quantile']} was calculated, but {expected_decile} was expected."

#     assert (
#         (quintile["data_quantile"]) == expected_quintile
#     ), f"{quintile['data_quantile']} was calculated, but {expected_quintile} was expected."

#     assert (
#         (quartile["data_quantile"]) == expected_quartile
#     ), f"{quartile['data_quantile']} was calculated, but {expected_quartile} was expected."
