import pytest

INDICES_OF_MULTIPLE_DEPRIVATION_URL = "/indices_of_multiple_deprivation"


@pytest.mark.django_db
def test_postcode_with_different_lsoa_years_returns_different_imd(api_client):
    """TS18 3WH has different LSOAs in 2011 vs 2021; ensure IMD differs."""
    # 2019 (uses 2011 LSOA mapping)
    resp_2019 = api_client.get(
        INDICES_OF_MULTIPLE_DEPRIVATION_URL, {"postcode": "TS18 3WH", "year": 2019}
    )
    assert resp_2019.status_code == 200
    data_2019 = resp_2019.json()
    assert data_2019["imd_rank"] == 12021
    assert data_2019["imd_decile"] == 4

    # 2025 (uses 2021 LSOA mapping)
    resp_2025 = api_client.get(
        INDICES_OF_MULTIPLE_DEPRIVATION_URL, {"postcode": "TS18 3WH", "year": 2025}
    )
    assert resp_2025.status_code == 200
    data_2025 = resp_2025.json()
    assert data_2025["imd_rank"] == 22577
    assert data_2025["imd_decile"] == 7
