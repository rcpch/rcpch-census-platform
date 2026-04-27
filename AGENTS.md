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
- `process_geometries` runs post-processing only (no boundary re-download), useful for SQL/view/table-shape changes. Accepts an optional `--layers` flag to process only specific overlay groups (see below).

## Tile-serving model

Tiles are served directly from PostGIS by pg_tileserv. There is no Django serialization path for map tiles.

Materialized table families:

- UK mixed-nation tables:
  - `public.uk_master_2011_z0_4`
  - `public.uk_master_2011_z5_7`
  - `public.uk_master_2011_z8_10`
  - `public.uk_master_2011_z11_14`
  - `public.uk_master_2021_z0_4`
  - `public.uk_master_2021_z5_7`
  - `public.uk_master_2021_z8_10`
  - `public.uk_master_2021_z11_14`
- LSOA-focused tables:
  - `public.lsoa_tiles_2011_z0_4`
  - `public.lsoa_tiles_2011_z5_7`
  - `public.lsoa_tiles_2011_z8_10`
  - `public.lsoa_tiles_2011_z11_14`
  - `public.lsoa_tiles_2021_z0_4`
  - `public.lsoa_tiles_2021_z5_7`
  - `public.lsoa_tiles_2021_z8_10`
  - `public.lsoa_tiles_2021_z11_14`

## Dataset/Boundary Source Of Truth

To avoid doc drift, treat `site/docs/boundaries.md` as the canonical source for:

- Boundary dataset endpoints and code mappings
- Boundary year vs IMD year behaviour
- Tile property contracts exposed by pg_tileserv

Current map behaviour summary (quick reference only):

| View / Era | England | Wales | Scotland | N. Ireland |
| --- | --- | --- | --- | --- |
| All UK (era = 2021) | 2021 LSOA + 2025 IMD | 2011 LSOA + 2019 WIMD | 2011 DataZone + 2020 SIMD | 2001 SOA + 2017 NIMDM |
| All UK (era = 2011) | 2011 LSOA + 2019 IMD | 2011 LSOA + 2019 WIMD | 2011 DataZone + 2020 SIMD | 2001 SOA + 2017 NIMDM |
| England-only (era = 2021) | 2021 LSOA + 2025 IMD | n/a | n/a | n/a |
| England-only (era = 2011) | 2011 LSOA + 2019 IMD | n/a | n/a | n/a |

Key point: the `uk_master_2021_*` tables are **mixed vintage** — England uses 2021 LSOAs and 2025 IMD, while Wales, Scotland and N. Ireland remain on their respective 2011-era boundaries and latest available IMD data. Wales has not adopted 2021 LSOA boundaries and has not published an IMD since WIMD 2019; Scotland and N. Ireland are similarly frozen on older vintages. There is no purely "all-2021" UK-wide dataset.

This means the era toggle has a meaningful effect on the All UK view (switching between 2019 and 2025 IMD data for England), not just on England-only views. Consuming applications (e.g. NPDA) can use `era=2021` for current-cohort maps and `era=2011` for historical-cohort maps, with Wales and other nations appearing identically in both because no newer data exists for them.

Local authority boundary import summary:

- England/Wales LA geometry is imported from the 2019 and 2024 ONS LAD BFC services.
- Scotland LA geometry is imported from the 2011 GB LAD BFC service because the pre-seeded Scottish LocalAuthority rows are year `2011`.
- The `public.la_tiles` overlay therefore uses year `2011` for Scotland and years `2019`/`2024` for England/Wales.

If this summary conflicts with `site/docs/boundaries.md`, update this section to match `site/docs/boundaries.md`.

## Exposed tile properties

As of current implementation:

- `public.uk_master_*` properties include:
  - `code`
  - `area_name`
  - `la_code` (England/Wales/Scotland; `NULL` for N. Ireland)
  - `la_name` (England/Wales/Scotland; `NULL` for N. Ireland)
  - `la_year` (England/Wales/Scotland; `NULL` for N. Ireland)
  - `nhser_code` (England only; `NULL` elsewhere)
  - `nhser_name` (England only; `NULL` elsewhere)
  - `icb_code` (England only; `NULL` elsewhere)
  - `icb_name` (England only; `NULL` elsewhere)
  - `lhb_code` (Wales only; `NULL` elsewhere)
  - `lhb_name` (Wales only; `NULL` elsewhere)
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

  To rebuild only specific overlay tables (much faster — minutes not hours):

  ```bash
  # Local authority tiles only
  python manage.py seed --mode process_geometries --layers local-authorities

  # All health boundaries (NHSER + ICB + LHB)
  python manage.py seed --mode process_geometries --layers health-geographies

  # Individual health boundary types
  python manage.py seed --mode process_geometries --layers nhs-regions
  python manage.py seed --mode process_geometries --layers integrated-care-boards
  python manage.py seed --mode process_geometries --layers local-health-boards

  # LSOAs + UK master tiles only
  python manage.py seed --mode process_geometries --layers lsoas

  # Multiple groups at once
  python manage.py seed --mode process_geometries --layers local-authorities nhs-regions
  ```

  **Note**: Section 1 (schema `ADD COLUMN IF NOT EXISTS`) always runs regardless of `--layers` since it is idempotent and fast. `--layers` only gates the expensive UPDATE/CREATE operations.

  Validation behavior after geometry processing:

  - Full geometry rebuilds (`import_bfc_boundaries`, or `process_geometries` with no `--layers` / `--layers all`) run `test_geometries` in strict mode and fail on missing/empty required boundary tier tables.
  - Scoped rebuilds (`process_geometries --layers <subset>`) run `test_geometries` in report-only mode for boundary-tier completeness, so operators can process a subset without failing due to unrelated layers not being rebuilt yet.

Full/base reseed likely required:

- New source CSV content for core IMD/reference tables
- New boundary source ingestion requirements that rely on raw geometry re-import
- Fresh environment bootstrap from empty database

Use:

- `python manage.py seed --mode __all__`
- then `python manage.py seed --mode import_bfc_boundaries`

## Health Boundaries Import (NHS Regions, ICBs, Local Health Boards)

Added April 2026. Three new health administrative boundaries imported via BFC (Boundaries Full Clipped) from ONS:

| Boundary Type | Year | Nation | Endpoint Code | Django Column | Record Count |
| --- | --- | --- | --- | --- | --- |
| NHS England Regions | 2021 | England | NHSER21CD | `nhser_code` | 7 |
| Integrated Care Boards | 2023 | England | ICB23CD | `icb_code` | ~42 |
| Local Health Boards | 2022 | Wales | LHB22CD | `lhb_code` | 7 |

All map to 2021 LSOA boundaries. Imported as part of `import_bfc_boundaries` mode. Models include:
- `NHSEnglishRegion`, `IntegratedCareBoard`, `LocalHealthBoard` in `deprivation_scores/models.py`
- Unique constraint on `(code, year)` to support multi-year versioning
- Full geometry processing (3857 transform, simplification, spatial indexes)

## Local Authority Boundary Imports

Current Local Authority boundary sources are split by nation/year:

| Boundary Type | Year | Nation Coverage | Endpoint Code | Django Column | Notes |
| --- | --- | --- | --- | --- | --- |
| Local Authority Districts | 2011 | Great Britain | `lad11cd` | `local_authority_district_code` | Used to spatialize the pre-seeded Scottish LA rows (`year = 2011`) |
| Local Authority Districts | 2019 | England and Wales in current import flow | `lad19cd` | `local_authority_district_code` | Used for 2011-era England/Wales LA references |
| Local Authority Districts | 2024 | England and Wales | `LAD24CD` | `local_authority_district_code` | Used for 2021-era England LA references |

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
  - For release-grade dumps, prefer `./s/build-dump --fresh --yes` to force a clean rebuild from scratch.
  - `./s/build-dump --existing --yes` reuses the current build container and skips reseeding.
- `s/release-dump`
  - Publishes dump artifacts to GitHub Releases; auto-splits large dumps.
- `s/restore-db`
  - Restores release dump into managed PostgreSQL (with safety guard and extension handling).
- `s/deploy-db`
  - Operator notes/steps for running restore in Azure Container Apps context.

Misc:

- `s/get-build-info`
  - Outputs current git hash and branch JSON.

### Frontend Cache-Busting (Automated on Deploy)

- `site/index.html` includes deploy-time placeholders in map script tags:
  - `config.js?v=__ASSET_VERSION__`
  - `map-logic.js?v=__ASSET_VERSION__`
- The deploy workflow (`.github/workflows/deploy_containerapps.yml`) replaces `__ASSET_VERSION__` with the first 12 chars of `latest_git_commit` from `build_info.json`.
- This ensures each deployed revision serves a unique JS URL and avoids stale browser/CDN asset caches after map/frontend updates.
- In local development (without deploy replacement), the placeholder string remains literal and is still a valid query string.

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
