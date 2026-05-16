import csv
from enum import Enum
import io
from math import floor
import requests
from shapely.geometry import MultiPolygon
import sys
from decimal import Decimal
import geopandas as gpd
import pandas as pd
from sqlalchemy import create_engine
from django.core.management.base import BaseCommand, CommandError
from django.db import connection
from django.conf import settings
from ...models import (
    LSOA,
    LocalAuthority,
    GreenSpace,
    DataZone,
    SOA,
    EnglishIndexMultipleDeprivation,
    WelshIndexMultipleDeprivation,
    ScottishIndexMultipleDeprivation,
    NorthernIrelandIndexMultipleDeprivation,
    PopulationDensity,
)


class QuantileType(Enum):
    QUARTILE = "quartile"
    QUINTILE = "quintile"
    DECILE = "decile"


IMD_2019_DOMAINS_OF_DEPRIVATION = "File_2_-_IoD2019_Domains_of_Deprivation.csv"
IMD_2019_SUBDOMAINS_OF_DEPRIVATION = "File_4_-_IoD2019_Sub-domains_of_Deprivation.csv"
IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION = (
    "File_3_-_IoD2019_Supplementary_Indices_-_IDACI_and_IDAOPI.csv"
)
IMD_2019_SCORES_OF_DEPRIVATION = "File_5_-_IoD2019_Scores.csv"
IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION = "File_9_-_IoD2019_Transformed_Scores.csv"
IMD_2019_LSOA_2015_POPULATION_DENOMINATORS = (
    "File_6_-_IoD2019_Population_Denominators.csv"
)
LSOA_2011_WARD_LAD_2019 = "Lower_Layer_Super_Output_Area_(2011)_to_Ward_(2019)_Lookup_in_England_and_Wales.csv"

IMD_2025_DOMAINS_OF_DEPRIVATION = "File_2_IoD2025_Domains_of_Deprivation.csv"
IMD_2025_SUBDOMAINS_OF_DEPRIVATION = "File_4_IoD2025_Sub-domains_of_Deprivation.csv"
IMD_2025_SUPPLEMENTARY_INDICES_OF_DEPRIVATION = (
    "File_3_IoD2025_Supplementary_Indices_IDACI_and_IDAOPI.csv"
)
IMD_2025_SCORES_OF_DEPRIVATION = (
    "File_5_IoD2025_Scores_for_the_Indices_of_Deprivation.csv"
)
IMD_2025_TRANSFORMED_SCORES_OF_DEPRIVATION = (
    "File_9_IoD2025_Transformed_Domain_Scores.csv"
)

LSOA_2021_WARD_LAD_2024 = (
    "LSOA_(2021)_to_Electoral_Ward_(2024)_to_LAD_(2024)_Best_Fit_Lookup_in_EW.csv"
)

SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES = "scottish_dz_lookup.csv"
ACCESS_TO_GREEN_SPACE = "access_to_green_space.csv"  # 2020 data https://www.ons.gov.uk/economy/environmentalaccounts/datasets/accesstogardensandpublicgreenspaceingreatbritain

IMD_WALES_DEPRIVATION_DOMAINS_RANKS = (
    "welsh-index-multiple-deprivation-2019-index-and-domain-ranks-by-small-area.csv"
)

IMD_WALES_DEPRIVATION_SCORES = "wimd-2019-index-and-domain-scores-by-small-area.csv"
IMD_SCOTLAND_RANKS = "SIMD+2020v2.csv"
NORTHERN_IRELAND_SOAS_AND_IMD_RANKS = "NIMDM17_SOAresults.csv"

POPULATION_DENSITIES = "Access_to_Natural_Green_Space_Inequalities__(LSOA).csv"


W = "\033[0m"  # white (normal)
R = "\033[31m"  # red
G = "\033[32m"  # green
B = "\033[34m"  # blue
P = "\033[35m"  # purple
BOLD = "\033[1m"
END = "\033[0m"


def get_table_year_counts(table_name, year):
    """Return total and spatialized row counts for a given table/year."""
    with connection.cursor() as cursor:
        cursor.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE year = %s",
            [year],
        )
        total_row = cursor.fetchone()
        total_rows = total_row[0] if total_row else 0

        cursor.execute(
            f"SELECT COUNT(*) FROM {table_name} WHERE year = %s AND geom IS NOT NULL",
            [year],
        )
        spatialized_row = cursor.fetchone()
        spatialized_rows = spatialized_row[0] if spatialized_row else 0

    return {
        "total_rows": total_rows,
        "spatialized_rows": spatialized_rows,
    }


class Command(BaseCommand):
    help = "seed database with census and IMD data for England, Wales, Scotland and Northern Ireland."

    def _get_dataset_spatial_status(self, dataset):
        table_name = dataset["table"]
        year = dataset["year"]

        counts = get_table_year_counts(table_name, year)
        total_rows = counts["total_rows"]
        spatialized_rows = counts["spatialized_rows"]

        is_complete = total_rows > 0 and total_rows == spatialized_rows

        return {
            "total_rows": total_rows,
            "spatialized_rows": spatialized_rows,
            "is_complete": is_complete,
        }

    def _run_post_processing_sql(self, layers=None):
        self.stdout.write(
            self.style.WARNING(
                "\n🚀 Running high-performance PostGIS optimizations and building UK-wide views..."
            )
        )

        # --- Nested SQL Helpers ---

        def get_lsoa_view_sql(view_name, geom_column, boundary_year):
            """Creates individual England/Wales Table filtered by boundary year"""
            return f"""
            -- 1. Clean up table (main cleanup section handles views)
            DROP TABLE IF EXISTS public.{view_name} CASCADE;

            -- 2. Create as a TABLE, not a VIEW
            CREATE TABLE public.{view_name} AS
            SELECT 
                l.year::int as year,
                l.{geom_column}::geometry(MultiPolygon, 3857) AS geom,
                l.lsoa_code::text,
                l.lsoa_name::text AS area_name,
                COALESCE(e.imd_decile, w.imd_decile, 0)::int as imd_decile,
                COALESCE(e.imd_rank, w.imd_rank, 0)::int as imd_rank
            FROM deprivation_scores_lsoa l
            LEFT JOIN deprivation_scores_englishindexmultipledeprivation e 
                ON e.lsoa_id = l.id
            LEFT JOIN deprivation_scores_welshindexmultipledeprivation w
                ON w.lsoa_id = l.id
            WHERE l.{geom_column} IS NOT NULL 
            AND l.year = {boundary_year};

            -- 3. Index it!
            CREATE INDEX idx_{view_name}_geom ON public.{view_name} USING GIST (geom);
            ANALYZE public.{view_name};
            """

        def get_uk_master_view_sql(view_name, geom_suffix, boundary_year, imd_year):
            """
            Creates UK Master View combining all 4 nations with IMD data.

            Boundary year mapping:
            - England/Wales LSOAs: 2011 (for IMD 2019) or 2021 (for IMD 2025)
            - Scotland datazones: Always 2011
            - N. Ireland SOAs: Always 2001

            IMD year mapping:
            - England: 2019 or 2025 (passed as imd_year)
            - Wales: Always 2019
            - Scotland: Always 2020
            - Northern Ireland: Always 2017
            """
            actual_geom_col = (
                "geom_3857" if geom_suffix == "3857" else f"geom_3857_{geom_suffix}"
            )

            # Fixed boundary years for Scotland and NI
            wales_boundary_year = 2011
            scotland_boundary_year = 2011
            ni_boundary_year = 2001

            # Fixed IMD years for Wales, Scotland and NI
            wales_imd_year = 2019
            scotland_imd_year = 2020
            ni_imd_year = 2017

            return f"""
            -- 1. Clean up table (main cleanup section handles views)
            DROP TABLE IF EXISTS public.{view_name} CASCADE;

            -- 2. Materialize the data into a physical TABLE for performance
            CREATE TABLE public.{view_name} AS
            -- ENGLAND
            SELECT 
                l.year::int AS year, 
                {imd_year}::int AS imd_year, 
                l.lsoa_code::text AS code, 
                l.lsoa_name::text AS area_name,
                la.local_authority_district_code::text AS la_code,
                la.local_authority_district_name::text AS la_name,
                la.year::int AS la_year,
                nh.nhser_code::text AS nhser_code,
                nh.nhser_name::text AS nhser_name,
                icb.icb_code::text AS icb_code,
                icb.icb_name::text AS icb_name,
                NULL::text AS lhb_code,
                NULL::text AS lhb_name,
                ST_MakeValid(ST_Multi(l.{actual_geom_col}))::geometry(MultiPolygon, 3857) AS geom, 
                'england'::text AS nation,
                COALESCE(e.imd_decile, 0)::int AS imd_decile
            FROM deprivation_scores_lsoa l
            LEFT JOIN deprivation_scores_englishindexmultipledeprivation e 
                ON e.lsoa_id = l.id AND e.year = {imd_year}
            LEFT JOIN deprivation_scores_localauthority la
                ON la.id = l.local_authority_district_id
            LEFT JOIN LATERAL (
                SELECT r.nhser_code, r.nhser_name
                FROM deprivation_scores_nhsenglishregion r
                WHERE r.year = 2021
                  AND r.geom_3857 IS NOT NULL
                  AND ST_Contains(r.geom_3857, ST_PointOnSurface(l.{actual_geom_col}))
                LIMIT 1
            ) nh ON TRUE
            LEFT JOIN LATERAL (
                SELECT b.icb_code, b.icb_name
                FROM deprivation_scores_integratedcareboard b
                WHERE b.year = 2023
                  AND b.geom_3857 IS NOT NULL
                  AND ST_Contains(b.geom_3857, ST_PointOnSurface(l.{actual_geom_col}))
                LIMIT 1
            ) icb ON TRUE
            WHERE l.lsoa_code LIKE 'E%' 
                AND l.{actual_geom_col} IS NOT NULL 
                AND l.year = {boundary_year}
            
            UNION ALL
            
            -- WALES (Always uses 2019 IMD)
            SELECT 
                l.year::int AS year, 
                {wales_imd_year}::int AS imd_year, 
                l.lsoa_code::text AS code, 
                l.lsoa_name::text AS area_name,
                la.local_authority_district_code::text AS la_code,
                la.local_authority_district_name::text AS la_name,
                la.year::int AS la_year,
                NULL::text AS nhser_code,
                NULL::text AS nhser_name,
                NULL::text AS icb_code,
                NULL::text AS icb_name,
                lhb.lhb_code::text AS lhb_code,
                lhb.lhb_name::text AS lhb_name,
                ST_MakeValid(ST_Multi(l.{actual_geom_col}))::geometry(MultiPolygon, 3857) AS geom, 
                'wales'::text AS nation,
                COALESCE(w.imd_decile, 0)::int AS imd_decile
            FROM deprivation_scores_lsoa l
            LEFT JOIN deprivation_scores_welshindexmultipledeprivation w 
                ON w.lsoa_id = l.id AND w.year = {wales_imd_year}
            LEFT JOIN deprivation_scores_localauthority la
                ON la.id = l.local_authority_district_id
            LEFT JOIN LATERAL (
                SELECT h.lhb_code, h.lhb_name
                FROM deprivation_scores_localhealthboard h
                WHERE h.year = 2022
                  AND h.geom_3857 IS NOT NULL
                  AND ST_Contains(h.geom_3857, ST_PointOnSurface(l.{actual_geom_col}))
                LIMIT 1
            ) lhb ON TRUE
            WHERE l.lsoa_code LIKE 'W%' 
                AND l.{actual_geom_col} IS NOT NULL 
                AND l.year = {wales_boundary_year}

            UNION ALL

            -- SCOTLAND (Always uses 2011 boundaries and 2020 IMD)
            SELECT 
                d.year::int AS year, 
                {scotland_imd_year}::int AS imd_year, 
                d.data_zone_code::text AS code, 
                d.data_zone_name::text AS area_name,
                la.local_authority_district_code::text AS la_code,
                la.local_authority_district_name::text AS la_name,
                la.year::int AS la_year,
                NULL::text AS nhser_code,
                NULL::text AS nhser_name,
                NULL::text AS icb_code,
                NULL::text AS icb_name,
                NULL::text AS lhb_code,
                NULL::text AS lhb_name,
                ST_MakeValid(ST_Multi(d.{actual_geom_col}))::geometry(MultiPolygon, 3857) AS geom, 
                'scotland'::text AS nation,
                COALESCE(WIDTH_BUCKET(s.imd_rank, 1, 6977, 10), 0)::int AS imd_decile
            FROM deprivation_scores_datazone d
            LEFT JOIN deprivation_scores_scottishindexmultipledeprivation s 
                ON s.data_zone_id = d.id AND s.year = {scotland_imd_year}
            LEFT JOIN deprivation_scores_localauthority la
                ON la.id = d.local_authority_id
            WHERE d.{actual_geom_col} IS NOT NULL 
                AND d.year = {scotland_boundary_year}

            UNION ALL

            -- NORTHERN IRELAND (Always uses 2001 boundaries and 2017 IMD)
            SELECT 
                so.year::int AS year, 
                {ni_imd_year}::int AS imd_year, 
                so.soa_code::text AS code, 
                so.soa_name::text AS area_name,
                NULL::text AS la_code,
                NULL::text AS la_name,
                NULL::int AS la_year,
                NULL::text AS nhser_code,
                NULL::text AS nhser_name,
                NULL::text AS icb_code,
                NULL::text AS icb_name,
                NULL::text AS lhb_code,
                NULL::text AS lhb_name,
                ST_MakeValid(ST_Multi(so.{actual_geom_col}))::geometry(MultiPolygon, 3857) AS geom, 
                'northern_ireland'::text AS nation,
                COALESCE(WIDTH_BUCKET(ni.imd_rank, 1, 891, 10), 0)::int AS imd_decile
            FROM deprivation_scores_soa so
            LEFT JOIN deprivation_scores_northernirelandindexmultipledeprivation ni 
                ON ni.soa_id = so.id AND ni.year = {ni_imd_year}
            WHERE so.{actual_geom_col} IS NOT NULL 
                AND so.year = {ni_boundary_year}

            UNION ALL

            -- CHANNEL ISLANDS / CROWN DEPENDENCIES (Guernsey, Isle of Man, Jersey — year 2024, no IMD)
            SELECT
                ci.year::int AS year,
                NULL::int AS imd_year,
                ci.code::text AS code,
                ci.name::text AS area_name,
                NULL::text AS la_code,
                NULL::text AS la_name,
                NULL::int AS la_year,
                NULL::text AS nhser_code,
                NULL::text AS nhser_name,
                NULL::text AS icb_code,
                NULL::text AS icb_name,
                NULL::text AS lhb_code,
                NULL::text AS lhb_name,
                ST_MakeValid(ST_Multi(ci.{actual_geom_col}))::geometry(MultiPolygon, 3857) AS geom,
                'channel_islands'::text AS nation,
                0::int AS imd_decile
            FROM deprivation_scores_channelisland ci
            WHERE ci.{actual_geom_col} IS NOT NULL
                AND ci.year = 2024;

            -- 3. Create Spatial Index (Removes 500 errors by speeding up BBOX queries)
            CREATE INDEX idx_{view_name}_geom ON public.{view_name} USING GIST (geom);
            
            -- 4. Gather statistics for the query planner
            ANALYZE public.{view_name};
            """

        def get_health_boundary_view_sql(
            view_name, source_table, code_column, name_column, year, nation, geom_column
        ):
            """Create a zoom-banded health boundary tile table."""
            return f"""
            DROP TABLE IF EXISTS public.{view_name} CASCADE;

            CREATE TABLE public.{view_name} AS
            SELECT
                year::int AS year,
                {code_column}::text AS code,
                {name_column}::text AS area_name,
                ST_MakeValid(ST_Multi({geom_column}))::geometry(MultiPolygon, 3857) AS geom,
                '{nation}'::text AS nation
            FROM {source_table}
            WHERE year = {year}
              AND {geom_column} IS NOT NULL;

            CREATE INDEX idx_{view_name}_geom ON public.{view_name} USING GIST (geom);
            ANALYZE public.{view_name};
            """

        def get_la_tile_sql(table_name, geom_column):
            """Create a zoom-banded local authority tile table."""
            return f"""
            DROP TABLE IF EXISTS public.{table_name} CASCADE;

            CREATE TABLE public.{table_name} AS
            SELECT
                year::int AS year,
                local_authority_district_code::text AS lad_code,
                ST_MakeValid(ST_Multi({geom_column}))::geometry(MultiPolygon, 3857) AS geom
            FROM deprivation_scores_localauthority
            WHERE {geom_column} IS NOT NULL;

            CREATE INDEX idx_{table_name}_geom ON public.{table_name} USING GIST (geom);
            ANALYZE public.{table_name};
            """

        # --- Layer resolution ---
        _ALL_LAYERS = frozenset(
            {
                "lsoas",
                "uk-master",
                "local-authorities",
                "nhs-regions",
                "integrated-care-boards",
                "local-health-boards",
                "channel-islands",
            }
        )
        if layers is None or "all" in layers:
            _active = _ALL_LAYERS
        else:
            _active = set(layers)
            if "health-geographies" in _active:
                _active.discard("health-geographies")
                _active |= {
                    "nhs-regions",
                    "integrated-care-boards",
                    "local-health-boards",
                }

        def want(*names):
            return any(n in _active for n in names)

        self.stdout.write(
            self.style.SUCCESS(f"  Active layer groups: {', '.join(sorted(_active))}")
        )

        # --- SQL Statement List (conditionally built by layer group) ---

        sql_statements = [
            # Section 1: Schema setup (always run — ADD COLUMN IF NOT EXISTS is idempotent and fast)
            "ALTER TABLE deprivation_scores_lsoa ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_lsoa ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_lsoa ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_lsoa ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_datazone ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_datazone ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_datazone ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_datazone ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_soa ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_soa ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_soa ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_soa ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localauthority ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localauthority ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localauthority ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localauthority ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_nhsenglishregion ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_nhsenglishregion ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_nhsenglishregion ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_nhsenglishregion ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_integratedcareboard ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_integratedcareboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_integratedcareboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_integratedcareboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localhealthboard ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localhealthboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localhealthboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_localhealthboard ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_channelisland ADD COLUMN IF NOT EXISTS geom_3857 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_channelisland ADD COLUMN IF NOT EXISTS geom_3857_simp_z0_4 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_channelisland ADD COLUMN IF NOT EXISTS geom_3857_simp_z5_7 geometry(MultiPolygon,3857);",
            "ALTER TABLE deprivation_scores_channelisland ADD COLUMN IF NOT EXISTS geom_3857_simp_z8_10 geometry(MultiPolygon,3857);",
        ]

        # Section 2: Cleanup (conditional per layer group)
        if want("uk-master"):
            sql_statements += [
                "DROP TABLE IF EXISTS public.uk_master_2011_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2011_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2011_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2011_z11_14 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2021_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2021_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2021_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.uk_master_2021_z11_14 CASCADE;",
            ]
        if want("lsoas"):
            sql_statements += [
                "DROP TABLE IF EXISTS public.lsoa_tiles_2011_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2011_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2011_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2011_z11_14 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2021_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2021_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2021_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.lsoa_tiles_2021_z11_14 CASCADE;",
            ]
        if want("local-authorities"):
            sql_statements += [
                """
            DO $$
            DECLARE
                relkind_char char;
            BEGIN
                SELECT c.relkind INTO relkind_char
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'la_tiles';

                IF relkind_char = 'r' THEN
                    EXECUTE 'DROP TABLE public.la_tiles CASCADE';
                ELSIF relkind_char = 'v' THEN
                    EXECUTE 'DROP VIEW public.la_tiles CASCADE';
                ELSIF relkind_char = 'm' THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.la_tiles CASCADE';
                END IF;
            END $$;
            """,
                "DROP TABLE IF EXISTS public.la_tiles_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.la_tiles_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.la_tiles_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.la_tiles_z11_14 CASCADE;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                """
            DO $$
            DECLARE
                relkind_char char;
            BEGIN
                SELECT c.relkind INTO relkind_char
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'nhser_tiles_2021';

                IF relkind_char = 'r' THEN
                    EXECUTE 'DROP TABLE public.nhser_tiles_2021 CASCADE';
                ELSIF relkind_char = 'v' THEN
                    EXECUTE 'DROP VIEW public.nhser_tiles_2021 CASCADE';
                ELSIF relkind_char = 'm' THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.nhser_tiles_2021 CASCADE';
                END IF;
            END $$;
            """,
                "DROP TABLE IF EXISTS public.nhser_tiles_2021_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.nhser_tiles_2021_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.nhser_tiles_2021_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.nhser_tiles_2021_z11_14 CASCADE;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                """
            DO $$
            DECLARE
                relkind_char char;
            BEGIN
                SELECT c.relkind INTO relkind_char
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'icb_tiles_2023';

                IF relkind_char = 'r' THEN
                    EXECUTE 'DROP TABLE public.icb_tiles_2023 CASCADE';
                ELSIF relkind_char = 'v' THEN
                    EXECUTE 'DROP VIEW public.icb_tiles_2023 CASCADE';
                ELSIF relkind_char = 'm' THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.icb_tiles_2023 CASCADE';
                END IF;
            END $$;
            """,
                "DROP TABLE IF EXISTS public.icb_tiles_2023_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.icb_tiles_2023_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.icb_tiles_2023_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.icb_tiles_2023_z11_14 CASCADE;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                """
            DO $$
            DECLARE
                relkind_char char;
            BEGIN
                SELECT c.relkind INTO relkind_char
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'lhb_tiles_2022';

                IF relkind_char = 'r' THEN
                    EXECUTE 'DROP TABLE public.lhb_tiles_2022 CASCADE';
                ELSIF relkind_char = 'v' THEN
                    EXECUTE 'DROP VIEW public.lhb_tiles_2022 CASCADE';
                ELSIF relkind_char = 'm' THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.lhb_tiles_2022 CASCADE';
                END IF;
            END $$;
            """,
                "DROP TABLE IF EXISTS public.lhb_tiles_2022_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.lhb_tiles_2022_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.lhb_tiles_2022_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.lhb_tiles_2022_z11_14 CASCADE;",
            ]
        if want("channel-islands"):
            sql_statements += [
                """
            DO $$
            DECLARE
                relkind_char char;
            BEGIN
                SELECT c.relkind INTO relkind_char
                FROM pg_class c
                JOIN pg_namespace n ON n.oid = c.relnamespace
                WHERE n.nspname = 'public' AND c.relname = 'channel_islands_tiles';

                IF relkind_char = 'r' THEN
                    EXECUTE 'DROP TABLE public.channel_islands_tiles CASCADE';
                ELSIF relkind_char = 'v' THEN
                    EXECUTE 'DROP VIEW public.channel_islands_tiles CASCADE';
                ELSIF relkind_char = 'm' THEN
                    EXECUTE 'DROP MATERIALIZED VIEW public.channel_islands_tiles CASCADE';
                END IF;
            END $$;
            """,
                "DROP TABLE IF EXISTS public.channel_islands_tiles_z0_4 CASCADE;",
                "DROP TABLE IF EXISTS public.channel_islands_tiles_z5_7 CASCADE;",
                "DROP TABLE IF EXISTS public.channel_islands_tiles_z8_10 CASCADE;",
                "DROP TABLE IF EXISTS public.channel_islands_tiles_z11_14 CASCADE;",
            ]

        # Section 3: Geoprocessing (WGS84 -> Web Mercator 3857)
        if want("lsoas"):
            sql_statements += [
                "UPDATE deprivation_scores_lsoa SET geom_3857 = ST_MakeValid(geom_3857) WHERE NOT ST_IsValid(geom_3857);",
                "UPDATE deprivation_scores_lsoa SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
                "UPDATE deprivation_scores_datazone SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
                "UPDATE deprivation_scores_soa SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]
        if want("local-authorities"):
            sql_statements += [
                "UPDATE deprivation_scores_localauthority SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                "UPDATE deprivation_scores_nhsenglishregion SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                "UPDATE deprivation_scores_integratedcareboard SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                "UPDATE deprivation_scores_localhealthboard SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]
        if want("channel-islands"):
            sql_statements += [
                "UPDATE deprivation_scores_channelisland SET geom_3857 = ST_Transform(geom, 3857) WHERE geom_3857 IS NULL AND geom IS NOT NULL;",
            ]

        # Section 4: Simplification
        # Compute all simplification tiers in a single pass per table to reduce write overhead.
        # z0-4: 1,500 m, z5-7: 200 m, z8-10: 60 m (all in EPSG:3857 metres).
        if want("lsoas"):
            sql_statements += [
                "UPDATE deprivation_scores_lsoa SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
                "UPDATE deprivation_scores_datazone SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
                "UPDATE deprivation_scores_soa SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]
        if want("local-authorities"):
            sql_statements += [
                "UPDATE deprivation_scores_localauthority SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                "UPDATE deprivation_scores_nhsenglishregion SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                "UPDATE deprivation_scores_integratedcareboard SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                "UPDATE deprivation_scores_localhealthboard SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]
        if want("channel-islands"):
            sql_statements += [
                "UPDATE deprivation_scores_channelisland SET geom_3857_simp_z0_4 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 1500)), 3)), geom_3857_simp_z5_7 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 200)), 3)), geom_3857_simp_z8_10 = ST_Multi(ST_CollectionExtract(ST_MakeValid(ST_SimplifyPreserveTopology(geom_3857, 60)), 3)) WHERE geom_3857 IS NOT NULL;",
            ]

        # Section 5: Spatial indexing & clustering
        if want("lsoas"):
            sql_statements += [
                # Raw geometry indexes (for z11+ and raw queries)
                "CREATE INDEX IF NOT EXISTS idx_lsoa_3857 ON deprivation_scores_lsoa USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_datazone_3857 ON deprivation_scores_datazone USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_soa_3857 ON deprivation_scores_soa USING GIST (geom_3857);",
                # Simplified geometry indexes (critical for tile performance)
                "CREATE INDEX IF NOT EXISTS idx_lsoa_simp_z0_4 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_lsoa_simp_z5_7 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_lsoa_simp_z8_10 ON deprivation_scores_lsoa USING GIST (geom_3857_simp_z8_10);",
                "CREATE INDEX IF NOT EXISTS idx_datazone_simp_z0_4 ON deprivation_scores_datazone USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_datazone_simp_z5_7 ON deprivation_scores_datazone USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_datazone_simp_z8_10 ON deprivation_scores_datazone USING GIST (geom_3857_simp_z8_10);",
                "CREATE INDEX IF NOT EXISTS idx_soa_simp_z0_4 ON deprivation_scores_soa USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_soa_simp_z5_7 ON deprivation_scores_soa USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_soa_simp_z8_10 ON deprivation_scores_soa USING GIST (geom_3857_simp_z8_10);",
                "CREATE INDEX IF NOT EXISTS idx_lsoa_year_id ON deprivation_scores_lsoa (year, id);",
                "CREATE INDEX IF NOT EXISTS idx_english_imd_year_lsoa ON deprivation_scores_englishindexmultipledeprivation (year, lsoa_id);",
                "CREATE INDEX IF NOT EXISTS idx_welsh_imd_year_lsoa ON deprivation_scores_welshindexmultipledeprivation (year, lsoa_id);",
                "CLUSTER deprivation_scores_lsoa USING idx_lsoa_simp_z5_7;",
                "CLUSTER deprivation_scores_datazone USING idx_datazone_simp_z5_7;",
                "CLUSTER deprivation_scores_soa USING idx_soa_simp_z5_7;",
            ]
        if want("local-authorities"):
            sql_statements += [
                "CREATE INDEX IF NOT EXISTS idx_localauthority_3857 ON deprivation_scores_localauthority USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_localauthority_simp_z0_4 ON deprivation_scores_localauthority USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_localauthority_simp_z5_7 ON deprivation_scores_localauthority USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_localauthority_simp_z8_10 ON deprivation_scores_localauthority USING GIST (geom_3857_simp_z8_10);",
                "CLUSTER deprivation_scores_localauthority USING idx_localauthority_3857;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                "CREATE INDEX IF NOT EXISTS idx_nhsenglishregion_3857 ON deprivation_scores_nhsenglishregion USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_nhsenglishregion_simp_z0_4 ON deprivation_scores_nhsenglishregion USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_nhsenglishregion_simp_z5_7 ON deprivation_scores_nhsenglishregion USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_nhsenglishregion_simp_z8_10 ON deprivation_scores_nhsenglishregion USING GIST (geom_3857_simp_z8_10);",
                "CLUSTER deprivation_scores_nhsenglishregion USING idx_nhsenglishregion_simp_z5_7;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                "CREATE INDEX IF NOT EXISTS idx_integratedcareboard_3857 ON deprivation_scores_integratedcareboard USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_integratedcareboard_simp_z0_4 ON deprivation_scores_integratedcareboard USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_integratedcareboard_simp_z5_7 ON deprivation_scores_integratedcareboard USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_integratedcareboard_simp_z8_10 ON deprivation_scores_integratedcareboard USING GIST (geom_3857_simp_z8_10);",
                "CLUSTER deprivation_scores_integratedcareboard USING idx_integratedcareboard_simp_z5_7;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                "CREATE INDEX IF NOT EXISTS idx_localhealthboard_3857 ON deprivation_scores_localhealthboard USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_localhealthboard_simp_z0_4 ON deprivation_scores_localhealthboard USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_localhealthboard_simp_z5_7 ON deprivation_scores_localhealthboard USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_localhealthboard_simp_z8_10 ON deprivation_scores_localhealthboard USING GIST (geom_3857_simp_z8_10);",
                "CLUSTER deprivation_scores_localhealthboard USING idx_localhealthboard_simp_z5_7;",
            ]
        if want("channel-islands"):
            sql_statements += [
                "CREATE INDEX IF NOT EXISTS idx_channelisland_3857 ON deprivation_scores_channelisland USING GIST (geom_3857);",
                "CREATE INDEX IF NOT EXISTS idx_channelisland_simp_z0_4 ON deprivation_scores_channelisland USING GIST (geom_3857_simp_z0_4);",
                "CREATE INDEX IF NOT EXISTS idx_channelisland_simp_z5_7 ON deprivation_scores_channelisland USING GIST (geom_3857_simp_z5_7);",
                "CREATE INDEX IF NOT EXISTS idx_channelisland_simp_z8_10 ON deprivation_scores_channelisland USING GIST (geom_3857_simp_z8_10);",
                "CLUSTER deprivation_scores_channelisland USING idx_channelisland_simp_z5_7;",
            ]

        # Section 6: LSOA tile tables
        if want("lsoas"):
            sql_statements += [
                get_lsoa_view_sql("lsoa_tiles_2011_z0_4", "geom_3857_simp_z0_4", 2011),
                get_lsoa_view_sql("lsoa_tiles_2011_z5_7", "geom_3857_simp_z5_7", 2011),
                get_lsoa_view_sql(
                    "lsoa_tiles_2011_z8_10", "geom_3857_simp_z8_10", 2011
                ),
                get_lsoa_view_sql("lsoa_tiles_2021_z0_4", "geom_3857_simp_z0_4", 2021),
                get_lsoa_view_sql("lsoa_tiles_2021_z5_7", "geom_3857_simp_z5_7", 2021),
                get_lsoa_view_sql(
                    "lsoa_tiles_2021_z8_10", "geom_3857_simp_z8_10", 2021
                ),
                # z11-14: raw geometry — no simplification, prevents gap artifacts at high zoom
                get_lsoa_view_sql("lsoa_tiles_2011_z11_14", "geom_3857", 2011),
                get_lsoa_view_sql("lsoa_tiles_2021_z11_14", "geom_3857", 2021),
            ]

        # Section 7: UK Master tile tables
        if want("uk-master"):
            sql_statements += [
                get_uk_master_view_sql("uk_master_2011_z0_4", "simp_z0_4", 2011, 2019),
                get_uk_master_view_sql("uk_master_2011_z5_7", "simp_z5_7", 2011, 2019),
                get_uk_master_view_sql(
                    "uk_master_2011_z8_10", "simp_z8_10", 2011, 2019
                ),
                get_uk_master_view_sql("uk_master_2021_z0_4", "simp_z0_4", 2021, 2025),
                get_uk_master_view_sql("uk_master_2021_z5_7", "simp_z5_7", 2021, 2025),
                get_uk_master_view_sql(
                    "uk_master_2021_z8_10", "simp_z8_10", 2021, 2025
                ),
                # z11-14: raw geometry — no simplification, prevents gap artifacts at high zoom
                get_uk_master_view_sql("uk_master_2011_z11_14", "3857", 2011, 2019),
                get_uk_master_view_sql("uk_master_2021_z11_14", "3857", 2021, 2025),
            ]

        # Section 8: Overlay tile tables
        if want("local-authorities"):
            sql_statements += [
                get_la_tile_sql("la_tiles_z0_4", "geom_3857_simp_z0_4"),
                get_la_tile_sql("la_tiles_z5_7", "geom_3857_simp_z5_7"),
                get_la_tile_sql("la_tiles_z8_10", "geom_3857_simp_z8_10"),
                # z11-14: reuse 60 m simplification — raw LA geometry can exceed pg_tileserv's
                # vertex limit on complex coastal authorities even after tile clipping.
                get_la_tile_sql("la_tiles_z11_14", "geom_3857_simp_z8_10"),
                "CREATE VIEW public.la_tiles AS SELECT * FROM public.la_tiles_z11_14;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                get_health_boundary_view_sql(
                    "nhser_tiles_2021_z0_4",
                    "deprivation_scores_nhsenglishregion",
                    "nhser_code",
                    "nhser_name",
                    2021,
                    "england",
                    "geom_3857_simp_z0_4",
                ),
                get_health_boundary_view_sql(
                    "nhser_tiles_2021_z5_7",
                    "deprivation_scores_nhsenglishregion",
                    "nhser_code",
                    "nhser_name",
                    2021,
                    "england",
                    "geom_3857_simp_z5_7",
                ),
                get_health_boundary_view_sql(
                    "nhser_tiles_2021_z8_10",
                    "deprivation_scores_nhsenglishregion",
                    "nhser_code",
                    "nhser_name",
                    2021,
                    "england",
                    "geom_3857_simp_z8_10",
                ),
                get_health_boundary_view_sql(
                    "nhser_tiles_2021_z11_14",
                    "deprivation_scores_nhsenglishregion",
                    "nhser_code",
                    "nhser_name",
                    2021,
                    "england",
                    "geom_3857",
                ),
                "CREATE VIEW public.nhser_tiles_2021 AS SELECT * FROM public.nhser_tiles_2021_z11_14;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                get_health_boundary_view_sql(
                    "icb_tiles_2023_z0_4",
                    "deprivation_scores_integratedcareboard",
                    "icb_code",
                    "icb_name",
                    2023,
                    "england",
                    "geom_3857_simp_z0_4",
                ),
                get_health_boundary_view_sql(
                    "icb_tiles_2023_z5_7",
                    "deprivation_scores_integratedcareboard",
                    "icb_code",
                    "icb_name",
                    2023,
                    "england",
                    "geom_3857_simp_z5_7",
                ),
                get_health_boundary_view_sql(
                    "icb_tiles_2023_z8_10",
                    "deprivation_scores_integratedcareboard",
                    "icb_code",
                    "icb_name",
                    2023,
                    "england",
                    "geom_3857_simp_z8_10",
                ),
                get_health_boundary_view_sql(
                    "icb_tiles_2023_z11_14",
                    "deprivation_scores_integratedcareboard",
                    "icb_code",
                    "icb_name",
                    2023,
                    "england",
                    "geom_3857",
                ),
                "CREATE VIEW public.icb_tiles_2023 AS SELECT * FROM public.icb_tiles_2023_z11_14;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                get_health_boundary_view_sql(
                    "lhb_tiles_2022_z0_4",
                    "deprivation_scores_localhealthboard",
                    "lhb_code",
                    "lhb_name",
                    2022,
                    "wales",
                    "geom_3857_simp_z0_4",
                ),
                get_health_boundary_view_sql(
                    "lhb_tiles_2022_z5_7",
                    "deprivation_scores_localhealthboard",
                    "lhb_code",
                    "lhb_name",
                    2022,
                    "wales",
                    "geom_3857_simp_z5_7",
                ),
                get_health_boundary_view_sql(
                    "lhb_tiles_2022_z8_10",
                    "deprivation_scores_localhealthboard",
                    "lhb_code",
                    "lhb_name",
                    2022,
                    "wales",
                    "geom_3857_simp_z8_10",
                ),
                get_health_boundary_view_sql(
                    "lhb_tiles_2022_z11_14",
                    "deprivation_scores_localhealthboard",
                    "lhb_code",
                    "lhb_name",
                    2022,
                    "wales",
                    "geom_3857",
                ),
                "CREATE VIEW public.lhb_tiles_2022 AS SELECT * FROM public.lhb_tiles_2022_z11_14;",
            ]
        if want("channel-islands"):
            sql_statements += [
                get_health_boundary_view_sql(
                    "channel_islands_tiles_z0_4",
                    "deprivation_scores_channelisland",
                    "code",
                    "name",
                    2024,
                    "channel_islands",
                    "geom_3857_simp_z0_4",
                ),
                get_health_boundary_view_sql(
                    "channel_islands_tiles_z5_7",
                    "deprivation_scores_channelisland",
                    "code",
                    "name",
                    2024,
                    "channel_islands",
                    "geom_3857_simp_z5_7",
                ),
                get_health_boundary_view_sql(
                    "channel_islands_tiles_z8_10",
                    "deprivation_scores_channelisland",
                    "code",
                    "name",
                    2024,
                    "channel_islands",
                    "geom_3857_simp_z8_10",
                ),
                get_health_boundary_view_sql(
                    "channel_islands_tiles_z11_14",
                    "deprivation_scores_channelisland",
                    "code",
                    "name",
                    2024,
                    "channel_islands",
                    "geom_3857",
                ),
                "CREATE VIEW public.channel_islands_tiles AS SELECT * FROM public.channel_islands_tiles_z11_14;",
            ]

        # Section 8: Final housekeeping (GRANT always; ANALYZE/VACUUM per layer)
        sql_statements += ["GRANT SELECT ON ALL TABLES IN SCHEMA public TO PUBLIC;"]
        if want("lsoas"):
            sql_statements += [
                "ANALYZE deprivation_scores_lsoa;",
                "ANALYZE deprivation_scores_datazone;",
                "ANALYZE deprivation_scores_soa;",
                "VACUUM ANALYZE public.uk_master_2011_z0_4;",
                "VACUUM ANALYZE public.uk_master_2011_z5_7;",
                "VACUUM ANALYZE public.uk_master_2011_z8_10;",
                "VACUUM ANALYZE public.uk_master_2021_z0_4;",
                "VACUUM ANALYZE public.uk_master_2021_z5_7;",
                "VACUUM ANALYZE public.uk_master_2021_z8_10;",
                "VACUUM ANALYZE public.uk_master_2011_z11_14;",
                "VACUUM ANALYZE public.uk_master_2021_z11_14;",
                "VACUUM ANALYZE public.lsoa_tiles_2011_z11_14;",
                "VACUUM ANALYZE public.lsoa_tiles_2021_z11_14;",
            ]
        if want("local-authorities"):
            sql_statements += [
                "VACUUM ANALYZE public.la_tiles_z0_4;",
                "VACUUM ANALYZE public.la_tiles_z5_7;",
                "VACUUM ANALYZE public.la_tiles_z8_10;",
                "VACUUM ANALYZE public.la_tiles_z11_14;",
            ]
        if want("nhs-regions"):
            sql_statements += [
                "VACUUM ANALYZE public.nhser_tiles_2021_z0_4;",
                "VACUUM ANALYZE public.nhser_tiles_2021_z5_7;",
                "VACUUM ANALYZE public.nhser_tiles_2021_z8_10;",
                "VACUUM ANALYZE public.nhser_tiles_2021_z11_14;",
            ]
        if want("integrated-care-boards"):
            sql_statements += [
                "VACUUM ANALYZE public.icb_tiles_2023_z0_4;",
                "VACUUM ANALYZE public.icb_tiles_2023_z5_7;",
                "VACUUM ANALYZE public.icb_tiles_2023_z8_10;",
                "VACUUM ANALYZE public.icb_tiles_2023_z11_14;",
            ]
        if want("local-health-boards"):
            sql_statements += [
                "VACUUM ANALYZE public.lhb_tiles_2022_z0_4;",
                "VACUUM ANALYZE public.lhb_tiles_2022_z5_7;",
                "VACUUM ANALYZE public.lhb_tiles_2022_z8_10;",
                "VACUUM ANALYZE public.lhb_tiles_2022_z11_14;",
            ]
        if want("channel-islands"):
            sql_statements += [
                "ANALYZE deprivation_scores_channelisland;",
                "VACUUM ANALYZE public.channel_islands_tiles_z0_4;",
                "VACUUM ANALYZE public.channel_islands_tiles_z5_7;",
                "VACUUM ANALYZE public.channel_islands_tiles_z8_10;",
                "VACUUM ANALYZE public.channel_islands_tiles_z11_14;",
            ]

        print("[POSTPROCESS] Starting SQL post-processing...")
        with connection.cursor() as cursor:
            for statement in sql_statements:
                stmt = statement.strip()
                if not stmt:
                    continue

                print(f"[POSTPROCESS] Executing: {stmt[:100]}...")

                try:
                    cursor.execute(stmt)
                    print("[POSTPROCESS] Success")
                except Exception as e:
                    err_msg = f"SQL Error: {e}"
                    self.stderr.write(self.style.ERROR(err_msg))
                    print(f"[POSTPROCESS] ERROR: {err_msg}")

        print("[POSTPROCESS] SQL post-processing complete.")

        self.stdout.write(
            self.style.SUCCESS("✅ Post-processing and spatial optimizations complete.")
        )

    def _stream_bfc_import(self, dataset, force=False):
        source = dataset["url"]
        table_name = dataset["table"]
        year = dataset["year"]
        chunk_size = dataset.get("chunk_size", 1000)
        specific_code_col = dataset.get("code_column", "").lower()
        django_col = dataset.get("django_code_col")
        source_name_col = dataset.get("name_column", "").lower()
        django_name_col = dataset.get("django_name_col")

        # 1. Guard
        status = self._get_dataset_spatial_status(dataset)
        if status["is_complete"] and not force:
            self.stdout.write(
                self.style.SUCCESS(
                    f"  {dataset['name']} already spatialized ({status['spatialized_rows']}/{status['total_rows']}). Skipping."
                )
            )
            return

        try:
            # 2. Remote Download with simple progress log
            if source.startswith("http"):
                # Check if this is an ArcGIS REST API endpoint that needs pagination
                is_arcgis_api = "/FeatureServer/" in source or "/MapServer/" in source

                if is_arcgis_api:
                    # Pagination for ArcGIS REST API using ObjectID strategy
                    self.stdout.write(f"  Downloading from ArcGIS REST API: {source}")

                    # Step 1: Get all ObjectIDs (fast, no geometry)
                    base_url = source.split("?")[0]  # Remove existing query params

                    # Extract query params from original URL if they exist
                    query_params = {}
                    if "?" in source:
                        param_string = source.split("?")[1]
                        for param in param_string.split("&"):
                            if "=" in param:
                                key, value = param.split("=", 1)
                                query_params[key] = value

                    # Get ObjectIDs only
                    oid_url = f"{base_url}?where={query_params.get('where', '1=1')}&returnIdsOnly=true&f=json"
                    self.stdout.write("  Fetching ObjectIDs...")
                    oid_response = requests.get(oid_url, timeout=300)
                    oid_response.raise_for_status()
                    oid_data = oid_response.json()

                    if "error" in oid_data:
                        raise ValueError(
                            f"API Error: {oid_data['error'].get('message', 'Unknown error')}"
                        )

                    object_ids = oid_data.get("objectIds", [])
                    if not object_ids:
                        raise ValueError("No ObjectIDs returned from API")

                    self.stdout.write(
                        f"  Found {len(object_ids)} features. Fetching in batches..."
                    )

                    # Step 2: Fetch features in batches by ObjectID (smaller batches to avoid URL length limits)
                    all_gdfs = []
                    batch_size = 100  # Reduced from 1000 to avoid 403 Forbidden due to URL length
                    log_interval = 1000  # Log progress every 1000 features

                    import time
                    from requests.exceptions import (
                        ChunkedEncodingError,
                        ConnectionError,
                        ReadTimeout,
                        HTTPError,
                    )

                    max_retries = 4
                    retry_delay = 5

                    def fetch_batch(batch_ids, depth=0):
                        id_list = ",".join(map(str, batch_ids))
                        batch_url = (
                            f"{base_url}?objectIds={id_list}&outFields=*&f=geojson"
                        )
                        indent = "  " * (depth + 1)
                        for attempt in range(max_retries):
                            try:
                                self.stdout.write(
                                    f"{indent}Downloading batch {batch_ids[0]}-{batch_ids[-1]} (attempt {attempt+1})..."
                                )
                                batch_response = requests.get(
                                    batch_url, stream=True, timeout=300
                                )
                                batch_response.raise_for_status()
                                total_bytes = 0
                                bytes_data = io.BytesIO()
                                for chunk in batch_response.iter_content(
                                    chunk_size=1024 * 1024
                                ):
                                    if chunk:
                                        bytes_data.write(chunk)
                                        total_bytes += len(chunk)
                                self.stdout.write(
                                    f"{indent}Downloaded {total_bytes/1e6:.2f} MB for batch {batch_ids[0]}-{batch_ids[-1]}"
                                )
                                bytes_data.seek(0)
                                batch_gdf = gpd.read_file(bytes_data)
                                all_gdfs.append(batch_gdf)
                                return True
                            except HTTPError as e:
                                if e.response.status_code == 504 and len(batch_ids) > 1:
                                    self.stdout.write(
                                        f"{indent}504 Gateway Timeout for batch {batch_ids[0]}-{batch_ids[-1]}. Splitting batch..."
                                    )
                                    mid = len(batch_ids) // 2
                                    fetch_batch(batch_ids[:mid], depth + 1)
                                    fetch_batch(batch_ids[mid:], depth + 1)
                                    return True
                                else:
                                    self.stdout.write(
                                        f"{indent}HTTP Error for batch {batch_ids[0]}-{batch_ids[-1]}: {str(e)}"
                                    )
                                    break
                            except (
                                ChunkedEncodingError,
                                ConnectionError,
                                ReadTimeout,
                            ) as e:
                                self.stdout.write(
                                    f"{indent}Connection error: {e}. Retrying ({attempt+1}/{max_retries})..."
                                )
                                time.sleep(retry_delay)
                            except Exception as e:
                                self.stdout.write(
                                    f"{indent}Failed to parse batch {batch_ids[0]}-{batch_ids[-1]}: {str(e)}"
                                )
                                break
                        else:
                            self.stdout.write(
                                f"{indent}Failed to download batch {batch_ids[0]}-{batch_ids[-1]} after {max_retries} attempts. Skipping."
                            )
                        return False

                    for i in range(0, len(object_ids), batch_size):
                        batch_ids = object_ids[i : i + batch_size]
                        fetch_batch(batch_ids)

                    # Only log every 1000 features
                    total_fetched = sum(len(gdf) for gdf in all_gdfs)
                    if total_fetched % log_interval == 0 or total_fetched >= len(
                        object_ids
                    ):
                        self.stdout.write(
                            f"    Progress: {total_fetched}/{len(object_ids)} features fetched"
                        )

                    if len(all_gdfs) == 0:
                        raise ValueError("No features retrieved from API")

                    # Concatenate all batches
                    final_gdf = gpd.GeoDataFrame(pd.concat(all_gdfs, ignore_index=True))
                    self.stdout.write(
                        f"  Download complete. Total features: {len(final_gdf)}"
                    )
                else:
                    # Non-paginated download (e.g., direct JSON files)
                    self.stdout.write(f"  Starting download: {source}")
                    response = requests.get(source, stream=True, timeout=300)
                    response.raise_for_status()

                    total_size = int(response.headers.get("content-length", 0))
                    bytes_data = io.BytesIO()
                    downloaded = 0
                    last_percent = -1

                    for chunk in response.iter_content(chunk_size=chunk_size * 1024):
                        bytes_data.write(chunk)
                        if total_size > 0:
                            downloaded += len(chunk)
                            percent = int(100 * downloaded / total_size)
                            if percent % 10 == 0 and percent != last_percent:
                                self.stdout.write(f"    Download Progress: {percent}%")
                                last_percent = percent

                    self.stdout.write(
                        "  Download complete. Parsing JSON into GeoPandas..."
                    )
                    bytes_data.seek(0)
                    final_gdf = gpd.read_file(bytes_data)
            else:
                self.stdout.write(f"  Loading local file: {source}")
                final_gdf = gpd.read_file(source)

            final_gdf.columns = [c.lower() for c in final_gdf.columns]

            # 3. Geometric Processing (ONLY for Northern Ireland Small Areas that need dissolving)
            # Northern Ireland downloads ~4500 small areas that need to be dissolved into ~890 SOAs
            is_ni_small_areas = (
                table_name == "deprivation_scores_soa"
                and len(final_gdf) > 1000
                and specific_code_col in final_gdf.columns
            )

            if is_ni_small_areas:
                self.stdout.write(
                    f"  Condensing {len(final_gdf)} Small Areas into ~890 SOAs (Memory Intensive)..."
                )

                if final_gdf.crs is None:
                    final_gdf.set_crs("EPSG:29903", inplace=True)

                # Dissolve
                final_gdf = final_gdf.dissolve(by=specific_code_col).reset_index()

                # Simplify (Tolerance 1.0m)
                self.stdout.write(
                    "  Simplifying geometries for database optimization..."
                )
                final_gdf["geometry"] = final_gdf.simplify(
                    tolerance=1.0, preserve_topology=True
                )

            # 4. Standardize CRS & Geometry Type
            # Only apply Irish projection logic to Northern Ireland data
            if table_name == "deprivation_scores_soa":
                if (
                    final_gdf.crs is None
                    or final_gdf.geometry.iloc[0].centroid.x > 1000
                ):
                    final_gdf.set_crs("EPSG:29903", allow_override=True, inplace=True)

            # Ensure we have WGS84 (EPSG:4326) for database storage
            if final_gdf.crs is None:
                self.stdout.write("  Warning: No CRS detected, assuming WGS84...")
                final_gdf.set_crs("EPSG:4326", inplace=True)
            elif final_gdf.crs != "EPSG:4326":
                self.stdout.write(f"  Reprojecting from {final_gdf.crs} to WGS84...")
                final_gdf = final_gdf.to_crs("EPSG:4326")

            # Convert to MultiPolygon only if needed (preserve valid geometries)
            def ensure_multipolygon(geom):
                if geom.geom_type == "MultiPolygon":
                    return geom
                elif geom.geom_type == "Polygon":
                    return MultiPolygon([geom])
                else:
                    # For other types, try to extract polygons
                    return MultiPolygon(
                        [g for g in geom.geoms if g.geom_type == "Polygon"]
                    )

            final_gdf["geometry"] = final_gdf["geometry"].map(ensure_multipolygon)

            # 5. Database Merge
            db = settings.DATABASES["default"]
            engine = create_engine(
                f"postgresql+psycopg2://{db['USER']}:{db['PASSWORD']}@{db['HOST']}:{db.get('PORT', 5432)}/{db['NAME']}"
            )

            temp_table = f"temp_shapes_{year}"
            self.stdout.write("  Uploading shapes to PostgreSQL...")

            upload_columns = [specific_code_col, "geometry"]
            if source_name_col and source_name_col in final_gdf.columns:
                upload_columns.insert(1, source_name_col)

            final_gdf[upload_columns].to_postgis(
                temp_table, engine, if_exists="replace", index=False
            )

            # DEBUG: Check temp table geometry after to_postgis
            with connection.cursor() as cursor:
                cursor.execute(
                    f"SELECT ST_NPoints(geometry) FROM {temp_table} LIMIT 1;"
                )

                cursor.execute(
                    f"SELECT ST_GeometryType(geom), ST_SRID(geom) FROM {table_name} WHERE year = %s LIMIT 1;",
                    [year],
                )

            with connection.cursor() as cursor:
                # Health boundary tables may be empty initially; insert-or-update handles both fresh and existing rows.
                if django_name_col and source_name_col:
                    cursor.execute(
                        f"""
                        INSERT INTO {table_name} ({django_col}, {django_name_col}, year, geom)
                        SELECT t.{specific_code_col}, t.{source_name_col}, %s,
                               t.geometry::geometry(MultiPolygon, 4326)
                        FROM {temp_table} t
                        ON CONFLICT ({django_col}, year)
                        DO UPDATE SET
                            {django_name_col} = EXCLUDED.{django_name_col},
                            geom = EXCLUDED.geom;
                    """,
                        [year],
                    )
                else:
                    # Existing reference tables are pre-seeded; update geometry only.
                    cursor.execute(
                        f"""
                        UPDATE {table_name} SET geom = t.geometry::geometry(MultiPolygon, 4326)
                        FROM {temp_table} t
                        WHERE {table_name}.{django_col} = t.{specific_code_col} AND {table_name}.year = %s;
                    """,
                        [year],
                    )

                # Apply code remapping for datasets where source codes differ from DB codes
                # (e.g. Scottish councils renumbered in 2019 but stored as year=2011).
                code_remapping = dataset.get("code_remapping", {})
                for source_code, db_code in code_remapping.items():
                    cursor.execute(
                        f"""
                        UPDATE {table_name} SET geom = t.geometry::geometry(MultiPolygon, 4326)
                        FROM {temp_table} t
                        WHERE t.{specific_code_col} = %s
                          AND {table_name}.{django_col} = %s
                          AND {table_name}.year = %s;
                        """,
                        [source_code, db_code, year],
                    )
                    self.stdout.write(f"  Code remap: {source_code} -> {db_code}")

                cursor.execute(
                    f"SELECT COUNT(*) FROM {table_name} WHERE year = %s AND geom IS NOT NULL;",
                    [year],
                )
                count_row = cursor.fetchone()
                count = count_row[0] if count_row else 0

                # DEBUG: Check main table immediately after UPDATE
                cursor.execute(
                    f"SELECT ST_NPoints(geom) FROM {table_name} WHERE year = %s LIMIT 1;",
                    [year],
                )

                cursor.execute(f"DROP TABLE IF EXISTS {temp_table};")
                connection.commit()

            self.stdout.write(
                self.style.SUCCESS(f"  Successfully spatialized {count} rows.")
            )

        except Exception as e:
            self.stderr.write(self.style.ERROR(f"  Import failed: {str(e)}"))
            with connection.cursor() as cursor:
                cursor.execute(f"DROP TABLE IF EXISTS temp_shapes_{year};")

    def purge_cdn_cache(self):
        """
        Tells the CDN to clear the cached map data.
        """
        self.stdout.write(self.style.MIGRATE_LABEL("  Requesting CDN Cache Purge..."))

        # Example for Cloudflare
        zone_id = settings.CLOUDFLARE_ZONE_ID
        api_token = settings.CLOUDFLARE_API_TOKEN

        url = f"https://api.cloudflare.com/client/v4/zones/{zone_id}/purge_cache"
        headers = {
            "Authorization": f"Bearer {api_token}",
            "Content-Type": "application/json",
        }

        # We target only the map-data URLs to avoid clearing the whole site
        data = {"prefixes": [f"{settings.SITE_URL}/api/map-data/"]}

        try:
            response = requests.post(url, headers=headers, json=data, timeout=10)
            if response.status_code == 200:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ CDN Cache Purged successfully.")
                )
            else:
                self.stdout.write(
                    self.style.ERROR(f"  ❌ CDN Purge failed: {response.text}")
                )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"  ❌ CDN Purge error: {e}"))

    def warm_cache(self):
        self.stdout.write(
            self.style.HTTP_INFO("  Pre-warming cache for zoom levels...")
        )
        # We target the specific levels our views are optimized for
        for z in [3, 6, 9]:
            url = f"{settings.SITE_URL}/api/map-data/?z={z}"
            try:
                # We use a long timeout because generating the first UK-wide
                # GeoJSON from the DB can take a few seconds
                requests.get(url, timeout=120)
                self.stdout.write(f"    ✅ Cache primed for zoom {z}")
            except Exception as e:
                self.stdout.write(f"    ⚠️ Could not warm zoom {z}: {e}")

    def test_geometries(self, strict=True):
        """
        Test to ensure that the spatial data and views are correctly set up.
        """
        self.stdout.write(
            self.style.MIGRATE_LABEL("\n🔍 Validating Spatial Data & Views...")
        )

        def table_or_view_exists(cursor, name):
            if "." in name:
                schema, rel = name.split(".", 1)
            else:
                schema, rel = "public", name
            cursor.execute(
                """
                SELECT EXISTS (
                    SELECT 1 FROM information_schema.tables 
                    WHERE table_schema=%s AND table_name=%s
                    UNION
                    SELECT 1 FROM information_schema.views 
                    WHERE table_schema=%s AND table_name=%s
                )
            """,
                [schema, rel, schema, rel],
            )
            exists_row = cursor.fetchone()
            return exists_row[0] if exists_row else False

        with connection.cursor() as cursor:
            # 1. Check the 2011 Master View
            self.stdout.write("Checking 2011 Era (2019 IMD)...")
            if table_or_view_exists(cursor, "uk_master_2011_z8_10"):
                cursor.execute("""
                    SELECT nation, COUNT(*) 
                    FROM public.uk_master_2011_z8_10 
                    GROUP BY nation;
                """)
                results_2011 = cursor.fetchall()
                nations_2011 = {row[0]: row[1] for row in results_2011}
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  Skipping 2011 view check: public.uk_master_2011_z8_10 does not exist."
                    )
                )
                nations_2011 = {}

            # 2. Check the 2021 Master View
            self.stdout.write("Checking 2021 Era (2025 IMD)...")
            if table_or_view_exists(cursor, "uk_master_2021_z8_10"):
                cursor.execute("""
                    SELECT nation, COUNT(*) 
                    FROM public.uk_master_2021_z8_10 
                    GROUP BY nation;
                """)
                results_2021 = cursor.fetchall()
                nations_2021 = {row[0]: row[1] for row in results_2021}
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  Skipping 2021 view check: public.uk_master_2021_z8_10 does not exist."
                    )
                )
                nations_2021 = {}

            expected_nations = [
                "england",
                "wales",
                "scotland",
                "northern_ireland",
                "channel_islands",
            ]

            for nation in expected_nations:
                count_11 = nations_2011.get(nation, 0)
                count_21 = nations_2021.get(nation, 0)

                status = "✅" if (count_11 > 0 and count_21 > 0) else "❌"
                label = nation.replace("_", " ").title()

                self.stdout.write(
                    f"  {status} {label}: 2011({count_11}) | 2021({count_21}) polygons."
                )

            # 4. Boundary tile tier verification
            self.stdout.write(
                "Checking boundary tier tables (z0_4, z5_7, z8_10, z11_14)..."
            )
            tiered_boundaries = {
                "Local Authorities": "la_tiles",
                "NHS Regions": "nhser_tiles_2021",
                "Integrated Care Boards": "icb_tiles_2023",
                "Local Health Boards": "lhb_tiles_2022",
                "Channel Islands": "channel_islands_tiles",
            }
            tiers = ["z0_4", "z5_7", "z8_10", "z11_14"]
            boundary_failures = []

            for label, prefix in tiered_boundaries.items():
                for tier in tiers:
                    table_name = f"{prefix}_{tier}"
                    if not table_or_view_exists(cursor, table_name):
                        boundary_failures.append(
                            f"Missing required boundary table: public.{table_name}"
                        )
                        continue

                    cursor.execute(f"SELECT COUNT(*) FROM public.{table_name};")
                    row = cursor.fetchone()
                    row_count = row[0] if row else 0
                    if row_count <= 0:
                        boundary_failures.append(
                            f"Boundary table is empty: public.{table_name}"
                        )
                        status = "❌"
                    else:
                        status = "✅"

                    self.stdout.write(f"  {status} {label} {tier}: {row_count} rows")

            if boundary_failures:
                failures = "\n  - " + "\n  - ".join(boundary_failures)
                if strict:
                    raise CommandError("Boundary tier validation failed:" + failures)
                self.stdout.write(
                    self.style.WARNING(
                        "  ⚠️ Boundary tier validation findings (report-only mode):"
                        + failures
                    )
                )

            # 5. Coordinate System Verification
            if table_or_view_exists(cursor, "uk_master_2021_z8_10"):
                cursor.execute(
                    "SELECT ST_X(ST_Centroid(geom)) FROM public.uk_master_2021_z8_10 LIMIT 1;"
                )
                coord_sample = cursor.fetchone()

                if coord_sample and abs(coord_sample[0]) > 180:
                    self.stdout.write(
                        self.style.SUCCESS(
                            "  ✅ Coordinate System: Web Mercator (EPSG:3857) confirmed."
                        )
                    )
                else:
                    self.stdout.write(
                        self.style.WARNING(
                            "  ⚠️ Coordinate System: Geometry may be in degrees (WGS84). Check ST_Transform logic."
                        )
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(
                        "  Skipping coordinate system check: public.uk_master_2021_z8_10 does not exist."
                    )
                )

        self.stdout.write(self.style.SUCCESS("✨ Validation Complete.\n"))

    def add_arguments(self, parser):
        parser.add_argument("--mode", type=str, help="Mode")
        parser.add_argument(
            "--force",
            action="store_true",
            help="Force re-import even if expected records with geom already exist",
        )
        parser.add_argument(
            "--layers",
            nargs="+",
            choices=[
                "all",
                "lsoas",
                "uk-master",
                "local-authorities",
                "nhs-regions",
                "integrated-care-boards",
                "local-health-boards",
                "health-geographies",
                "channel-islands",
            ],
            default=None,
            help=(
                "Limit process_geometries to specific overlay groups. "
                "'health-geographies' expands to nhs-regions + integrated-care-boards + local-health-boards. "
                "'uk-master' rebuilds uk_master_2011_* and uk_master_2021_* tables. "
                "Omit to process all layers (equivalent to 'all')."
            ),
        )

    def handle(self, *args, **options):
        force = options.get("force", False)

        # Define the datasets to be used by the engine
        BFC_DATASETS = [
            {
                "name": "LSOA 2011 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Clipped_BFC_EW_V3_2022/FeatureServer/0/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_lsoa",
                "django_code_col": "lsoa_code",
                "year": 2011,
                "code_column": "LSOA11CD",
            },
            {
                "name": "LSOA 2021 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_2021_EW_BFE_V10_RUC/FeatureServer/3/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_lsoa",
                "django_code_col": "lsoa_code",
                "year": 2021,
                "code_column": "LSOA21CD",
            },
            {
                "name": "LAD 2011 GB BFC",
                # GB (not UK) = England + Wales + Scotland; supplies geometry for Scottish 2011 rows.
                # Four Scottish councils were renumbered in 2019; their 2011 BFC codes differ from
                # the codes stored in the DB (which came from a 2019-era lookup CSV). The
                # code_remapping dict maps old BFC code -> current DB code so the import engine
                # can patch those rows after the primary UPDATE.
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2011_GB_BFC_2022/FeatureServer/0/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_localauthority",
                "django_code_col": "local_authority_district_code",
                "year": 2011,
                "code_column": "lad11cd",  # lowercase for this service
                "chunk_size": 25,
                "code_remapping": {
                    # 2011 BFC code -> DB code (2019 code stored with year=2011)
                    "S12000015": "S12000047",  # Fife
                    "S12000024": "S12000048",  # Perth and Kinross
                    "S12000044": "S12000050",  # North Lanarkshire
                    "S12000046": "S12000049",  # Glasgow City
                },
            },
            {
                "name": "LAD 2024 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_May_2024_Boundaries_UK_BFC/FeatureServer/0/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_localauthority",
                "django_code_col": "local_authority_district_code",
                "year": 2024,
                "code_column": "LAD24CD",
                "chunk_size": 1,  # Fewer LAs
            },
            {
                "name": "LAD 2019 BFC",
                # Note the _2022 suffix and the /0/query at the end
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD_Dec_2019_Boundaries_UK_BFC_2022/FeatureServer/0/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_localauthority",
                "django_code_col": "local_authority_district_code",
                "year": 2019,
                "code_column": "lad19cd",  # MUST be lowercase for this specific service
                "chunk_size": 25,  # Very complex polygons; keep chunk size small
            },
            {
                "name": "Scotland DataZones 2011 BFC",
                "url": "https://maps.gov.scot/server/rest/services/ScotGov/StatisticalUnits/MapServer/2/query?where=1=1&outFields=*&f=geojson",
                "table": "deprivation_scores_datazone",
                "django_code_col": "data_zone_code",
                "year": 2011,
                "code_column": "DataZone",
                "chunk_size": 100,
            },
            {
                "name": "Northern Ireland SOA 2011 (Auto-Processed)",
                "url": "https://admin.opendatani.gov.uk/dataset/519e5019-6726-445d-8821-12d88f164c1e/resource/b64d8909-883e-42b1-bc79-50dc43f6769e/download/sa2011.json",
                "table": "deprivation_scores_soa",
                "django_code_col": "soa_code",
                "year": 2001,
                "code_column": "soa2011",
            },
            {
                "name": "NHS England Regions 2021 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/NHS_England_Regions_April_2021_EN_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson",
                "table": "deprivation_scores_nhsenglishregion",
                "django_code_col": "nhser_code",
                "django_name_col": "nhser_name",
                "year": 2021,
                "code_column": "NHSER21CD",
                "name_column": "NHSER21NM",
                "chunk_size": 10,  # Only 7 regions, but use 10 for safety
            },
            {
                "name": "Integrated Care Boards 2023 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Integrated_Care_Boards_April_2023_EN_BFC/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson",
                "table": "deprivation_scores_integratedcareboard",
                "django_code_col": "icb_code",
                "django_name_col": "icb_name",
                "year": 2023,
                "code_column": "ICB23CD",
                "name_column": "ICB23NM",
                "chunk_size": 20,  # ~42 ICBs
            },
            {
                "name": "Local Health Boards 2022 BFC",
                "url": "https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Health_Boards_April_2022_WA_BFC_2022/FeatureServer/0/query?where=1%3D1&outFields=*&f=geojson",
                "table": "deprivation_scores_localhealthboard",
                "django_code_col": "lhb_code",
                "django_name_col": "lhb_name",
                "year": 2022,
                "code_column": "LHB22CD",
                "name_column": "LHB22NM",
                "chunk_size": 10,  # 7 LHBs in Wales
            },
        ]

        # Channel Island / Crown Dependency datasets — kept separate from BFC_DATASETS
        # because they are small single-polygon files from different sources (not ArcGIS).
        # All share year=2024 and use INSERT...ON CONFLICT so --force is required to re-import.
        CHANNEL_ISLAND_DATASETS = [
            {
                "name": "Guernsey (geoBoundaries ADM0)",
                "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/GGY/ADM0/geoBoundaries-GGY-ADM0.geojson",
                "table": "deprivation_scores_channelisland",
                "django_code_col": "code",
                "django_name_col": "name",
                "year": 2024,
                "code_column": "shapeiso",
                "name_column": "shapename",
                "chunk_size": 1,
            },
            {
                "name": "Isle of Man (geoBoundaries ADM0)",
                "url": "https://github.com/wmgeolab/geoBoundaries/raw/9469f09/releaseData/gbOpen/IMN/ADM0/geoBoundaries-IMN-ADM0.geojson",
                "table": "deprivation_scores_channelisland",
                "django_code_col": "code",
                "django_name_col": "name",
                "year": 2024,
                "code_column": "shapeiso",
                "name_column": "shapename",
                "chunk_size": 1,
            },
            {
                "name": "Jersey (GADM v4.1 ADM0)",
                "url": "https://geodata.ucdavis.edu/gadm/gadm4.1/json/gadm41_JEY_0.json",
                "table": "deprivation_scores_channelisland",
                "django_code_col": "code",
                "django_name_col": "name",
                "year": 2024,
                "code_column": "gid_0",
                "name_column": "country",
                "chunk_size": 1,
            },
        ]

        # Update your logic here
        if options.get("mode") == "import_bfc_boundaries":
            self.stdout.write(
                "\n"
                + self.style.SUCCESS(
                    "Starting high-performance BFC boundary import via ArcGIS API..."
                )
                + "\n"
            )

            if not force:
                self.stdout.write(
                    "Preflight: checking boundary completeness by table/year..."
                )

            datasets_to_import = []
            skipped_count = 0
            for ds in BFC_DATASETS:
                status = self._get_dataset_spatial_status(ds)

                if force:
                    datasets_to_import.append(ds)
                    self.stdout.write(
                        f"  FORCE {ds['name']}: will reprocess ({status['spatialized_rows']}/{status['total_rows']} spatialized)."
                    )
                elif status["is_complete"]:
                    skipped_count += 1
                    self.stdout.write(
                        f"  SKIP  {ds['name']}: complete ({status['spatialized_rows']}/{status['total_rows']})."
                    )
                else:
                    datasets_to_import.append(ds)
                    self.stdout.write(
                        f"  RUN   {ds['name']}: incomplete ({status['spatialized_rows']}/{status['total_rows']})."
                    )

            for ds in datasets_to_import:
                self._stream_bfc_import(
                    dataset=ds,
                    force=force,
                )

            self.stdout.write(
                self.style.SUCCESS(
                    f"Boundary import preflight summary: run={len(datasets_to_import)}, skipped={skipped_count}, force={force}."
                )
            )

            # Always import channel islands as part of a full BFC import. They share year=2024
            # on the same table, so the skip-guard would fire after the first insert otherwise.
            self.stdout.write(
                self.style.SUCCESS(
                    "\nImporting Channel Island / Crown Dependency boundaries..."
                )
            )
            for ds in CHANNEL_ISLAND_DATASETS:
                self._stream_bfc_import(dataset=ds, force=True)

            # Run optimizations after all datasets are imported
            self._run_post_processing_sql()

            # Warm the local cache and then purge the remote CDN
            # if not settings.DEBUG:  # Only purge in production
            #     self.purge_cdn_cache()
            #     # Trigger the CDN to fetch the new data immediately
            #     self.warm_cache()

            # test that the tables have the correct number of geometries
            self.test_geometries(strict=True)
            return
        if options.get("mode") == "process_geometries":
            layers = options.get("layers")
            self.stdout.write(
                "\n"
                + self.style.SUCCESS(
                    "Starting SQL post-processing and spatial optimizations..."
                )
                + "\n"
            )
            self._run_post_processing_sql(layers=layers)
            partial_layers = bool(layers) and "all" not in layers
            self.test_geometries(strict=not partial_layers)
            return

        if options["mode"] == "test_geometries":
            self.test_geometries(strict=True)
            return

        if options["mode"] == "add_organisational_areas":
            self.stdout.write(B + "Adding organisational areas..." + W)
            add_lsoas_2011_wards_2019_to_LADS_2019()
            add_lsoas_2021_wards_2024_to_LADS_2024()
            add_scottish_data_zones_and_local_authorities()
            # add_2015_population_denominators()
            add_lad_access_to_outdoor_space()
        elif options["mode"] == "add_welsh_imds":
            self.stdout.write(
                "\n" + B + "Adding Welsh IMDs to existing LSOAs" + W + "\n"
            )
            add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas()
            add_welsh_2019_scores_to_existing_2011_lsoas()
        elif options["mode"] == "add_english_imds":
            self.stdout.write(
                "\n" + B + "Adding 2019 English IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_subdomains()
            update_english_imd_data_with_supplementary_indices()
            update_english_imd_data_with_scores()
            update_english_imd_data_with_transformed_scores()
            # 2025 IMD data for 2021 LSOAs
            self.stdout.write(
                "\n" + B + "Adding 2025 English IMDs to existing 2021 LSOAs" + W + "\n"
            )
            add_english_2025_deprivation_scores_and_domains_to_2021_lsoas()
            update_english_2025_imd_data_with_subdomains()
            update_english_2025_imd_data_with_supplementary_indices()
            update_english_2025_imd_data_with_scores()
            update_english_2025_imd_data_with_transformed_scores()
        elif options["mode"] == "add_scottish_imds":
            self.stdout.write(
                "\n" + B + "Adding Scottish IMDs to existing Datazones" + W + "\n"
            )
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
        elif options["mode"] == "add_northern_ireland_imds":
            self.stdout.write(
                "\n" + B + "Adding Northern Ireland SOAs and IMDs" + W + "\n"
            )
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
        elif options["mode"] == "add_population_densities":
            self.stdout.write("\n" + B + "Adding population densities..." + W + "\n")
            update_population_densities()
        elif options["mode"] == "__all__":
            self.stdout.write("\n" + B + "Seeding all data..." + W + "\n")
            self.stdout.write("\n" + B + "Adding organisational areas..." + W + "\n")
            add_lsoas_2011_wards_2019_to_LADS_2019()
            add_lsoas_2021_wards_2024_to_LADS_2024()
            add_scottish_data_zones_and_local_authorities()
            # add_2015_population_denominators()
            add_lad_access_to_outdoor_space()
            self.stdout.write(
                "\n" + B + "Adding 2019 English IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_subdomains()
            update_english_imd_data_with_supplementary_indices()
            update_english_imd_data_with_scores()
            update_english_imd_data_with_transformed_scores()
            self.stdout.write(
                "\n" + B + "Adding 2025 English IMDs to existing 2021 LSOAs" + W + "\n"
            )
            add_english_2025_deprivation_scores_and_domains_to_2021_lsoas()
            update_english_2025_imd_data_with_subdomains()
            update_english_2025_imd_data_with_supplementary_indices()
            update_english_2025_imd_data_with_scores()
            update_english_2025_imd_data_with_transformed_scores()
            self.stdout.write(
                "\n" + B + "Adding Welsh 2019 IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas()
            add_welsh_2019_scores_to_existing_2011_lsoas()
            self.stdout.write(
                "\n" + B + "Adding Scottish IMDs to existing Datazones" + W + "\n"
            )
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
            self.stdout.write(
                "\n" + B + "Adding Northern Ireland SOAs and IMDs" + W + "\n"
            )
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
            self.stdout.write("\n" + B + "Adding population densities..." + W + "\n")
            update_population_densities()
            test_table_totals()
        elif options["mode"] == "ci_test":
            # Limited seed for CI testing - only seeds data needed for tests
            self.stdout.write(
                "\n" + B + "Seeding limited data for CI testing..." + W + "\n"
            )
            # Organisational areas (LSOAs, Data Zones, etc.)
            self.stdout.write("\n" + B + "Adding organisational areas..." + W + "\n")
            add_lsoas_2011_wards_2019_to_LADS_2019()
            add_lsoas_2021_wards_2024_to_LADS_2024()
            add_scottish_data_zones_and_local_authorities()
            # English IMD data (2019 and 2025)
            self.stdout.write(
                "\n" + B + "Adding English IMD domains and scores..." + W + "\n"
            )
            add_english_deprivation_scores_and_domains_to_2011_lsoas()
            update_english_imd_data_with_scores()
            add_english_2025_deprivation_scores_and_domains_to_2021_lsoas()
            update_english_2025_imd_data_with_scores()
            # Welsh IMD data
            self.stdout.write(
                "\n" + B + "Adding Welsh 2019 IMDs to existing 2011 LSOAs" + W + "\n"
            )
            add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas()
            add_welsh_2019_scores_to_existing_2011_lsoas()
            # Scottish IMD data
            self.stdout.write(
                "\n" + B + "Adding Scottish IMDs to existing Datazones" + W + "\n"
            )
            add_scottish_deprivation_ranks_and_domains_to_2011_datazones()
            # Northern Ireland IMD data
            self.stdout.write(
                "\n" + B + "Adding Northern Ireland SOAs and IMDs" + W + "\n"
            )
            add_northern_ireland_soas_and_deprivation_domains_with_ranks()
        elif options["mode"] == "test_table_totals":
            test_table_totals()
        else:
            self.stdout.write("No options supplied...")
        self.stdout.write(image())
        self.stdout.write("done.")


"""
England and Wales LSOAs, Wards and LADS
"""


def add_lsoas_2011_wards_2019_to_LADS_2019():
    # import LSOA 2011/Ward & LAD 2019 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2011_WARD_LAD_2019}"

    if (
        LocalAuthority.objects.filter(year=2019).exists()
        and LocalAuthority.objects.filter(year=2019).count() >= 339
    ) or (
        LSOA.objects.filter(year=2011).exists()
        and LSOA.objects.filter(year=2011).count() >= 34753
    ):
        sys.stdout.write(
            "\n"
            + R
            + "2019 Local Authorities and 2011 LSOAs already added. Skipping..."
            + W
            + "\n"
        )
        return
    else:
        lad_counter = 0
        lsoa_counter = 0

        with open(path, "r") as f:
            sys.stdout.write(
                "\n"
                + G
                + "📎 Adding English & Welsh 2019 Local Authority Districts and 2011 LSOAs..."
                + W
                + "\n"
            )
            data = list(csv.reader(f, delimiter=","))

            for row in data[1:]:
                local_authority_district_2019, created = (
                    LocalAuthority.objects.get_or_create(
                        local_authority_district_code=row[5],
                        year=2019,
                        defaults={
                            "local_authority_district_name": row[6],
                        },
                    )
                )
                if created:
                    lad_counter += 1

                _, created = LSOA.objects.get_or_create(
                    lsoa_code=row[1],
                    year=2011,
                    defaults={
                        "lsoa_name": row[2],
                        "local_authority_district": local_authority_district_2019,
                    },
                )
                if created:
                    lsoa_counter += 1
        final = f"  Added total {lad_counter} local authority districts and {lsoa_counter} lsoas."
        sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
        try:
            assert lsoa_counter == 34753
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 34753 lsoa records, but got {lsoa_counter}."
                + W
                + "\n"
            )
        try:
            assert lad_counter == 339
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 339 lad records, but got {lad_counter}."
                + W
                + "\n"
            )
            pass


def add_lsoas_2021_wards_2024_to_LADS_2024():
    # import LSOA 2021/Ward & LAD 2024 boundaries
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{LSOA_2021_WARD_LAD_2024}"
    if (
        LocalAuthority.objects.filter(year=2024).exists()
        and LocalAuthority.objects.filter(year=2024).count() >= 318
    ) or (
        LSOA.objects.filter(year=2021).exists()
        and LSOA.objects.filter(year=2021).count() >= 35672
    ):
        sys.stdout.write(
            "\n"
            + R
            + "2024 Local Authorities and 2021 LSOAs already added. Skipping..."
            + W
            + "\n"
        )
        return
    else:
        lad_counter = 0
        lsoa_counter = 0

        with open(path, "r", encoding="utf-8") as f:
            sys.stdout.write(
                "\n"
                + G
                + "📎 Adding English & Welsh 2024 Local Authority Districts and 2021 LSOAs..."
                + W
                + "\n"
            )
            data = list(csv.reader(f, delimiter=","))

            for row in data[1:]:
                local_authority_district_2024, created = (
                    LocalAuthority.objects.get_or_create(
                        local_authority_district_code=row[6],
                        year=2024,
                        defaults={
                            "local_authority_district_name": row[7],
                        },
                    )
                )
                if created:
                    lad_counter += 1

                _, created = LSOA.objects.get_or_create(
                    lsoa_code=row[0],
                    year=2021,
                    defaults={
                        "lsoa_name": row[1],
                        "local_authority_district": local_authority_district_2024,
                    },
                )
                if created:
                    lsoa_counter += 1
        final = f"  Added total {lad_counter} 2024 local authority districts and {lsoa_counter} 2021 lsoas."
        sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
        try:
            assert lsoa_counter == 35672
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 35672 lsoa records, but got {lsoa_counter}."
                + W
                + "\n"
            )
        try:
            assert lad_counter == 318
        except AssertionError:
            sys.stdout.write(
                "\n"
                + R
                + f"😬 Expected 318 lad records, but got {lad_counter}."
                + W
                + "\n"
            )
            pass


"""
2019 English IMD data
"""


def add_english_deprivation_scores_and_domains_to_2011_lsoas():
    # import domains of deprivation data

    if (
        EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2011).exists()
        and EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2011).count()
        >= 32844
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English 2019 indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_DOMAINS_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English domains of deprivation to LSOAs with ranks and deciles"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if LSOA.objects.filter(lsoa_code=row[0], year=2011).exists():
                lsoa = LSOA.objects.filter(lsoa_code=row[0], year=2011).get()

                EnglishIndexMultipleDeprivation.objects.create(
                    imd_rank=int(float(row[4])),
                    imd_decile=int(float(row[5])),
                    income_rank=int(float(row[6])),
                    income_decile=int(float(row[7])),
                    employment_rank=int(float(row[8])),
                    employment_decile=int(float(row[9])),
                    education_skills_training_rank=int(float(row[10])),
                    education_skills_training_decile=int(float(row[11])),
                    health_deprivation_disability_rank=int(float(row[12])),
                    health_deprivation_disability_decile=int(float(row[13])),
                    crime_rank=int(float(row[14])),
                    crime_decile=int(float(row[15])),
                    barriers_to_housing_services_rank=int(float(row[16])),
                    barriers_to_housing_services_decile=int(float(row[17])),
                    living_environment_rank=int(float(row[18])),
                    living_environment_decile=int(float(row[19])),
                    lsoa=lsoa,
                    year=2019,
                )
                count += 1
    final = f" {count} IMD records with domains added (ranks and deciles)\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_subdomains():
    # import subdomains of deprivation data
    # Guard: check if subdomains already populated for 2019 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            year=2019, children_young_people_sub_domain_rank__isnull=False
        ).count()
        >= 32844
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2019 subdomains already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUBDOMAINS_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding 2019 sub-domains of deprivation to 2011 LSOAs"
        + W
        + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W)
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2019).update(
                children_young_people_sub_domain_rank=int(float(row[6])),
                children_young_people_sub_domain_decile=int(float(row[7])),
                adult_skills_sub_domain_rank=int(float(row[8])),
                adult_skills_sub_domain_decile=int(float(row[9])),
                geographical_barriers_sub_domain_rank=int(float(row[12])),
                geographical_barriers_sub_domain_decile=int(float(row[13])),
                wider_barriers_sub_domain_rank=int(float(row[14])),
                wider_barriers_sub_domain_decile=int(float(row[15])),
                indoors_sub_domain_rank=int(float(row[18])),
                indoors_sub_domain_decile=int(float(row[19])),
                outdoors_sub_domain_rank=int(float(row[20])),
                outdoors_sub_domain_decile=int(float(row[21])),
            )

            count += 1
    final = f" Added {count} subdomains of deprivation 2019 to LSOAs\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_supplementary_indices():
    # import domains of deprivation data
    # Guard: check if supplementary indices already populated for 2019 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            year=2019, idaci_rank__isnull=False
        ).count()
        >= 32844
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2019 supplementary indices already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2019 supplementary indices (IDACI and IDAOPI) of deprivation to 2011 LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2019).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
    final = f" Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2019 to 2011 LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_scores():
    # import domains of deprivation data
    # Guard: check if scores already populated for 2019 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            year=2019, income_score__isnull=False
        ).count()
        >= 32844
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English 2019 scores already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_SCORES_OF_DEPRIVATION}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2019 English scores of deprivation to 2011 LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2019).update(
                imd_score=Decimal(row[4]),
                income_score=Decimal(row[5]),
                employment_score=Decimal(row[6]),
                education_skills_training_score=Decimal(row[7]),
                health_deprivation_disability_score=Decimal(row[8]),
                crime_score=Decimal(row[9]),
                barriers_to_housing_services_score=Decimal(row[10]),
                living_environment_score=Decimal(row[11]),
                idaci_score=Decimal(row[12]),
                idaopi_score=Decimal(row[13]),
                children_young_people_sub_domain_score=Decimal(row[14]),
                adult_skills_sub_domain_score=Decimal(row[15]),
                geographical_barriers_sub_domain_score=Decimal(row[16]),
                wider_barriers_sub_domain_score=Decimal(row[17]),
                indoors_sub_domain_score=Decimal(row[18]),
                outdoors_sub_domain_score=Decimal(row[19]),
                year=2019,
            )
            count += 1
    final = f" Added {count} English scores of deprivation 2019\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


def update_english_imd_data_with_transformed_scores():
    # import domains of deprivation data
    # Guard: check if transformed scores already populated for 2019 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            year=2019, income_score_exponentially_transformed__isnull=False
        ).count()
        >= 32844
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2019 transformed scores already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    )
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding 2019 English transformed scores of deprivation to 2011 LSOAs"
        + W
        + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in data[1:]:
            lsoa = LSOA.objects.get(lsoa_code=row[0], year=2011)
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2019).update(
                income_score_exponentially_transformed=Decimal(row[4]),
                employment_score_exponentially_transformed=Decimal(row[5]),
                education_skills_training_score_exponentially_transformed=Decimal(
                    row[6]
                ),
                health_deprivation_disability_score_exponentially_transformed=Decimal(
                    row[7]
                ),
                crime_score_exponentially_transformed=Decimal(row[8]),
                barriers_to_housing_services_score_exponentially_transformed=Decimal(
                    row[9]
                ),
                living_environment_score_exponentially_transformed=Decimal(row[10]),
            )
            count += 1
    final = f" Added {count} English 2019 transformed scores of deprivation 2019\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )
        pass


"""
England  IMD 2025 data
"""


def add_english_2025_deprivation_scores_and_domains_to_2021_lsoas():
    """
    Import 2025 domains of deprivation data for 2021 LSOAs
    """
    if (
        EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2021).exists()
        and EnglishIndexMultipleDeprivation.objects.filter(lsoa__year=2021).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English 2025 indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_DOMAINS_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English 2025 domains of deprivation to 2021 LSOAs with ranks and deciles"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if LSOA.objects.filter(lsoa_code=row[0], year=2021).exists():
                lsoa = LSOA.objects.filter(lsoa_code=row[0], year=2021).get()

                EnglishIndexMultipleDeprivation.objects.create(
                    imd_rank=int(float(row[4])),
                    imd_decile=int(float(row[5])),
                    income_rank=int(float(row[6])),
                    income_decile=int(float(row[7])),
                    employment_rank=int(float(row[8])),
                    employment_decile=int(float(row[9])),
                    education_skills_training_rank=int(float(row[10])),
                    education_skills_training_decile=int(float(row[11])),
                    health_deprivation_disability_rank=int(float(row[12])),
                    health_deprivation_disability_decile=int(float(row[13])),
                    crime_rank=int(float(row[14])),
                    crime_decile=int(float(row[15])),
                    barriers_to_housing_services_rank=int(float(row[16])),
                    barriers_to_housing_services_decile=int(float(row[17])),
                    living_environment_rank=int(float(row[18])),
                    living_environment_decile=int(float(row[19])),
                    lsoa=lsoa,
                    year=2025,
                )
                count += 1
    final = f" {count} IMD 2025 records with domains added (ranks and deciles)\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_subdomains():
    """
    Import 2025 subdomains of deprivation data
    """
    # Guard: check if subdomains already populated for 2025 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            lsoa__year=2021, children_young_people_sub_domain_rank__isnull=False
        ).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2025 subdomains already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SUBDOMAINS_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n" + G + "📎 - Adding 2025 sub-domains of deprivation to LSOAs" + W + "\n"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W)
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
                children_young_people_sub_domain_rank=int(float(row[6])),
                children_young_people_sub_domain_decile=int(float(row[7])),
                adult_skills_sub_domain_rank=int(float(row[8])),
                adult_skills_sub_domain_decile=int(float(row[9])),
                geographical_barriers_sub_domain_rank=int(float(row[12])),
                geographical_barriers_sub_domain_decile=int(float(row[13])),
                wider_barriers_sub_domain_rank=int(float(row[14])),
                wider_barriers_sub_domain_decile=int(float(row[15])),
                indoors_sub_domain_rank=int(float(row[18])),
                indoors_sub_domain_decile=int(float(row[19])),
                outdoors_sub_domain_rank=int(float(row[20])),
                outdoors_sub_domain_decile=int(float(row[21])),
            )

            count += 1
    final = f" Added {count} subdomains of deprivation 2025 to LSOAs\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_supplementary_indices():
    """
    Import 2025 supplementary indices (IDACI and IDAOPI) data
    """
    # Guard: check if supplementary indices already populated for 2025 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            lsoa__year=2021, idaci_rank__isnull=False
        ).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2025 supplementary indices already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SUPPLEMENTARY_INDICES_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2025 supplementary indices (IDACI and IDAOPI) of deprivation to LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
                idaci_rank=int(float(row[6])),
                idaci_decile=int(float(row[7])),
                idaopi_rank=int(float(row[8])),
                idaopi_decile=int(float(row[9])),
            )
            count += 1
    final = f" Added {count} supplementary indices (IDACI and IDAOPI) of deprivation 2025 to LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_scores():
    """
    Import 2025 scores of deprivation data
    """
    # Guard: check if scores already populated for 2025 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            lsoa__year=2021, income_score__isnull=False
        ).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ English 2025 scores already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_SCORES_OF_DEPRIVATION}"
    with open(path, "r", encoding="utf-8") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding English 2025 scores of deprivation to LSOAs"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
                imd_score=Decimal(row[4]),
                income_score=Decimal(row[5]),
                employment_score=Decimal(row[6]),
                education_skills_training_score=Decimal(row[7]),
                health_deprivation_disability_score=Decimal(row[8]),
                crime_score=Decimal(row[9]),
                barriers_to_housing_services_score=Decimal(row[10]),
                living_environment_score=Decimal(row[11]),
                idaci_score=Decimal(row[12]),
                idaopi_score=Decimal(row[13]),
                children_young_people_sub_domain_score=Decimal(row[14]),
                adult_skills_sub_domain_score=Decimal(row[15]),
                geographical_barriers_sub_domain_score=Decimal(row[16]),
                wider_barriers_sub_domain_score=Decimal(row[17]),
                indoors_sub_domain_score=Decimal(row[18]),
                outdoors_sub_domain_score=Decimal(row[19]),
            )
            count += 1
    final = f" Added {count} English scores of deprivation 2025\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


def update_english_2025_imd_data_with_transformed_scores():
    """
    Import 2025 transformed scores of deprivation data
    """
    # Guard: check if transformed scores already populated for 2025 data
    if (
        EnglishIndexMultipleDeprivation.objects.filter(
            lsoa__year=2021, income_score_exponentially_transformed__isnull=False
        ).count()
        >= 33755
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ English 2025 transformed scores already exist! Skipping..."
            + W
            + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/2025/{IMD_2025_TRANSFORMED_SCORES_OF_DEPRIVATION}"
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding English 2025 transformed scores of deprivation to LSOAs"
        + W
        + "\n"
    )
    with open(path, "r", encoding="utf-8") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for row in data[1:]:
            try:
                lsoa = LSOA.objects.get(lsoa_code=row[0], year=2021)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {row[0]} not found. Skipping..." + W + "\n"
                )
                continue
            EnglishIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2025).update(
                income_score_exponentially_transformed=Decimal(row[4]),
                employment_score_exponentially_transformed=Decimal(row[5]),
                education_skills_training_score_exponentially_transformed=Decimal(
                    row[6]
                ),
                health_deprivation_disability_score_exponentially_transformed=Decimal(
                    row[7]
                ),
                crime_score_exponentially_transformed=Decimal(row[8]),
                barriers_to_housing_services_score_exponentially_transformed=Decimal(
                    row[9]
                ),
                living_environment_score_exponentially_transformed=Decimal(row[10]),
            )
            count += 1
    final = f" Added {count} English transformed scores of deprivation 2025\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 33755
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 33755 records, but got {count}." + W + "\n"
        )
        pass


"""
Scottish organisational areas and deprivation data
"""


def add_scottish_data_zones_and_local_authorities():
    """
    Add data zones and scottish local authorities
    """
    if (
        DataZone.objects.filter(year=2011).exists()
        and DataZone.objects.filter(year=2011).count() >= 6976
    ):
        sys.stdout.write(
            R + "\n⏭️ Scottish 2011 Data Zones already added. Skipping..." + W + "\n"
        )
        return

    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{SCOTTISH_DATA_ZONES_AND_LOCAL_AUTHORITIES}"
    )
    with open(path, "r", encoding="windows-1252") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding 2011 Scottish Data Zones and Local Authorities"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        lad_count = 0
        dz_count = 0
        for row in data[1:]:
            local_authority, created = LocalAuthority.objects.update_or_create(
                local_authority_district_code=row[6],
                year=2011,
                defaults={"local_authority_district_name": row[7]},
            )

            if created:
                lad_count += 1

            _, created = DataZone.objects.update_or_create(
                data_zone_code=row[0],
                year=2011,
                defaults={
                    "data_zone_name": row[1],
                    "local_authority": local_authority,
                },
            )

            if created:
                dz_count += 1
    final = (
        f"  Added {lad_count} Scottish Local Authorities and {dz_count} data zones...\n"
    )
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert dz_count == 6976
    except AssertionError:
        sys.stdout.write(
            "\n"
            + R
            + f"😬 Expected 6976 data zone records, but got {dz_count}."
            + W
            + "\n"
        )
    try:
        assert lad_count == 32
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32 lad records, but got {lad_count}." + W + "\n"
        )
        pass


def add_scottish_deprivation_ranks_and_domains_to_2011_datazones():
    # import domains of deprivation data

    if (
        ScottishIndexMultipleDeprivation.objects.filter(data_zone__year=2011).exists()
        and ScottishIndexMultipleDeprivation.objects.filter(
            data_zone__year=2011
        ).count()
        >= 6976
    ):
        sys.stdout.write(
            R + "\n⏭️ Scottish 2020 indices already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_SCOTLAND_RANKS}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding Scottish domains of deprivation to data zones with ranks"
            + W
            + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            if DataZone.objects.filter(data_zone_code=row[0], year=2011).exists():
                data_zone = DataZone.objects.filter(
                    data_zone_code=row[0], year=2011
                ).get()

                ScottishIndexMultipleDeprivation.objects.create(
                    imd_rank=row[2],
                    version=2,
                    income_rank=round(float(row[6])),
                    employment_rank=round(float(row[7])),
                    education_rank=round(float(row[8])),
                    health_rank=round(float(row[9])),
                    access_rank=round(float(row[10])),
                    crime_rank=round(float(row[11])),
                    housing_rank=round(float(row[12])),
                    data_zone=data_zone,
                    year=2020,
                )
                count += 1

    final = f" {count} Scottish IMD records with domains added (ranks).\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final + W + "\n")
    try:
        assert count == 6976
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 6976 records, but got {count}." + W + "\n"
        )
        pass


"""
Welsh deprivation data
"""


def add_welsh_2019_domains_and_ranks_to_existing_2011_lsoas():
    """
    import Welsh domains and ranks 2019 data
    """
    if (
        WelshIndexMultipleDeprivation.objects.filter(year=2019).exists()
        and WelshIndexMultipleDeprivation.objects.filter(year=2019).count() >= 1909
    ):
        sys.stdout.write(
            R + "\n⏭️ Welsh 2019 indices already present. Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_DOMAINS_RANKS}"
    with open(path, "r") as f:
        sys.stdout.write("\n" + G + "📎 - Adding Welsh IMD ranks/quantiles" + W + "\n")
        data = list(csv.reader(f, delimiter=","))
        count = 0
        for record in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=record[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    "\n" + R + f"⏭️ LSOA {record[0]} not found. Skipping..." + W + "\n"
                )
                continue
            WelshIndexMultipleDeprivation.objects.create(
                imd_rank=int(record[3]),
                imd_quartile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.QUARTILE
                ),
                imd_quintile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.QUINTILE
                ),
                imd_decile=quantile_for_rank(
                    rank=int(record[3]), quantile=QuantileType.DECILE
                ),
                imd_score=None,
                income_rank=int(record[4]),
                income_quartile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.QUARTILE
                ),
                income_quintile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.QUINTILE
                ),
                income_decile=quantile_for_rank(
                    rank=int(record[4]), quantile=QuantileType.DECILE
                ),
                income_score=None,
                employment_rank=int(record[5]),
                employment_quartile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.QUARTILE
                ),
                employment_quintile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.QUINTILE
                ),
                employment_decile=quantile_for_rank(
                    rank=int(record[5]), quantile=QuantileType.DECILE
                ),
                employment_score=None,
                health_rank=int(record[6]),
                health_quartile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.QUARTILE
                ),
                health_quintile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.QUINTILE
                ),
                health_decile=quantile_for_rank(
                    rank=int(record[6]), quantile=QuantileType.DECILE
                ),
                health_score=None,
                education_rank=int(record[7]),
                education_quartile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.QUARTILE
                ),
                education_quintile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.QUINTILE
                ),
                education_decile=quantile_for_rank(
                    rank=int(record[7]), quantile=QuantileType.DECILE
                ),
                education_score=None,
                access_to_services_rank=int(record[8]),
                access_to_services_quartile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.QUARTILE
                ),
                access_to_services_quintile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.QUINTILE
                ),
                access_to_services_decile=quantile_for_rank(
                    rank=int(record[8]), quantile=QuantileType.DECILE
                ),
                access_to_services_score=None,
                housing_rank=int(record[9]),
                housing_quartile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.QUARTILE
                ),
                housing_quintile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.QUINTILE
                ),
                housing_decile=quantile_for_rank(
                    rank=int(record[9]), quantile=QuantileType.DECILE
                ),
                housing_score=None,
                community_safety_rank=int(record[10]),
                community_safety_quartile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.QUARTILE
                ),
                community_safety_quintile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.QUINTILE
                ),
                community_safety_decile=quantile_for_rank(
                    rank=int(record[10]), quantile=QuantileType.DECILE
                ),
                community_safety_score=None,
                physical_environment_rank=int(record[11]),
                physical_environment_quartile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.QUARTILE
                ),
                physical_environment_quintile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.QUINTILE
                ),
                physical_environment_decile=quantile_for_rank(
                    rank=int(record[11]), quantile=QuantileType.DECILE
                ),
                physical_environment_score=None,
                lsoa=lsoa,
                year=2019,
            )
            count += 1
    final = f" Added {count} Welsh IMD ranks/quantiles.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)  # should be 1909
    try:
        assert count == 1909
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 1909 records, but got {count}." + W + "\n"
        )
        pass


def add_welsh_2019_scores_to_existing_2011_lsoas():
    """
    import Welsh IMD scores 2019 and add to existing ranks/imds
    """
    # Guard: check if Welsh scores already populated
    if (
        WelshIndexMultipleDeprivation.objects.filter(
            year=2019, income_score__isnull=False
        ).count()
        >= 1909
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ Welsh 2019 scores already exist! Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_WALES_DEPRIVATION_SCORES}"
    with open(path, "r") as f:
        sys.stdout.write(G + "\n📎 - Adding Welsh IMD scores" + W + "\n")
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for record in data[1:]:  # skip the first row
            try:
                lsoa = LSOA.objects.get(lsoa_code=record[0], year=2011)
            except LSOA.DoesNotExist:
                sys.stderr.write(
                    R + f"\n⏭️ LSOA {record[0]} not found. Skipping..." + W + "\n"
                )
                continue
            WelshIndexMultipleDeprivation.objects.filter(lsoa=lsoa, year=2019).update(
                imd_score=record[3],
                income_score=record[4],
                employment_score=record[5],
                health_score=record[6],
                education_score=record[7],
                access_to_services_score=record[8],
                housing_score=record[9],
                community_safety_score=record[10],
                physical_environment_score=record[11],
                lsoa=lsoa,
                year=2019,
            )
            count += 1
    final = f" Added {count} Welsh IMD scores.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)  # should be 1909
    try:
        assert count == 1909
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 1909 records, but got {count}." + W + "\n"
        )
        pass


"""
Northern Ireland SOAs and deprivation data
"""


def add_northern_ireland_soas_and_deprivation_domains_with_ranks():
    path = f"{settings.IMD_DATA_FILES_FOLDER}/{NORTHERN_IRELAND_SOAS_AND_IMD_RANKS}"

    if (
        NorthernIrelandIndexMultipleDeprivation.objects.filter(year=2017).exists()
        and NorthernIrelandIndexMultipleDeprivation.objects.filter(year=2017).count()
        >= 890
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ Northern Ireland 2017 IMD already added. Skipping..."
            + W
            + "\n"
        )
        return
    else:
        imd_counter = 0

        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding Northern Ireland 2001 SOAs and 2017 deprivation domains and ranks..."
            + W
            + "\n"
        )
        with open(path, "r") as f:
            data = list(csv.reader(f, delimiter=","))
            for row in data[1:891]:  # skip the first row: run up to to 890
                soa, created = SOA.objects.update_or_create(
                    soa_code=row[2], soa_name=row[3], year=2001
                )

                NorthernIrelandIndexMultipleDeprivation.objects.update_or_create(
                    year=2017,
                    imd_rank=row[4],
                    income_rank=row[5],
                    employment_rank=row[6],
                    health_deprivation_and_disability_rank=row[7],
                    education_skills_and_training_rank=row[8],
                    access_to_services_rank=row[9],
                    living_environment_rank=row[10],
                    crime_and_disorder_rank=row[11],
                    soa=soa,
                )

                imd_counter += 1
    final = f" {imd_counter} Northern Ireland SOAs and IMD domains and ranks added.\n"
    sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final + W + "\n")
    try:
        assert imd_counter == 890
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 890 records, but got {imd_counter}." + W + "\n"
        )
        pass


"""
Green space and population density data
"""


def add_2015_population_denominators():
    # import domains of deprivation data
    # note this includes scotland so must load data zones first
    path = (
        f"{settings.IMD_DATA_FILES_FOLDER}/{IMD_2019_LSOA_2015_POPULATION_DENOMINATORS}"
    )
    with open(path, "r") as f:
        sys.stdout.write(
            G + "\n📎 - Adding 2015 population denominators to LSOAs" + W + "\n"
        )
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[1:]:  # skip the first row
            LSOA.objects.filter(lsoa_code=row[0], year=2011).update(
                total_population_mid_2015=int(float(row[4])),
                dependent_children_mid_2015=int(float(row[5])),
                population_16_59_mid_2015=int(float(row[6])),
                older_population_over_16_mid_2015=int(float(row[7])),
                working_age_population_over_18_mid_2015=int(float(row[8])),
            )

            count += 1
    final = f" Added {count} 2015 population denominators to LSOAs\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 32844
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
        )


def add_lad_access_to_outdoor_space():
    # import domains of deprivation data

    if (
        GreenSpace.objects.filter(year=2020).exists()
        and GreenSpace.objects.filter(year=2020).count() >= 371
    ):
        sys.stdout.write(
            "\n" + R + "⏭️ 2020 Green space data already added. Skipping..." + W + "\n"
        )
        return

    path = f"{settings.IMD_DATA_FILES_FOLDER}/{ACCESS_TO_GREEN_SPACE}"
    sys.stdout.write(
        "\n"
        + G
        + "📎 - Adding 2020 green space records to Local Authorities."
        + W
        + "\n"
    )
    with open(path, "r") as f:
        data = list(csv.reader(f, delimiter=","))
        count = 0

        for row in data[2:]:  # header is on row 3
            la_code = row[4]
            # Scottish LAs were created with year=2011, English & Welsh with year=2019
            la_year = 2011 if la_code.startswith("S") else 2019
            try:
                local_authority = LocalAuthority.objects.get(
                    local_authority_district_code=la_code,
                    year=la_year,
                )
            except LocalAuthority.DoesNotExist:
                sys.stderr.write(
                    "\n"
                    + R
                    + f"⏭️ Local Authority {row[4]} not found. Skipping..."
                    + W
                    + "\n"
                )
                continue
            if GreenSpace.objects.filter(
                local_authority=local_authority, year=2020
            ).exists():
                final = f"⏭️ Green space data already available for {local_authority.local_authority_district_name}.\n"
                sys.stdout.write(final)
                pass
            else:
                GreenSpace.objects.create(
                    local_authority=local_authority,
                    houses_address_count=int(float(row[6])),
                    houses_addresses_with_private_outdoor_space_count=int(
                        float(row[7])
                    ),
                    houses_outdoor_space_total_area=int(float(row[8])),
                    houses_percentage_of_addresses_with_private_outdoor_space=int(
                        float(row[9])
                    ),
                    houses_average_size_private_outdoor_space=int(float(row[10])),
                    houses_median_size_private_outdoor_space=int(float(row[11])),
                    flats_address_count=int(float(row[12])),
                    flats_addresses_with_private_outdoor_space_count=int(
                        float(row[13])
                    ),
                    flats_outdoor_space_total_area=int(float(row[14])),
                    flats_outdoor_space_count=int(float(row[15])),
                    flats_percentage_of_addresses_with_private_outdoor_space=int(
                        float(row[16])
                    ),
                    flats_average_size_private_outdoor_space=int(float(row[17])),
                    flats_average_number_of_flats_sharing_a_garden=int(float(row[18])),
                    total_addresses_count=int(float(row[19])),
                    total_addresses_with_private_outdoor_space_count=int(
                        float(row[20])
                    ),
                    total_percentage_addresses_with_private_outdoor_space=int(
                        float(row[21])
                    ),
                    total_average_size_private_outdoor_space=int(float(row[22])),
                    year=2020,
                )

                count += 1
    final = f" Added {count} Local Authority green space records.\n"
    sys.stdout.write(BOLD + "\n🔥 Complete." + END + final)
    try:
        assert count == 371
    except AssertionError:
        sys.stdout.write(
            "\n" + R + f"😬 Expected 371 records, but got {count}." + W + "\n"
        )
        pass


def update_population_densities():
    """
    Processes population density data from a list of dictionaries, creating PopulationDensity objects.

    Args:
        data: A list of dictionaries, where each dictionary represents a row of data.
                The first row is assumed to be a header and is skipped.  The order of
                data in subsequent rows is assumed to match the order of fields
                used to create the PopulationDensity object.

    Returns:
        None.  The function creates PopulationDensity objects in the database.

    Thanks to the remarkable alex.gilroy@theriverstrust for this resource
    """
    if (
        PopulationDensity.objects.exists()
        and PopulationDensity.objects.all().count() >= 32058
    ):
        sys.stdout.write(
            "\n"
            + R
            + "⏭️ Population density data already added. Skipping..."
            + W
            + "\n"
        )  # should be 32058
        return

    count = 0

    path = f"{settings.POPULATION_DENSITIES_FOLDER}/{POPULATION_DENSITIES}"
    with open(path, "r") as f:
        sys.stdout.write(
            "\n"
            + G
            + "📎 - Adding population densities for England by LSOA and ethnicities\n"
            + W
        )
        data = list(csv.reader(f, delimiter=","))

        for row in data[1:]:  # Iterate starting from the second row (index 1)
            lsoa11cd = row[1]  # Access the first element (index 1) which is 'lsoa11cd'
            lsoa = None
            if LSOA.objects.filter(lsoa_code=lsoa11cd, year=2011).exists():
                lsoa = LSOA.objects.filter(lsoa_code=lsoa11cd, year=2011).get()
            if lsoa is None:
                error = (
                    "\n"
                    + R
                    + f"⏭️ LSOA with code {lsoa11cd} not found. Skipping row...."
                    + W
                    + "\n"
                )
                sys.stderr.write(error)
                continue

            PopulationDensity.objects.update_or_create(
                lsoa=lsoa,
                year=2024,
                defaults={
                    "perc_buff200": row[8] if row[8] else None,
                    "perc_buff300": row[9] if row[9] else None,
                    "perc_buff1k": row[10] if row[10] else None,
                    "perc_buff2k": row[11] if row[11] else None,
                    "perc_buff5k": row[12] if row[12] else None,
                    "perc_buff10k": row[13] if row[13] else None,
                    "imd_decile": row[14] if row[14] else None,
                    "population_density_2011": row[15] if row[15] else None,
                    "population_2011": row[16] if row[16] else None,
                    "buff200_popdens_deficit": row[17] if row[17] else None,
                    "buff300_popdens_deficit": row[18] if row[18] else None,
                    "buff1k_popdens_deficit": row[19] if row[19] else None,
                    "buff2k_popdens_deficit": row[20] if row[20] else None,
                    "buff5k_popdens_deficit": row[21] if row[21] else None,
                    "buff10k_popdens_deficit": row[22] if row[22] else None,
                    "buff200_imd_deficit": row[23] if row[23] else None,
                    "buff300_imd_deficit": row[24] if row[24] else None,
                    "buff1k_imd_deficit": row[25] if row[25] else None,
                    "buff2k_imd_deficit": row[26] if row[26] else None,
                    "buff5k_imd_deficit": row[27] if row[27] else None,
                    "buff10k_imd_deficit": row[28] if row[28] else None,
                    "ag_area_ha": row[29] if row[29] else None,
                    "index_multiple_deprivation_2019": row[30] if row[30] else None,
                    "population_estimate2018": row[31] if row[31] else None,
                    "population_growth_2011_2018": row[32] if row[32] else None,
                    "ethnic_white_2011": row[33] if row[33] else None,
                    "ethnic_mixed_2011": row[34] if row[34] else None,
                    "ethnic_asian_2011": row[35] if row[35] else None,
                    "ethnic_black_african_caribbean": row[36] if row[36] else None,
                    "ethnic_other_2011": row[37] if row[37] else None,
                    "population_2011_1000s": row[38] if row[38] else None,
                    "nr_area_ha": row[39] if row[39] else None,
                    "nr_percentage": row[40] if row[40] else None,
                    "ruc_category": row[41] if row[41] else None,
                    "ruc11": row[42] if row[42] else None,
                    "lnr_area_ha": row[43] if row[43] else None,
                    "residentialaddress_count": row[44] if row[44] else None,
                    "pg_area": row[45] if row[45] else None,
                    "pg_area_per1kpeople": row[46] if row[46] else None,
                    "perc_osmmgs": row[47] if row[47] else None,
                    "pgarea_resaddress_ratio": row[48] if row[48] else None,
                    "accessiblewoodland_ha": row[49] if row[49] else None,
                    "mean_manmade_percentage": row[50] if row[50] else None,
                    "cohort_age_0_to_4": row[51] if row[51] else None,
                    "cohort_age_5_to_7": row[52] if row[52] else None,
                    "cohort_age_8_to_9": row[53] if row[53] else None,
                    "cohort_age_10_to_14": row[54] if row[54] else None,
                    "cohort_age_15": row[55] if row[55] else None,
                    "cohort_age_16_to_17": row[56] if row[56] else None,
                    "cohort_age_18_to_19": row[57] if row[57] else None,
                    "cohort_age_20_to_24": row[58] if row[58] else None,
                    "cohort_age_25_to_29": row[59] if row[59] else None,
                    "cohort_age_30_to_44": row[60] if row[60] else None,
                    "cohort_age_45_to_59": row[61] if row[61] else None,
                    "cohort_age_60_to_64": row[62] if row[62] else None,
                    "cohort_age_65_to_74": row[63] if row[63] else None,
                    "cohort_age_75_to_84": row[64] if row[64] else None,
                    "cohort_age_85_to_89": row[65] if row[65] else None,
                    "cohort_age_90_and_over": row[66] if row[66] else None,
                    "perc_close2home": row[67] if row[67] else None,
                    "popn_close2home": row[68] if row[68] else None,
                    "cohort_children": row[69] if row[69] else None,
                    "cohort_olderpeople": row[70] if row[70] else None,
                    "perc_pop_close2home": row[71] if row[71] else None,
                    "popn_children_close2home": row[72] if row[72] else None,
                    "popn_olderpeople_close2home": row[73] if row[73] else None,
                    "imd_reversed": row[74] if row[74] else None,
                    "ag_area_ha_per_person": row[75] if row[75] else None,
                },
            )

            count += 1

        final = f" {count} Population Density records by LSOA stored.\n"
        sys.stdout.write("\n" + BOLD + "🔥 Complete." + END + final)
        try:
            # Check if the count matches the expected number of records
            assert count == 32844
        except AssertionError:
            sys.stdout.write(
                "\n" + R + f"😬 Expected 32844 records, but got {count}." + W + "\n"
            )
            pass


"""
Quantile calculations
"""


def calculated_quantile_for_rank(rank, total_records, quantile_type):
    """
    Return a quantile against a rank and a total
    Params:
    rank: integer - represents rank in a list of records
    total_records: integer - represents the total number of records
    quantile_type: integer - the number of equally sized groups the records are divided into
    """
    _ = [
        "median",
        "tertile",
        "quartile",
        "quintile",
        "sextile",
        "septile",
        "octile",
        "decile",
        "duodecile",
        "hexadecile",
        "vigintile",
    ]

    tile_size = floor(total_records / quantile_type)
    if tile_size <= rank:
        return 1
    else:
        return floor(rank / tile_size)


def quantile_for_rank(rank: int, quantile: QuantileType) -> int:
    """
    returns a quantile for a rank in WIMD data

    WIMD 2019 Rank	Decile
            1-191	    1
            192-382	    2
            383-573	    3
            574-764	    4
            765-955	    5
            956-1146	6
            1147-1337	7
            1338-1528	8
            1529-1719	9
            1720-1909	10
    WIMD 2019 Rank	Quintile
            1-382	    1
            383-764	    2
            765-1146	3
            1147-1528	4
            1529-1909	5
    WIMD 2019 Rank	Quartile
            1-478	    1
            479-955	    2
            956-1432	3
            1433-1909	4
    """
    if (
        (quantile == QuantileType.QUARTILE and rank <= 478)
        or (rank <= 191 and quantile == QuantileType.DECILE)
        or (rank <= 382 and quantile == QuantileType.QUINTILE)
    ):
        return 1
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 955)
        or (rank <= 382 and quantile == QuantileType.DECILE)
        or (rank <= 764 and quantile == QuantileType.QUINTILE)
    ):
        return 2
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 1432)
        or (rank <= 573 and quantile == QuantileType.DECILE)
        or (rank <= 1146 and quantile == QuantileType.QUINTILE)
    ):
        return 3
    elif (
        (quantile == QuantileType.QUARTILE and rank <= 1909)
        or (rank <= 764 and quantile == QuantileType.DECILE)
        or (rank <= 1528 and quantile == QuantileType.QUINTILE)
    ):
        return 4
    elif (rank <= 955 and quantile == QuantileType.DECILE) or (
        rank <= 1909 and quantile == QuantileType.QUINTILE
    ):
        return 5
    elif rank <= 1146 and quantile == QuantileType.DECILE:
        return 6
    elif rank <= 1337 and quantile == QuantileType.DECILE:
        return 7
    elif rank <= 1528 and quantile == QuantileType.DECILE:
        return 8
    elif rank <= 1719 and quantile == QuantileType.DECILE:
        return 9
    elif rank <= 1909 and quantile == QuantileType.DECILE:
        return 10
    else:
        raise ValueError(f"Incorrect rank {rank} passed for {quantile.value}")


"""
Tests
"""


def test_table_totals():
    """
    Test the total number of records in each table
    """
    sys.stdout.write("\n" + G + "📎 - Testing table totals..." + W + "\n")
    # Check if the count matches the expected number of records
    normal_vals = [
        {
            "model": LSOA,
            "count": LSOA.objects.filter(year=2011).count(),
            "expected": 34753,
            "message": "2011 LSOA should have 34753 (32844 in England, 1909 in wales) rows.",
        },
        {
            "model": LSOA,
            "count": LSOA.objects.filter(year=2021).count(),
            "expected": 35672,
            "message": "2021 LSOA should have 35672 rows.",
        },
        {
            "model": DataZone,
            "count": DataZone.objects.count(),
            "expected": 6976,
            "message": "DataZone should have 6976 rows.",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(year=2011).count(),
            "expected": 32,
            "message": "2011 LocalAuthority for Scotland should have 32 .",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(year=2019).count(),
            "expected": 339,
            "message": "2019 LocalAuthority for England and Wales should have 339 (317 in England, 22 in Wales) rows (the 11 Northern Irish Local Authorities are not included here). ",
        },
        {
            "model": LocalAuthority,
            "count": LocalAuthority.objects.filter(
                year=2024, geom__isnull=False
            ).count(),
            "expected": 318,
            "message": "2024 LocalAuthority should have 318 rows with geometries.",
        },
        {
            "model": PopulationDensity,
            "count": PopulationDensity.objects.count(),
            "expected": 32844,
            "message": "PopulationDensity should have 32844 rows.",
        },
        {
            "model": GreenSpace,
            "count": GreenSpace.objects.count(),
            "expected": 371,
            "message": "GreenSpace should have 371 rows.",
        },
        {
            "model": SOA,
            "count": SOA.objects.count(),
            "expected": 890,
            "message": "SOA should have 890 rows.",
        },
        {
            "model": WelshIndexMultipleDeprivation,
            "count": WelshIndexMultipleDeprivation.objects.count(),
            "expected": 1909,
            "message": "WelshIndexMultipleDeprivation should have 1909 rows.",
        },
        {
            "model": NorthernIrelandIndexMultipleDeprivation,
            "count": NorthernIrelandIndexMultipleDeprivation.objects.count(),
            "expected": 890,
            "message": "NorthernIrelandIndexMultipleDeprivation should have 890 rows.",
        },
        {
            "model": ScottishIndexMultipleDeprivation,
            "count": ScottishIndexMultipleDeprivation.objects.count(),
            "expected": 6976,
            "message": "ScottishIndexMultipleDeprivation should have 6976 rows.",
        },
        {
            "label": "NHSEnglishRegion",
            "count": get_table_year_counts("deprivation_scores_nhsenglishregion", 2021)[
                "spatialized_rows"
            ],
            "expected": 7,
            "message": "NHSEnglishRegion should have 7 rows with geometries for year 2021.",
        },
        {
            "label": "IntegratedCareBoard",
            "count": get_table_year_counts(
                "deprivation_scores_integratedcareboard", 2023
            )["spatialized_rows"],
            "expected": 42,
            "message": "IntegratedCareBoard should have 42 rows with geometries for year 2023.",
        },
        {
            "label": "LocalHealthBoard",
            "count": get_table_year_counts("deprivation_scores_localhealthboard", 2022)[
                "spatialized_rows"
            ],
            "expected": 7,
            "message": "LocalHealthBoard should have 7 rows with geometries for year 2022.",
        },
        {
            "label": "ChannelIsland",
            "count": get_table_year_counts("deprivation_scores_channelisland", 2024)[
                "spatialized_rows"
            ],
            "expected": 3,
            "message": "ChannelIsland should have 3 rows with geometries for year 2024 (Guernsey, Isle of Man, Jersey).",
        },
    ]
    for val in normal_vals:
        label = val.get("label") or val["model"].__name__
        try:
            assert val["count"] == val["expected"]
        except AssertionError:
            sys.stdout.write(
                "\n" + R + f"😬 {val['message']} But got {val['count']}." + W + "\n"
            )
            continue
        sys.stdout.write(W + f"✅ {label} has {val['count']} records." + W + "\n")


def image():
    return """

                                .^~^      ^777777!~:       ^!???7~:
                                ^JJJ:.:!^ 7#BGPPPGBGY:   !5BBGPPGBBY.
                                 :~!!?J~. !BBJ    YBB?  ?BB5~.  .~J^
                              .:~7?JJ?:   !BBY^~~!PBB~ .GBG:
                              .~!?JJJJ^   !BBGGGBBBY^  .PBG^
                                 ?J~~7?:  !BBJ.:?BB5^   ~GBG?^:^~JP7
                                :?:   .   !BBJ   ~PBG?.  :?PBBBBBG5!
                                ..::...     .::. ...:^::. .. .:^~~^:.
                                !GPGGGGPY7.   :!?JJJJ?7~..PGP:    !GGJ
                                7BBY~~!YBBY  !JJ?!^^^!??::GBG:    7BBJ
                                7BB?   .GBG.^JJ7.     .. .GBG!^^^^JBBJ
                                7BB577?5BBJ ~JJ!         .GBBGGGGGGBBJ
                                7BBGPPP5J~  :JJJ^.   .^^ .GBG^.::.?BBJ
                                7#B?         :7JJ?77?JJ?^:GBB:    7##Y
                                ~YY!           :~!77!!^. .JYJ.    ~YY7


                                       RCPCH Census Platform 2022

                """
