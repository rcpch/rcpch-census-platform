"""
Tests for batch (multiple postcode) support on the
index_of_multiple_deprivation_quantile endpoint.

The endpoint is country-agnostic: each postcode's country is detected from the
postcode itself, so a single request can mix English, Welsh, Scottish and
Northern Irish postcodes.

Expected values mirror those used in the nation-specific test files, which are
derived from the seeded IMD datasets (English IMD 2019/2025, WIMD 2019,
SIMD 2020, NIMDM 2017).
"""

import pytest
from unittest.mock import patch

from tests.conftest import MockResponse
from tests.postcode_mock_data import get_mock_postcode_response

INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL = "/index_of_multiple_deprivation_quantile"

# Expected IMD ranks per postcode (dataset year noted per nation)
EXPECTED_RANKS = {
    "SE1 7PB": {"country": "england", "year": 2019, "rank": 21865, "decile": 7},
    "CF10 3NQ": {"country": "wales", "year": 2019, "rank": 833, "decile": 5},
    "KW1 4AA": {"country": "scotland", "year": 2020, "rank": 1555, "decile": 3},
    "BT52 1PF": {"country": "northern_ireland", "year": 2017, "rank": 137, "decile": 2},
}

pytestmark = pytest.mark.django_db


class TestQuantileBatchMultiplePostcodes:
    """Tests for supplying multiple postcodes to the quantile endpoint."""

    def test_single_postcode_keeps_legacy_response_shape(self, api_client):
        """A single postcode must still return the original {"result": ...} shape."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        data = response.json()
        assert "result" in data
        assert "results" not in data
        assert data["result"]["rank"] == 21865
        assert data["result"]["country"] == "england"

    def test_comma_separated_postcodes_mixed_nations(self, api_client):
        """Comma-separated postcodes from all four UK nations resolve in one request."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,CF10 3NQ,KW1 4AA,BT52 1PF", "quantile": 10},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert len(results) == 4

        # Results are returned in the order supplied
        assert [r["postcode"] for r in results] == [
            "SE1 7PB",
            "CF10 3NQ",
            "KW1 4AA",
            "BT52 1PF",
        ]

        by_postcode = {r["postcode"]: r for r in results}
        for postcode, expected in EXPECTED_RANKS.items():
            item = by_postcode[postcode]
            # Default year for each nation is used when year is omitted
            assert item["country"] == expected["country"]
            assert item["year"] == expected["year"]
            assert item["rank"] == expected["rank"]
            assert item["data_quantile"] == expected["decile"]
            assert item["requested_quantile"] == 10
            assert item["requested_quantile_name"] == "decile"
            assert item["error"] is None

    def test_repeated_postcode_parameters(self, api_client):
        """Repeated postcode query parameters are also accepted."""
        response = api_client.get(
            f"{INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL}"
            "?postcode=SE1%207PB&postcode=M1%205AL&quantile=10&year=2019"
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert [r["postcode"] for r in results] == ["SE1 7PB", "M1 5AL"]
        assert results[0]["rank"] == 21865
        assert results[1]["rank"] == 8998

    def test_spaces_and_empty_entries_are_tolerated(self, api_client):
        """Whitespace around commas and empty entries do not break the batch."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": " SE1 7PB , , CF10 3NQ,", "quantile": 10},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert [r["postcode"] for r in results] == ["SE1 7PB", "CF10 3NQ"]

    def test_unknown_postcode_returns_error_item_without_failing_batch(
        self, api_client
    ):
        """An unresolvable postcode becomes an error item; valid postcodes still resolve."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,ZZ9 9ZZ", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        results = response.json()["results"]

        assert results[0]["postcode"] == "SE1 7PB"
        assert results[0]["error"] is None
        assert results[0]["rank"] == 21865

        assert results[1]["postcode"] == "ZZ9 9ZZ"
        assert results[1]["error"] == "Could not get LSOA from postcode."
        assert results[1]["rank"] is None
        assert results[1]["data_quantile"] is None
        assert results[1]["country"] is None

    def test_terminated_postcode_returns_error_item(self, api_client):
        """A terminated postcode is reported per item rather than failing the batch."""

        def terminated_side_effect(url, **kwargs):
            if "/terminated_postcodes/" in url:
                return MockResponse(
                    {
                        "status": 200,
                        "result": {
                            "postcode": "B1 1AA",
                            "year_termination": 2010,
                        },
                    },
                    200,
                )
            postcode = url.split("/postcodes/")[-1]
            if postcode.replace(" ", "").upper() == "B11AA":
                # Active postcode lookup 404s so the terminated endpoint is tried
                return MockResponse({"status": 404, "error": "Postcode not found"}, 404)
            mock_data = get_mock_postcode_response(postcode)
            if mock_data is None:
                return MockResponse({"status": 404, "error": "Postcode not found"}, 404)
            return MockResponse(mock_data, 200)

        with patch(
            "deprivation_scores.general_functions.postcode.requests.get",
            side_effect=terminated_side_effect,
        ):
            response = api_client.get(
                INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
                {"postcode": "SE1 7PB,B1 1AA", "quantile": 10, "year": 2019},
            )

        assert response.status_code == 200
        results = response.json()["results"]
        assert results[0]["error"] is None
        assert results[0]["rank"] == 21865
        assert results[1]["postcode"] == "B1 1AA"
        assert results[1]["error"] == "Terminated postcode."
        assert results[1]["rank"] is None

    def test_year_invalid_for_one_nation_only_errors_that_postcode(self, api_client):
        """An explicit year that a nation does not publish only errors those postcodes."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,KW1 4AA", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        results = response.json()["results"]

        assert results[0]["error"] is None
        assert results[0]["rank"] == 21865

        assert results[1]["postcode"] == "KW1 4AA"
        assert results[1]["error"] == "Year must be 2020 for Scotland."
        assert results[1]["rank"] is None

    def test_explicit_year_valid_for_all_supplied_nations(self, api_client):
        """An explicit year applies to every postcode when valid for each nation."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,CF10 3NQ", "quantile": 5, "year": 2019},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert all(r["error"] is None for r in results)
        assert results[0]["year"] == 2019
        assert results[1]["year"] == 2019

    def test_invalid_global_year_returns_400(self, api_client):
        """A year that is not a published IMD dataset year is rejected outright."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,M1 5AL", "quantile": 10, "year": 2018},
        )
        assert response.status_code == 400

    def test_invalid_quantile_returns_400_for_batch(self, api_client):
        """Quantile validation is unchanged for batch requests."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,M1 5AL", "quantile": 15},
        )
        assert response.status_code == 400

    def test_missing_postcode_returns_400(self, api_client):
        """A request without any postcode is rejected."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"quantile": 10},
        )
        assert response.status_code == 400

    def test_too_many_postcodes_returns_400(self, api_client):
        """Batch requests above the maximum number of postcodes are rejected."""
        postcodes = ",".join(["SE1 7PB"] * 101)
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": postcodes, "quantile": 10},
        )
        assert response.status_code == 400

    def test_over_long_postcode_returns_error_item(self, api_client):
        """Postcodes longer than any valid UK postcode are rejected per item."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": f"SE1 7PB,{'X' * 500}", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert results[0]["error"] is None
        assert results[0]["rank"] == 21865
        assert results[1]["error"] == "Invalid postcode supplied."

    def test_single_over_long_postcode_returns_400(self, api_client):
        """A single over-long postcode is rejected with the legacy 400."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "X" * 500, "quantile": 10},
        )
        assert response.status_code == 400

    def test_path_traversal_postcode_is_an_ordinary_lookup_failure(self, api_client):
        """Malicious-looking postcodes never break the batch; they error per item."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "../../admin,SE1 7PB", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert results[0]["error"] == "Could not get LSOA from postcode."
        assert results[1]["error"] is None
        assert results[1]["rank"] == 21865


class TestQuantileBatchIncludeFullIndices:
    """Tests for the include_full_indices option."""

    def test_single_postcode_includes_full_indices(self, api_client):
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {
                "postcode": "SE1 7PB",
                "quantile": 10,
                "year": 2019,
                "include_full_indices": "true",
            },
        )
        assert response.status_code == 200
        result = response.json()["result"]
        assert result["rank"] == 21865
        indices = result["indices"]
        assert indices["imd_rank"] == 21865
        assert indices["imd_decile"] == 7
        assert indices["type"] == "England"
        # England-specific domain present
        assert "idaci_rank" in indices

    def test_batch_includes_country_specific_indices(self, api_client):
        """Each batch item carries the full indices for its own nation's dataset."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {
                "postcode": "SE1 7PB,CF10 3NQ,KW1 4AA,BT52 1PF",
                "quantile": 10,
                "include_full_indices": "true",
            },
        )
        assert response.status_code == 200
        by_postcode = {r["postcode"]: r for r in response.json()["results"]}

        england = by_postcode["SE1 7PB"]["indices"]
        assert england["type"] == "England"
        assert england["imd_rank"] == 21865
        assert "idaci_rank" in england

        wales = by_postcode["CF10 3NQ"]["indices"]
        assert wales["type"] == "Wales"
        assert wales["imd_rank"] == 833
        assert "housing_rank" in wales

        scotland = by_postcode["KW1 4AA"]["indices"]
        assert scotland["type"] == "Scotland"
        assert scotland["imd_rank"] == 1555
        assert scotland["data_zone"]["data_zone_code"] == "S01010782"

        northern_ireland = by_postcode["BT52 1PF"]["indices"]
        assert northern_ireland["type"] == "Northern Ireland"
        assert northern_ireland["imd_rank"] == 137
        assert northern_ireland["soa"]["soa_code"] == "95JJ05W1"

    def test_error_items_have_null_indices_when_requested(self, api_client):
        """Error items keep a uniform shape with a null indices key."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {
                "postcode": "SE1 7PB,ZZ9 9ZZ",
                "quantile": 10,
                "year": 2019,
                "include_full_indices": "true",
            },
        )
        assert response.status_code == 200
        results = response.json()["results"]
        assert results[0]["indices"] is not None
        assert results[1]["error"] == "Could not get LSOA from postcode."
        assert results[1]["indices"] is None

    def test_full_indices_omitted_by_default(self, api_client):
        """Without the flag, responses contain no indices key (backwards compatible)."""
        response = api_client.get(
            INDEX_OF_MULTIPLE_DEPRIVATION_QUANTILE_URL,
            {"postcode": "SE1 7PB,M1 5AL", "quantile": 10, "year": 2019},
        )
        assert response.status_code == 200
        for item in response.json()["results"]:
            assert "indices" not in item
