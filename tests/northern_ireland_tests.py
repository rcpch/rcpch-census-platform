import pytest

# API endpoint URLs (no /api prefix - routes are at root level)
INDICES_OF_MULTIPLE_DEPRIVATION_URL = "/indices_of_multiple_deprivation"
INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL = "/index_of_multiple_deprivation_quantile"

# Northern Ireland IMD test data from NIMDM 2017
# SOA codes and expected values from the NIMDM 2017 dataset
# Northern Ireland has 890 Super Output Areas (SOAs)
NI_2017_IMD_TEST_DATA = [
    {
        "Postcode": "BT48 7ET",
        "SOA": "Strand 1 Derry",
        "Urban_Rural": "Urban",
        "LGD": "Derry and Strabane",
        "IMD_Rank": 5,
        "Decile": 1,
        "Quintile": 1,
        "Quartile": 1,
    },
    {
        "Postcode": "BT4 3QL",
        "SOA": "Stormont 2",
        "Urban_Rural": "Urban",
        "LGD": "Belfast",
        "IMD_Rank": 889,
        "Decile": 10,
        "Quintile": 5,
        "Quartile": 4,
    },
    {
        "Postcode": "BT52 1PF",
        "SOA": "Central Coleraine",
        "Urban_Rural": "Urban",
        "LGD": "Causeway Coast and Glens",
        "IMD_Rank": 137,
        "Decile": 2,
        "Quintile": 1,
        "Quartile": 1,
    },
    {
        "Postcode": "BT7 3FH",
        "SOA": "Rosetta 1",
        "Urban_Rural": "Urban",
        "LGD": "Belfast",
        "IMD_Rank": 846,
        "Decile": 10,
        "Quintile": 5,
        "Quartile": 4,
    },
    {
        "Postcode": "BT35 6BP",
        "SOA": "Drumgullion 1",
        "Urban_Rural": "Urban",
        "LGD": "Newry, Mourne and Down",
        "IMD_Rank": 70,
        "Decile": 1,
        "Quintile": 1,
        "Quartile": 1,
    },
]


@pytest.mark.django_db
class TestNorthernIrelandIndicesOfMultipleDeprivation:
    """Tests for the indices_of_multiple_deprivation endpoint using Northern Ireland NIMDM 2017 data."""

    def test_valid_ni_postcode_returns_imd_data(self, api_client):
        """Test that a valid Northern Ireland postcode returns IMD data."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert "imd_rank" in data

    def test_ni_postcode_default_year_is_2017(self, api_client):
        """Test that the default year for NI postcodes is 2017 when not specified."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF"},
        )
        assert response.status_code == 200
        data = response.json()
        assert "imd_rank" in data
        assert data["year"] == 2017

    def test_ni_imd_rank_coleraine_matches_expected(self, api_client):
        """Test that IMD rank matches expected value for Central Coleraine."""
        # BT52 1PF (Central Coleraine) has NIMDM 2017 Rank 137
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 137

    def test_ni_imd_rank_derry_matches_expected(self, api_client):
        """Test that IMD rank matches expected value for Strand 1 Derry (high deprivation)."""
        # BT48 7ET (Strand 1 Derry) has NIMDM 2017 Rank 5 - very high deprivation
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT48 7ET", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 5

    def test_ni_high_deprivation_postcode(self, api_client):
        """Test a high deprivation postcode (low rank) from NIMDM 2017 dataset."""
        # BT35 6BP (Drumgullion 1) has NIMDM 2017 Rank 70 - high deprivation
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT35 6BP", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 70

    def test_ni_low_deprivation_postcode(self, api_client):
        """Test a low deprivation postcode (high rank) from NIMDM 2017 dataset."""
        # BT4 3QL (Stormont 2) has NIMDM 2017 Rank 889 - very low deprivation
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT4 3QL", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 889

    def test_ni_rosetta_postcode(self, api_client):
        """Test Rosetta postcode returns expected NIMDM data."""
        # BT7 3FH (Rosetta 1) has NIMDM 2017 Rank 846
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT7 3FH", "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["imd_rank"] == 846

    def test_invalid_year_2019_for_ni_returns_error(self, api_client):
        """Test that year 2019 returns an error for NI postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF", "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_year_2020_for_ni_returns_error(self, api_client):
        """Test that year 2020 returns an error for NI postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF", "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_year_2025_for_ni_returns_error(self, api_client):
        """Test that year 2025 returns an error for NI postcodes."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "BT52 1PF", "year": 2025},
        )
        assert response.status_code == 400

    def test_missing_postcode_returns_error(self, api_client):
        """Test that missing postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_postcode_returns_error(self, api_client):
        """Test that an invalid postcode returns an error."""
        response = api_client.get(
            INDICES_OF_MULTIPLE_DEPRIVATION_URL,
            {"postcode": "INVALID123", "year": 2017},
        )
        assert response.status_code == 400


@pytest.mark.django_db
class TestNorthernIrelandIndexOfMultipleDeprivationQuantile:
    """Tests for the index_of_multiple_deprivation_quantile endpoint using NI NIMDM 2017 data."""

    def test_valid_ni_postcode_returns_quantile_data(self, api_client):
        """Test that a valid NI postcode returns quantile data."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]
        assert "data_quantile" in data["result"]

    def test_ni_quantile_default_year_is_2017(self, api_client):
        """Test that the default year for NI postcodes is 2017 when not specified."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "rank" in data["result"]

    # Tests for BT48 7ET (Strand 1 Derry) - Rank 5, Decile 1, Quintile 1, Quartile 1 (high deprivation)

    def test_ni_decile_derry_matches_expected(self, api_client):
        """Test that decile matches expected value for Strand 1 Derry (high deprivation)."""
        # BT48 7ET has NIMDM 2017 Rank 5 and Decile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT48 7ET", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 5
        assert data["data_quantile"] == 1

    def test_ni_quintile_derry_matches_expected(self, api_client):
        """Test that quintile matches expected value for Strand 1 Derry."""
        # BT48 7ET has NIMDM 2017 Rank 5 and Quintile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT48 7ET", "quantile": 5, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 5
        assert data["data_quantile"] == 1
        assert data["requested_quantile"] == 5
        assert data["requested_quantile_name"] == "quintile"

    def test_ni_quartile_derry_matches_expected(self, api_client):
        """Test that quartile matches expected value for Strand 1 Derry."""
        # BT48 7ET has NIMDM 2017 Rank 5 and Quartile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT48 7ET", "quantile": 4, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 5
        assert data["data_quantile"] == 1
        assert data["requested_quantile"] == 4
        assert data["requested_quantile_name"] == "quartile"

    # Tests for BT4 3QL (Stormont 2) - Rank 889, Decile 10, Quintile 5, Quartile 4 (low deprivation)

    def test_ni_decile_stormont_matches_expected(self, api_client):
        """Test that decile matches expected value for Stormont 2 (low deprivation)."""
        # BT4 3QL has NIMDM 2017 Rank 889 and Decile 10
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT4 3QL", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 889
        assert data["data_quantile"] == 10

    def test_ni_quintile_stormont_matches_expected(self, api_client):
        """Test that quintile matches expected value for Stormont 2."""
        # BT4 3QL has NIMDM 2017 Rank 889 and Quintile 5
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT4 3QL", "quantile": 5, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 889
        assert data["data_quantile"] == 5

    def test_ni_quartile_stormont_matches_expected(self, api_client):
        """Test that quartile matches expected value for Stormont 2."""
        # BT4 3QL has NIMDM 2017 Rank 889 and Quartile 4
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT4 3QL", "quantile": 4, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 889
        assert data["data_quantile"] == 4

    # Tests for BT52 1PF (Central Coleraine) - Rank 137, Decile 2, Quintile 1, Quartile 1

    def test_ni_decile_coleraine_matches_expected(self, api_client):
        """Test that decile matches expected value for Central Coleraine."""
        # BT52 1PF has NIMDM 2017 Rank 137 and Decile 2
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 137
        assert data["data_quantile"] == 2

    def test_ni_quintile_coleraine_matches_expected(self, api_client):
        """Test that quintile matches expected value for Central Coleraine."""
        # BT52 1PF has NIMDM 2017 Rank 137 and Quintile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 5, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 137
        assert data["data_quantile"] == 1

    def test_ni_quartile_coleraine_matches_expected(self, api_client):
        """Test that quartile matches expected value for Central Coleraine."""
        # BT52 1PF has NIMDM 2017 Rank 137 and Quartile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 4, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 137
        assert data["data_quantile"] == 1

    # Tests for BT7 3FH (Rosetta 1) - Rank 846, Decile 10, Quintile 5, Quartile 4

    def test_ni_decile_rosetta_matches_expected(self, api_client):
        """Test that decile matches expected value for Rosetta 1."""
        # BT7 3FH has NIMDM 2017 Rank 846 and Decile 10
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT7 3FH", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 846
        assert data["data_quantile"] == 10

    def test_ni_quintile_rosetta_matches_expected(self, api_client):
        """Test that quintile matches expected value for Rosetta 1."""
        # BT7 3FH has NIMDM 2017 Rank 846 and Quintile 5
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT7 3FH", "quantile": 5, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 846
        assert data["data_quantile"] == 5

    def test_ni_quartile_rosetta_matches_expected(self, api_client):
        """Test that quartile matches expected value for Rosetta 1."""
        # BT7 3FH has NIMDM 2017 Rank 846 and Quartile 4
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT7 3FH", "quantile": 4, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 846
        assert data["data_quantile"] == 4

    # Tests for BT35 6BP (Drumgullion 1) - Rank 70, Decile 1, Quintile 1, Quartile 1

    def test_ni_decile_drumgullion_matches_expected(self, api_client):
        """Test that decile matches expected value for Drumgullion 1."""
        # BT35 6BP has NIMDM 2017 Rank 70 and Decile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT35 6BP", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 70
        assert data["data_quantile"] == 1

    def test_ni_quintile_drumgullion_matches_expected(self, api_client):
        """Test that quintile matches expected value for Drumgullion 1."""
        # BT35 6BP has NIMDM 2017 Rank 70 and Quintile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT35 6BP", "quantile": 5, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 70
        assert data["data_quantile"] == 1

    def test_ni_quartile_drumgullion_matches_expected(self, api_client):
        """Test that quartile matches expected value for Drumgullion 1."""
        # BT35 6BP has NIMDM 2017 Rank 70 and Quartile 1
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT35 6BP", "quantile": 4, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["rank"] == 70
        assert data["data_quantile"] == 1

    def test_ni_country_is_northern_ireland(self, api_client):
        """Test that country field is 'northern_ireland' for NI postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2017},
        )
        assert response.status_code == 200
        data = response.json()["result"]
        assert data["country"] == "northern_ireland"

    # Error handling tests

    def test_missing_quantile_returns_error(self, api_client):
        """Test that missing quantile parameter returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_quantile_returns_error(self, api_client):
        """Test that an invalid quantile value returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 15, "year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_quantile_zero_returns_error(self, api_client):
        """Test that quantile=0 returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 0, "year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_quantile_negative_returns_error(self, api_client):
        """Test that a negative quantile value returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": -1, "year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_quantile_100_returns_error(self, api_client):
        """Test that quantile=100 (out of valid range) returns a 400 error."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 100, "year": 2017},
        )
        assert response.status_code == 400

    def test_invalid_year_2019_for_ni_returns_error(self, api_client):
        """Test that year 2019 returns an error for NI postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 400

    def test_invalid_year_2020_for_ni_returns_error(self, api_client):
        """Test that year 2020 returns an error for NI postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2020},
        )
        assert response.status_code == 400

    def test_invalid_year_2025_for_ni_returns_error(self, api_client):
        """Test that year 2025 returns an error for NI postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "BT52 1PF", "quantile": 10, "year": 2025},
        )
        assert response.status_code == 400

    def test_all_valid_quantiles_work(self, api_client):
        """Test that all valid quantile values work for NI data."""
        valid_quantiles = [2, 3, 4, 5, 6, 7, 8, 10, 12, 18, 20]
        for quantile in valid_quantiles:
            response = api_client.get(
                INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
                {"postcode": "BT52 1PF", "quantile": quantile, "year": 2017},
            )
            assert response.status_code == 200, f"Failed for quantile {quantile}"
            data = response.json()["result"]
            assert data["requested_quantile"] == quantile
