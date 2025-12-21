import pytest

# API endpoint URLs (no /api prefix - routes are at root level)
INDICES_OF_MULTIPLE_DEPRIVATION_URL = "/indices_of_multiple_deprivation"
INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL = "/index_of_multiple_deprivation_quantile"

# Scottish IMD test data from SIMD 2020v2
# Data zone codes and expected values from the SIMD 2020v2 dataset
SCOTTISH_2020_IMD_TEST_DATA = [
    {
        "Postcode": "KW1 4AA",
        "Data Zone": "Wick North - 01",
        "IMD Rank": 1555,
        "IMD Decile": 3,
    },
    {
        "Postcode": "PA1 1AD",
        "Data Zone": "Paisley Central - 02",
        "IMD Rank": 2124,
        "IMD Decile": 4,
    },
    {
        "Postcode": "FK1 1AA",
        "Data Zone": "Falkirk - Grahamston - 03",
        "IMD Rank": 1481,
        "IMD Decile": 3,
    },
    {
        "Postcode": "EH1 1AD",
        "Data Zone": "Edinburgh City Centre",
        "IMD Rank": 3500,  # Approximate - needs verification
        "IMD Decile": 5,
    },
]


@pytest.mark.django_db
class TestScottishIndicesOfMultipleDeprivation:
    """Tests for the indices_of_multiple_deprivation endpoint using Scottish SIMD 2020 data."""

    def test_valid_scottish_postcode_returns_imd_data(self, api_client):
        """Test that a valid Scottish postcode returns IMD data."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "KW1 4AA", "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        # Scottish data has imd_rank but not imd_decile (decile via quantile endpoint)
        assert "imd_rank" in data
        assert "income_rank" in data
        assert "employment_rank" in data

    def test_scottish_postcode_default_year_is_2020(self, api_client):
        """Test that the default year for Scottish postcodes is 2020 when not specified."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "KW1 4AA"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "imd_rank" in data
        assert data["year"] == 2020

    def test_scottish_imd_rank_matches_expected(self, api_client):
        """Test that IMD rank matches expected value from SIMD 2020 dataset."""
        # KW1 4AA (Wick North) has IMD Rank 1555 in SIMD 2020
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "KW1 4AA", "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 1555

    def test_scottish_income_rank_matches_expected(self, api_client):
        """Test that income rank matches expected value from SIMD 2020 dataset."""
        # KW1 4AA (Wick North) has income rank 1539 in SIMD 2020
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "KW1 4AA", "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["income_rank"] == 1539

    def test_high_deprivation_scottish_postcode(self, api_client):
        """Test a high deprivation postcode (low rank) from SIMD 2020 dataset."""
        # FK1 1AA (Falkirk - Grahamston) has IMD Rank 1481
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "FK1 1AA", "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 1481

    def test_paisley_postcode(self, api_client):
        """Test Paisley postcode returns expected SIMD data."""
        # PA1 1AD (Paisley Central) has IMD Rank 2124
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "PA1 1AD", "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 2124

    def test_invalid_year_for_scotland_returns_error(self, api_client):
        """Test that an invalid year returns an error for Scottish postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "KW1 4AA", "year": 2019},
        )
        assert response.status_code == 400

    def test_missing_postcode_returns_error(self, api_client):
        """Test that missing postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_postcode_returns_error(self, api_client):
        """Test that an invalid postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "INVALID123", "year": 2020},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestScottishIndexOfMultipleDeprivationQuantile:
    """Tests for the index_of_multiple_deprivation_quantile endpoint using Scottish SIMD 2020 data."""

    def test_valid_scottish_postcode_returns_quantile_data(self, api_client):
        """Test that a valid Scottish postcode returns quantile data."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 10, "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]
        assert "data_quantile" in data["result"]

    def test_scottish_quantile_default_year_is_2020(self, api_client):
        """Test that the default year for Scottish postcodes is 2020 when not specified."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]

    def test_scottish_decile_quantile_matches_expected(self, api_client):
        """Test that decile (quantile=10) matches expected value from SIMD 2020 dataset."""
        # KW1 4AA (Wick North) has IMD Rank 1555 and Decile 3 in SIMD 2020
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 10, "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1555
        assert data["data_quantile"] == 3

    def test_scottish_quintile_calculation(self, api_client):
        """Test quintile calculation for Scottish data."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 5, "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1555
        assert data["requested_quantile"] == 5
        assert data["requested_quantile_name"] == "quintile"

    def test_scottish_country_is_scotland(self, api_client):
        """Test that country field is 'scotland' for Scottish postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 10, "year": 2020},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["country"] == "scotland"

    def test_missing_quantile_returns_error(self, api_client):
        """Test that missing quantile parameter returns an error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_quantile_returns_error(self, api_client):
        """Test that an invalid quantile value returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 15, "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_year_for_scotland_returns_error(self, api_client):
        """Test that an invalid year returns an error for Scottish postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "KW1 4AA", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 400

    def test_all_valid_quantiles_work(self, api_client):
        """Test that all valid quantile values work for Scottish data."""
        valid_quantiles = [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]
        for quantile in valid_quantiles:
            response = api_client.get(
                INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
                {"postcode": "KW1 4AA", "quantile": quantile, "year": 2020},
            )
            assert response.status_code == 200, f"Failed for quantile {quantile}"
            data = response.json()["result"]
            assert data["requested_quantile"] == quantile
