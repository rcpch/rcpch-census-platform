import pytest
from django.db import connection

_SKIP_REASON = (
    "uk_master tile tables not present — run 'seed --mode process_geometries' first"
)


def _skip_if_no_tile_tables(cursor):
    """Call pytest.skip() inside a test if the uk_master tables haven't been built."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'uk_master_2011_z8_10'
        """
    )
    if cursor.fetchone()[0] == 0:
        pytest.skip(_SKIP_REASON)


@pytest.mark.django_db
def test_uk_master_tables_expose_local_authority_fields():
    """UK master tile tables should expose LA metadata columns for tooltips."""
    expected_columns = {"la_code", "la_name", "la_year"}

    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('uk_master_2011_z8_10', 'uk_master_2021_z8_10')
              AND column_name IN ('la_code', 'la_name', 'la_year')
            ORDER BY table_name, column_name
            """
        )
        rows = cursor.fetchall()

    found = {
        "uk_master_2011_z8_10": set(),
        "uk_master_2021_z8_10": set(),
    }
    for table_name, column_name in rows:
        found[table_name].add(column_name)

    assert found["uk_master_2011_z8_10"] == expected_columns
    assert found["uk_master_2021_z8_10"] == expected_columns


@pytest.mark.django_db
def test_uk_master_2011_local_authority_population_by_nation():
    """
    LA metadata should be populated for England/Wales/Scotland and null for NI.
    """
    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT nation,
                   COUNT(*) AS total_rows,
                   COUNT(*) FILTER (WHERE la_code IS NULL) AS null_la_code,
                   COUNT(*) FILTER (WHERE la_name IS NULL) AS null_la_name,
                   COUNT(*) FILTER (WHERE la_year IS NULL) AS null_la_year
            FROM public.uk_master_2011_z8_10
            GROUP BY nation
            ORDER BY nation
            """
        )
        rows = cursor.fetchall()

    by_nation = {
        nation: {
            "total_rows": total_rows,
            "null_la_code": null_la_code,
            "null_la_name": null_la_name,
            "null_la_year": null_la_year,
        }
        for nation, total_rows, null_la_code, null_la_name, null_la_year in rows
    }

    for nation in ["england", "wales", "scotland"]:
        assert nation in by_nation, f"Missing nation in tile table: {nation}"
        assert by_nation[nation]["total_rows"] > 0
        assert by_nation[nation]["null_la_code"] == 0
        assert by_nation[nation]["null_la_name"] == 0
        assert by_nation[nation]["null_la_year"] == 0

    assert "northern_ireland" in by_nation
    assert by_nation["northern_ireland"]["total_rows"] > 0
    assert (
        by_nation["northern_ireland"]["null_la_code"]
        == by_nation["northern_ireland"]["total_rows"]
    )
    assert (
        by_nation["northern_ireland"]["null_la_name"]
        == by_nation["northern_ireland"]["total_rows"]
    )
    assert (
        by_nation["northern_ireland"]["null_la_year"]
        == by_nation["northern_ireland"]["total_rows"]
    )
