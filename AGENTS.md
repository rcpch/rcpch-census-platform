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

## Dataset/Boundary Source Of Truth

To avoid doc drift, treat `site/docs/boundaries.md` as the canonical source for:

- Boundary dataset endpoints and code mappings
- Boundary year vs IMD year behaviour
- Tile property contracts exposed by pg_tileserv

Current map behaviour summary (quick reference only):

| View | England | Wales | Scotland | N. Ireland |
| --- | --- | --- | --- | --- |
| All UK | 2011 LSOA + 2019 IMD | 2011 LSOA + 2019 WIMD | 2011 DataZone + 2020 SIMD | 2001 SOA + 2017 NIMDM |
| England-only (era toggle = 2021) | 2021 LSOA + 2025 IMD | n/a | n/a | n/a |
| England-only (era toggle = 2011) | 2011 LSOA + 2019 IMD | n/a | n/a | n/a |

If this summary conflicts with `site/docs/boundaries.md`, update this section to match `site/docs/boundaries.md`.

## Exposed tile properties

As of current implementation:

- `public.uk_master_*` properties include:
  - `code`
  - `area_name`
  - `la_code` (England/Wales/Scotland; `NULL` for N. Ireland)
  - `la_name` (England/Wales/Scotland; `NULL` for N. Ireland)
  - `la_year` (England/Wales/Scotland; `NULL` for N. Ireland)
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
- `s/test`
  - Runs pytest with pass-through flags; uses running web container when available, otherwise starts a one-off test container.
- `s/wait-for-db.sh`
  - Waits for DB readiness; optionally waits for seeded/populated tables when `WAIT_FOR_POPULATION=true`.

## Git hooks (one-time setup)

A pre-push hook lives in `.githooks/pre-push`. Activate it once per clone:

```bash
git config core.hooksPath .githooks
```

What it does on every `git push`:

- If `uk_master_*` tile tables exist locally → runs `tests/test_uk_master_local_authority_fields.py` and **blocks the push on failure**.
- If tables are absent (i.e. `process_geometries` has not been run) → prints a reminder and **allows the push**, matching CI behaviour (tests are skipped there too).

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

## Publishing and deployment docs

For full operator guidance, use these docs in `site/docs/`:

- `site/docs/database-dump-and-publish.md`
  - Local dump build/test and GitHub Release publication (including chunk splitting for large dumps).
- `site/docs/managed-database-seeding.md`
  - Restoring a release dump into Azure Database for PostgreSQL (typically from Azure Container Apps via `s/restore-db`).
- `site/docs/deploy.md`
  - End-to-end deployment architecture and sequence (dump publication, DB seed/restore, app deploy, verification).

If these docs and this file disagree, treat `site/docs/*.md` as the source of truth and update this summary.

## Recommended release/deploy workflow (high-level)

For this project's large database footprint, the intended workflow is:

1. Build and test the seeded database dump locally (`s/build-dump`).
2. Publish the dump to GitHub Releases (`s/release-dump`), with automatic split parts for large artifacts.
3. In Azure, restore that released dump into the managed PostgreSQL instance (`s/restore-db`, usually executed from the web container).
4. Deploy/update application containers (Django/nginx/pg_tileserv) separately.

Why this is preferred:

- Keeps heavy seed/build work local and reproducible.
- Uses versioned release artifacts for rollback and auditability.
- Decouples data lifecycle from app container rollout.

Practical note:

- App deployment does not seed the managed database automatically; restore/seed is a separate operator step.

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
