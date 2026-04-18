# AGENTS.md

This file is a quick operational guide for coding agents and LLM tools working in this repository. It complements, not replaces, the full project docs under site/docs/.

## Project at a glance

- Stack: Django + PostGIS + pg_tileserv + optional nginx in deployment.
- Core purpose: seed UK deprivation and boundary datasets, then serve fast vector tiles for map rendering.
- Key seeding command: `python manage.py seed --mode <mode>`.

## Data pipeline summary

The platform has two distinct data phases:

1. Base data seeding (tabular and relational data)

- Populates:
  - Organisational geography references (LSOA/DataZone/SOA/LocalAuthority)
  - IMD datasets by nation and year
  - Supplementary scores/ranks and population density data

- Typical modes include:
  - `__all__`
  - `add_organisational_areas`
  - `add_english_imds`
  - `add_welsh_imds`
  - `add_scottish_imds`
  - `add_northern_ireland_imds`
  - `add_population_densities`
  - `ci_test`

1. Boundary enrichment + spatial post-processing

- `import_bfc_boundaries` downloads/streams external geometry datasets and merges geometries into base tables.
- `_run_post_processing_sql()` then:
  - Creates 3857 geometry columns
  - Generates simplified geometries for low/medium zoom
  - Builds spatial indexes and clusters
  - Materializes tile-serving tables for all zoom tiers
- `process_geometries` runs post-processing only (no boundary re-download), useful for SQL/view/table-shape changes.

## Tile-serving model

Tiles are served directly from PostGIS by pg_tileserv. There is no Django serialization path for map tiles.

Materialized table families:

- UK mixed-nation tables:
  - `public.uk_master_2011_z0_4`
  - `public.uk_master_2011_z5_7`
  - `public.uk_master_2011_z8_10`
  - `public.uk_master_2021_z0_4`
  - `public.uk_master_2021_z5_7`
  - `public.uk_master_2021_z8_10`
- LSOA-focused tables:
  - `public.lsoa_tiles_2011_z0_4`
  - `public.lsoa_tiles_2011_z5_7`
  - `public.lsoa_tiles_2011_z8_10`
  - `public.lsoa_tiles_2021_z0_4`
  - `public.lsoa_tiles_2021_z5_7`
  - `public.lsoa_tiles_2021_z8_10`

## Exposed tile properties

As of current implementation:

- `public.uk_master_*` properties include:
  - `code`
  - `area_name`
  - `imd_decile`
  - `imd_year`
  - `nation`
  - `year`
- `public.lsoa_tiles_*` properties include:
  - `lsoa_code`
  - `area_name`
  - `imd_decile`
  - `imd_rank`
  - `year`

If you need to expose additional tile attributes, update SQL in `deprivation_scores/management/commands/seed.py` helper methods and rerun `--mode process_geometries`.

## When reseeding is required vs not required

No full reseed required:

- Adding/removing columns in tile materialization SQL
- Adjusting simplification thresholds/indexing in post-processing SQL
- Refreshing tile output shape from existing seeded data

Use:

- `python manage.py seed --mode process_geometries`

Full/base reseed likely required:

- New source CSV content for core IMD/reference tables
- New boundary source ingestion requirements that rely on raw geometry re-import
- Fresh environment bootstrap from empty database

Use:

- `python manage.py seed --mode __all__`
- then `python manage.py seed --mode import_bfc_boundaries`

## Convenience scripts in s/

Primary helper scripts:

- `s/dev`
  - Starts the PostGIS development compose stack.
- `s/runserver`
  - Runs Django dev server.
- `s/migrate`
  - Runs `makemigrations` then `migrate`.
- `s/pg-tiles`
  - Starts pg_tileserv service via compose.
- `s/wait-for-db.sh`
  - Waits for DB readiness; optionally waits for seeded/populated tables when `WAIT_FOR_POPULATION=true`.

Database dump/release workflow helpers:

- `s/build-dump`
  - Creates a local PostGIS container, runs migrations and seed modes, builds a compressed pg_dump, and performs a restore test.
- `s/release-dump`
  - Publishes dump artifacts to GitHub Releases; auto-splits large dumps.
- `s/restore-db`
  - Restores release dump into managed PostgreSQL (with safety guard and extension handling).
- `s/deploy-db`
  - Operator notes/steps for running restore in Azure Container Apps context.

Misc:

- `s/get-build-info`
  - Outputs current git hash and branch JSON.

## Agent implementation notes

- For map property changes, prioritize `seed.py` post-processing SQL over frontend workarounds.
- Keep output column aliases stable (`code`, `nation`, `imd_decile`, etc.) to avoid breaking map clients.
- For nation-agnostic labels in UI, use `area_name` rather than assuming LSOA naming across all nations.
- After SQL changes, validate with pg_tileserv metadata endpoint:
  - `/tiles/public.uk_master_2021_z8_10.json`
  - `/tiles/public.lsoa_tiles_2021_z8_10.json`

## Debugging tile property issues

If a new property appears correctly in the pg_tileserv metadata JSON but the frontend shows a fallback value (e.g. "Unknown area"), follow this checklist:

1. **Confirm DB data is populated** — run SQL against the source tables to check for nulls:

   ```sql
   SELECT COUNT(*) FILTER (WHERE area_name IS NULL) FROM public.uk_master_2021_z8_10;
   SELECT COUNT(*) FILTER (WHERE trim(area_name) = '') FROM public.uk_master_2021_z8_10;
   ```

2. **Confirm tile tables have been rebuilt** — run `process_geometries` after any SQL change:

   ```bash
   python manage.py seed --mode process_geometries
   ```

3. **Confirm pg_tileserv reports the property** — the metadata endpoint is authoritative:

   ```bash
   curl http://localhost:7800/public.uk_master_2021_z8_10.json | jq '.properties[] | .name'
   ```

4. **Inspect actual runtime keys** — `map-logic.js` logs the exact property keys and a sample object to the browser console on first hover. Open DevTools and hover an area to confirm what MapLibre is receiving.

5. **Check the JS lookup order** — `getPropCaseInsensitive()` in `site/map-logic.js` tries keys in order. Ensure the canonical alias (e.g. `area_name`) is the first candidate.

In a confirmed case: tile schema, DB data, and pg_tileserv metadata were all correct. The root cause was that `feature.properties` lookup was strict and brittle. Adding `getPropCaseInsensitive()` with an ordered candidate list resolved the issue.
