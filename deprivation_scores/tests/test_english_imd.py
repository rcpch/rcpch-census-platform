import pytest 

# Assert LSOA returns correct IMD rank
# Assert LSOA correctly return error if incorrect IMD rank



@pytest.mark.django_db
def test_correctly_return_imd_raw_score(api_client) -> None:
    """
    The IMD raw score returned is correct
    :param api_client
    :return
    """

    postcode = "TN3 9EB"
    # expected Index of Multiple Deprivation Rank: 25265, Decile: 8

    response = api_client.get(f"/indices_of_multiple_deprivation?postcode={postcode}", format="json")

    assert response.status_code == 200
    assert response.data["imd_rank"] == 25265
    assert response.data["imd_decile"] == 8


