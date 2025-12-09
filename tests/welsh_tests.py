import pytest

# API endpoint URLs (no /api prefix - routes are at root level)
INDICES_OF_MULTIPLE_DEPRIVATION_URL = "/indices_of_multiple_deprivation"
INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL = "/index_of_multiple_deprivation_quantile"

# Welsh IMD test data from WIMD 2019
# LSOA codes and expected values from the WIMD 2019 dataset
WELSH_2019_IMD_TEST_DATA = [
    {
        "Postcode": "CF103NQ",
        "LSOA Code": "W01001939",
        "LSOA Name": "Cathays 10",
        "WIMD 2019 Rank": 833,
        "WIMD 2019 Decile": 5,
        "WIMD 2019 Quintile": 3,
        "WIMD 2019 Quartile": 2,
    },
    {
        "Postcode": "CH6 5QX",
        "LSOA Code": "W01000291",
        "LSOA Name": "Flint Coleshill 3",
        "WIMD 2019 Rank": 1279,
        "WIMD 2019 Decile": 7,
        "WIMD 2019 Quintile": 4,
        "WIMD 2019 Quartile": 3,
    },
    {
        "Postcode": "LD3 0TP",
        "LSOA Code": "W01000440",
        "LSOA Name": "Felin-fâch",
        "WIMD 2019 Rank": 1480,
        "WIMD 2019 Decile": 8,
        "WIMD 2019 Quintile": 4,
        "WIMD 2019 Quartile": 4,
    },
    {
        "Postcode": "SA1 1AA",
        "LSOA Code": "W01000741",
        "LSOA Name": "Bonymaen 4",
        "WIMD 2019 Rank": 355,
        "WIMD 2019 Decile": 2,
        "WIMD 2019 Quintile": 1,
        "WIMD 2019 Quartile": 1,
    },
    {
        "Postcode": "LD1 5AB",
        "LSOA Code": "W01000455",
        "LSOA Name": "Llandrindod North",
        "WIMD 2019 Rank": 769,
        "WIMD 2019 Decile": 5,
        "WIMD 2019 Quintile": 3,
        "WIMD 2019 Quartile": 2,
    },
]


@pytest.mark.django_db
class TestWelshIndicesOfMultipleDeprivation:
    """Tests for the indices_of_multiple_deprivation endpoint using Welsh WIMD 2019 data."""

    def test_valid_welsh_postcode_returns_imd_data(self, api_client):
        """Test that a valid Welsh postcode returns IMD data."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CF103NQ", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert "imd_rank" in data
        assert "income_rank" in data
        assert "employment_rank" in data

    def test_welsh_postcode_default_year_is_2019(self, api_client):
        """Test that the default year for Welsh postcodes is 2019 when not specified."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CF103NQ"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "imd_rank" in data
        assert data["year"] == 2019

    def test_welsh_imd_rank_cathays_matches_expected(self, api_client):
        """Test that IMD rank matches expected value for Cathays 10 area."""
        # CF103NQ (Cathays 10) has WIMD 2019 Rank 833
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CF103NQ", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 833

    def test_welsh_imd_rank_flint_matches_expected(self, api_client):
        """Test that IMD rank matches expected value for Flint Coleshill area."""
        # CH6 5QX (Flint Coleshill 3) has WIMD 2019 Rank 1279
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CH6 5QX", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 1279

    def test_welsh_high_deprivation_postcode(self, api_client):
        """Test a high deprivation postcode (low rank) from WIMD 2019 dataset."""
        # SA1 1AA (Bonymaen 4) has WIMD 2019 Rank 355 - high deprivation
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "SA1 1AA", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 355

    def test_welsh_low_deprivation_postcode(self, api_client):
        """Test a low deprivation postcode (high rank) from WIMD 2019 dataset."""
        # LD3 0TP (Felin-fâch) has WIMD 2019 Rank 1480 - low deprivation
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "LD3 0TP", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 1480

    def test_welsh_llandrindod_postcode(self, api_client):
        """Test Llandrindod North postcode returns expected WIMD data."""
        # LD1 5AB (Llandrindod North) has WIMD 2019 Rank 769
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "LD1 5AB", "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 769

    def test_invalid_year_2020_for_wales_returns_error(self, api_client):
        """Test that year 2020 returns an error for Welsh postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CF103NQ", "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_year_2025_for_wales_returns_error(self, api_client):
        """Test that year 2025 returns an error for Welsh postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "CF103NQ", "year": 2025},
        )
        assert response.status_code == 400

    def test_missing_postcode_returns_error(self, api_client):
        """Test that missing postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_postcode_returns_error(self, api_client):
        """Test that an invalid postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "INVALID123", "year": 2019},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestWelshIndexOfMultipleDeprivationQuantile:
    """Tests for the index_of_multiple_deprivation_quantile endpoint using Welsh WIMD 2019 data."""

    def test_valid_welsh_postcode_returns_quantile_data(self, api_client):
        """Test that a valid Welsh postcode returns quantile data."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]
        assert "data_quantile" in data["result"]

    def test_welsh_quantile_default_year_is_2019(self, api_client):
        """Test that the default year for Welsh postcodes is 2019 when not specified."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]

    # Tests for CF103NQ (Cathays 10) - Rank 833, Decile 5, Quintile 3, Quartile 2

    def test_welsh_decile_cathays_matches_expected(self, api_client):
        """Test that decile (quantile=10) matches expected value for Cathays 10."""
        # CF103NQ has WIMD 2019 Rank 833 and Decile 5
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 833
        assert data["data_quantile"] == 5

    def test_welsh_quintile_cathays_matches_expected(self, api_client):
        """Test that quintile (quantile=5) matches expected value for Cathays 10."""
        # CF103NQ has WIMD 2019 Rank 833 and Quintile 3
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 833
        assert data["data_quantile"] == 3
        assert data["requested_quantile"] == 5
        assert data["requested_quantile_name"] == "quintile"

    def test_welsh_quartile_cathays_matches_expected(self, api_client):
        """Test that quartile (quantile=4) matches expected value for Cathays 10."""
        # CF103NQ has WIMD 2019 Rank 833 and Quartile 2
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 4, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 833
        assert data["data_quantile"] == 2
        assert data["requested_quantile"] == 4
        assert data["requested_quantile_name"] == "quartile"

    # Tests for CH6 5QX (Flint Coleshill 3) - Rank 1279, Decile 7, Quintile 4, Quartile 3

    def test_welsh_decile_flint_matches_expected(self, api_client):
        """Test that decile matches expected value for Flint Coleshill."""
        # CH6 5QX has WIMD 2019 Rank 1279 and Decile 7
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CH6 5QX", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1279
        assert data["data_quantile"] == 7

    def test_welsh_quintile_flint_matches_expected(self, api_client):
        """Test that quintile matches expected value for Flint Coleshill."""
        # CH6 5QX has WIMD 2019 Rank 1279 and Quintile 4
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CH6 5QX", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1279
        assert data["data_quantile"] == 4

    def test_welsh_quartile_flint_matches_expected(self, api_client):
        """Test that quartile matches expected value for Flint Coleshill."""
        # CH6 5QX has WIMD 2019 Rank 1279 and Quartile 3
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CH6 5QX", "quantile": 4, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1279
        assert data["data_quantile"] == 3

    # Tests for LD3 0TP (Felin-fâch) - Rank 1480, Decile 8, Quintile 4, Quartile 4

    def test_welsh_decile_felinfach_matches_expected(self, api_client):
        """Test that decile matches expected value for Felin-fâch."""
        # LD3 0TP has WIMD 2019 Rank 1480 and Decile 8
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD3 0TP", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1480
        assert data["data_quantile"] == 8

    def test_welsh_quintile_felinfach_matches_expected(self, api_client):
        """Test that quintile matches expected value for Felin-fâch."""
        # LD3 0TP has WIMD 2019 Rank 1480 and Quintile 4
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD3 0TP", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1480
        assert data["data_quantile"] == 4

    def test_welsh_quartile_felinfach_matches_expected(self, api_client):
        """Test that quartile matches expected value for Felin-fâch."""
        # LD3 0TP has WIMD 2019 Rank 1480 and Quartile 4
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD3 0TP", "quantile": 4, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 1480
        assert data["data_quantile"] == 4

    # Tests for SA1 1AA (Bonymaen 4) - Rank 355, Decile 2, Quintile 1, Quartile 1 (high deprivation)

    def test_welsh_decile_bonymaen_matches_expected(self, api_client):
        """Test that decile matches expected value for Bonymaen (high deprivation area)."""
        # SA1 1AA has WIMD 2019 Rank 355 and Decile 2
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SA1 1AA", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 355
        assert data["data_quantile"] == 2

    def test_welsh_quintile_bonymaen_matches_expected(self, api_client):
        """Test that quintile matches expected value for Bonymaen (high deprivation area)."""
        # SA1 1AA has WIMD 2019 Rank 355 and Quintile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SA1 1AA", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 355
        assert data["data_quantile"] == 1

    def test_welsh_quartile_bonymaen_matches_expected(self, api_client):
        """Test that quartile matches expected value for Bonymaen (high deprivation area)."""
        # SA1 1AA has WIMD 2019 Rank 355 and Quartile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SA1 1AA", "quantile": 4, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 355
        assert data["data_quantile"] == 1

    # Tests for LD1 5AB (Llandrindod North) - Rank 769, Decile 5, Quintile 3, Quartile 2

    def test_welsh_decile_llandrindod_matches_expected(self, api_client):
        """Test that decile matches expected value for Llandrindod North."""
        # LD1 5AB has WIMD 2019 Rank 769 and Decile 5
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD1 5AB", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 769
        assert data["data_quantile"] == 5

    def test_welsh_quintile_llandrindod_matches_expected(self, api_client):
        """Test that quintile matches expected value for Llandrindod North."""
        # LD1 5AB has WIMD 2019 Rank 769 and Quintile 3
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD1 5AB", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 769
        assert data["data_quantile"] == 3

    def test_welsh_quartile_llandrindod_matches_expected(self, api_client):
        """Test that quartile matches expected value for Llandrindod North."""
        # LD1 5AB has WIMD 2019 Rank 769 and Quartile 2
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "LD1 5AB", "quantile": 4, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 769
        assert data["data_quantile"] == 2

    def test_welsh_country_is_wales(self, api_client):
        """Test that country field is 'wales' for Welsh postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["country"] == "wales"

    # Error handling tests

    def test_missing_quantile_returns_error(self, api_client):
        """Test that missing quantile parameter returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_quantile_returns_error(self, api_client):
        """Test that an invalid quantile value returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 15, "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_quantile_zero_returns_error(self, api_client):
        """Test that quantile=0 returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 0, "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_quantile_negative_returns_error(self, api_client):
        """Test that a negative quantile value returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": -1, "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_quantile_100_returns_error(self, api_client):
        """Test that quantile=100 (out of valid range) returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 100, "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_year_2020_for_wales_returns_error(self, api_client):
        """Test that year 2020 returns an error for Welsh postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10, "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_year_2025_for_wales_returns_error(self, api_client):
        """Test that year 2025 returns an error for Welsh postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "CF103NQ", "quantile": 10, "year": 2025},
        )
        assert response.status_code == 400

    def test_all_valid_quantiles_work(self, api_client):
        """Test that all valid quantile values work for Welsh data."""
        valid_quantiles = [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]
        for quantile in valid_quantiles:
            response = api_client.get(
                INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
                {"postcode": "CF103NQ", "quantile": quantile, "year": 2019},
            )
            assert response.status_code == 200, f"Failed for quantile {quantile}"
            data = response.json()["result"]
            assert data["requested_quantile"] == quantile
