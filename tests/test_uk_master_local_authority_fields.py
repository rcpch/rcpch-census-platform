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


# ---------------------------------------------------------------------------
# Health boundary column presence
# ---------------------------------------------------------------------------

_HEALTH_COLS = {
    "nhser_code",
    "nhser_name",
    "icb_code",
    "icb_name",
    "lhb_code",
    "lhb_name",
}
_SKIP_REASON_HEALTH = (
    "uk_master tile tables not present — run 'seed --mode process_geometries' first"
)

_HEALTH_VIEW_SKIP_REASON = (
    "health boundary views not present — run 'seed --mode process_geometries' first"
)


def _skip_if_no_health_views(cursor):
    """Skip if the nhser_tiles_2021 view hasn't been created."""
    cursor.execute(
        """
        SELECT COUNT(*) FROM information_schema.tables
        WHERE table_schema = 'public'
          AND table_name = 'nhser_tiles_2021'
        """
    )
    if cursor.fetchone()[0] == 0:
        pytest.skip(_HEALTH_VIEW_SKIP_REASON)


@pytest.mark.django_db
def test_uk_master_tables_expose_health_boundary_fields():
    """UK master tile tables must include all six health boundary columns."""
    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('uk_master_2011_z8_10', 'uk_master_2021_z8_10')
              AND column_name IN ('nhser_code', 'nhser_name', 'icb_code', 'icb_name',
                                  'lhb_code', 'lhb_name')
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

    assert found["uk_master_2011_z8_10"] == _HEALTH_COLS, (
        f"uk_master_2011_z8_10 missing health columns: "
        f"{_HEALTH_COLS - found['uk_master_2011_z8_10']}"
    )
    assert found["uk_master_2021_z8_10"] == _HEALTH_COLS, (
        f"uk_master_2021_z8_10 missing health columns: "
        f"{_HEALTH_COLS - found['uk_master_2021_z8_10']}"
    )


# ---------------------------------------------------------------------------
# Health boundary data population
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_uk_master_2011_england_health_fields_populated():
    """England rows in uk_master_2011_z8_10 must have nhser_code and icb_code populated."""
    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE nhser_code IS NULL) AS null_nhser_code,
                COUNT(*) FILTER (WHERE nhser_name IS NULL) AS null_nhser_name,
                COUNT(*) FILTER (WHERE icb_code IS NULL) AS null_icb_code,
                COUNT(*) FILTER (WHERE icb_name IS NULL) AS null_icb_name
            FROM public.uk_master_2011_z8_10
            WHERE nation = 'england'
            """
        )
        total, null_nhser_code, null_nhser_name, null_icb_code, null_icb_name = (
            cursor.fetchone()
        )

    assert total > 0, "No England rows in uk_master_2011_z8_10"
    assert null_nhser_code == 0, f"{null_nhser_code} England rows missing nhser_code"
    assert null_nhser_name == 0, f"{null_nhser_name} England rows missing nhser_name"
    assert null_icb_code == 0, f"{null_icb_code} England rows missing icb_code"
    assert null_icb_name == 0, f"{null_icb_name} England rows missing icb_name"


@pytest.mark.django_db
def test_uk_master_2011_wales_lhb_fields_populated():
    """Wales rows in uk_master_2011_z8_10 must have lhb_code and lhb_name populated."""
    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT
                COUNT(*) AS total,
                COUNT(*) FILTER (WHERE lhb_code IS NULL) AS null_lhb_code,
                COUNT(*) FILTER (WHERE lhb_name IS NULL) AS null_lhb_name
            FROM public.uk_master_2011_z8_10
            WHERE nation = 'wales'
            """
        )
        total, null_lhb_code, null_lhb_name = cursor.fetchone()

    assert total > 0, "No Wales rows in uk_master_2011_z8_10"
    assert null_lhb_code == 0, f"{null_lhb_code} Wales rows missing lhb_code"
    assert null_lhb_name == 0, f"{null_lhb_name} Wales rows missing lhb_name"


@pytest.mark.django_db
def test_uk_master_2011_health_fields_null_outside_nation():
    """
    Scotland and NI rows must have all health fields null.
    England rows must have lhb_* null.
    Wales rows must have nhser_* and icb_* null.
    """
    with connection.cursor() as cursor:
        _skip_if_no_tile_tables(cursor)
        cursor.execute(
            """
            SELECT
                nation,
                COUNT(*) FILTER (WHERE nhser_code IS NOT NULL) AS has_nhser,
                COUNT(*) FILTER (WHERE icb_code IS NOT NULL)   AS has_icb,
                COUNT(*) FILTER (WHERE lhb_code IS NOT NULL)   AS has_lhb
            FROM public.uk_master_2011_z8_10
            GROUP BY nation
            """
        )
        rows = {
            nation: (has_nhser, has_icb, has_lhb)
            for nation, has_nhser, has_icb, has_lhb in cursor.fetchall()
        }

    # Scotland: no health fields
    if "scotland" in rows:
        has_nhser, has_icb, has_lhb = rows["scotland"]
        assert has_nhser == 0, f"Scotland rows unexpectedly have nhser_code"
        assert has_icb == 0, f"Scotland rows unexpectedly have icb_code"
        assert has_lhb == 0, f"Scotland rows unexpectedly have lhb_code"

    # Northern Ireland: no health fields
    if "northern_ireland" in rows:
        has_nhser, has_icb, has_lhb = rows["northern_ireland"]
        assert has_nhser == 0, f"NI rows unexpectedly have nhser_code"
        assert has_icb == 0, f"NI rows unexpectedly have icb_code"
        assert has_lhb == 0, f"NI rows unexpectedly have lhb_code"

    # England: no lhb fields
    if "england" in rows:
        _, _, has_lhb = rows["england"]
        assert has_lhb == 0, f"England rows unexpectedly have lhb_code"

    # Wales: no nhser/icb fields
    if "wales" in rows:
        has_nhser, has_icb, _ = rows["wales"]
        assert has_nhser == 0, f"Wales rows unexpectedly have nhser_code"
        assert has_icb == 0, f"Wales rows unexpectedly have icb_code"


# ---------------------------------------------------------------------------
# Health boundary tile views
# ---------------------------------------------------------------------------


@pytest.mark.django_db
def test_health_boundary_views_exist_and_are_populated():
    """nhser_tiles_2021, icb_tiles_2023, and lhb_tiles_2022 must exist and have rows."""
    views = {
        "nhser_tiles_2021": 7,  # 7 NHS England Regions
        "icb_tiles_2023": 42,  # 42 ICBs
        "lhb_tiles_2022": 7,  # 7 Local Health Boards in Wales
    }

    with connection.cursor() as cursor:
        _skip_if_no_health_views(cursor)

        for view_name, expected_min in views.items():
            cursor.execute(f"SELECT COUNT(*) FROM public.{view_name}")
            count = cursor.fetchone()[0]
            assert (
                count >= expected_min
            ), f"{view_name} has {count} rows, expected at least {expected_min}"


@pytest.mark.django_db
def test_health_boundary_views_expose_required_columns():
    """Each health boundary view must expose code, area_name, nation, year, and geom."""
    required = {"code", "area_name", "nation", "year", "geom"}
    view_names = ["nhser_tiles_2021", "icb_tiles_2023", "lhb_tiles_2022"]

    with connection.cursor() as cursor:
        _skip_if_no_health_views(cursor)
        cursor.execute(
            """
            SELECT table_name, column_name
            FROM information_schema.columns
            WHERE table_schema = 'public'
              AND table_name IN ('nhser_tiles_2021', 'icb_tiles_2023', 'lhb_tiles_2022')
              AND column_name IN ('code', 'area_name', 'nation', 'year', 'geom')
            ORDER BY table_name, column_name
            """
        )
        rows = cursor.fetchall()

    found = {v: set() for v in view_names}
    for table_name, column_name in rows:
        found[table_name].add(column_name)

    for view_name in view_names:
        assert (
            found[view_name] == required
        ), f"{view_name} missing columns: {required - found[view_name]}"


@pytest.mark.django_db
def test_health_boundary_views_have_no_null_geometry():
    """All rows in each health boundary view must have non-null geometry."""
    view_names = ["nhser_tiles_2021", "icb_tiles_2023", "lhb_tiles_2022"]

    with connection.cursor() as cursor:
        _skip_if_no_health_views(cursor)

        for view_name in view_names:
            cursor.execute(
                f"SELECT COUNT(*) FROM public.{view_name} WHERE geom IS NULL"
            )
            null_count = cursor.fetchone()[0]
            assert (
                null_count == 0
            ), f"{view_name} has {null_count} rows with null geometry"
