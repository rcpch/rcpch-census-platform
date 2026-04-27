# Boundary Dataset & Spatial Optimization Pipeline

This document describes the automated pipeline for fetching, merging, and optimizing UK boundary geometries (LSOA, DataZone, SOA, and Local Authority) for the project.

## Overview

Unlike standard data seeding, geometries are handled via a post-processing enrichment phase. This ensures that the base statistical data (IMD scores) is established first, with spatial data added and optimized afterwards to support high-performance map rendering.

### The Pipeline Workflow

1. **Base Seeding**: The project first seeds the base tables (`LSOA`, `DataZone`, `SOA`, `LocalAuthority`) and their associated IMD tables using the standard CSV import modes.
2. **Enrichment (`import_bfc_boundaries`)**:
    * The management command streams GeoJSON data directly from ArcGIS REST APIs in chunks.
    * Data is loaded into a **temporary table** (`temp_shapes_{year}`).
    * A SQL **Merge** is performed: Geometries are joined to the base tables using the specific code mappings and the `year`.
3. **Spatial Optimization**:
    * **Transformation**: Geometries are transformed to **EPSG:3857** (Web Mercator).
    * **Simplification**: Multiple resolutions are created (`ST_SimplifyPreserveTopology`) to ensure the map remains performant at national scales.
    * **Indexing**: GIST spatial indexes are applied to all geometry columns.

## Dataset Mapping & Endpoints

We use **BFC (Boundaries Full Clipped)** datasets to ensure high-fidelity boundaries before simplification.

| Nation / Type | Year | ArcGIS Endpoint (Layer 0 Query) | ArcGIS ID Field | Django Model Column |
| :--- | :--- | :--- | :--- | :--- |
| **England/Wales LSOA** | 2011 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Lower_layer_Super_Output_Areas_Dec_2011_Boundaries_Full_Clipped_BFC_EW_V3_2022/FeatureServer/0/query) | `LSOA11CD` | `lsoa_code` |
| **England/Wales LSOA** | 2021 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LSOA_2021_EW_BFE_V10_RUC/FeatureServer/3/query) | `LSOA21CD` | `lsoa_code` |
| **Scotland DataZone** | 2011 | [ScotGov MapServer](https://maps.gov.scot/server/rest/services/ScotGov/StatisticalUnits/MapServer/2/query) | `DataZone` | `data_zone_code` |
| **N. Ireland SOA** | 2011 | [NISRA FeatureServer](https://services3.arcgis.com/APHjSHuFMGWVZFgQ/arcgis/rest/services/SOA2011/FeatureServer/0/query) | `SOA_CODE` | `soa_code` |
| **Great Britain Local Authority** | 2011 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2011_GB_BFC_2022/FeatureServer/0/query) | `lad11cd` | `local_authority_district_code` |
| **England/Wales Local Authority** | 2019 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/LAD_Dec_2019_Boundaries_UK_BFC_2022/FeatureServer/0/query) | `lad19cd` | `local_authority_district_code` |
| **England/Wales Local Authority** | 2024 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_May_2024_Boundaries_UK_BFC/FeatureServer/0/query) | `LAD24CD` | `local_authority_district_code` |
| **NHS England Regions** | 2021 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/NHS_England_Regions_April_2021_EN_BFC_2022/FeatureServer/0/query) | `NHSER21CD` | `nhser_code` |
| **Integrated Care Boards** | 2023 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Integrated_Care_Boards_April_2023_EN_BFC/FeatureServer/0/query) | `ICB23CD` | `icb_code` |
| **Local Health Boards** | 2022 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Health_Boards_April_2022_WA_BFC_2022/FeatureServer/0/query) | `LHB22CD` | `lhb_code` |

### Local Authority import note

Local authority geometries are intentionally split across three datasets in the current pipeline:

* The 2011 GB LAD dataset supplies geometry for the pre-seeded Scottish `LocalAuthority` rows, which exist as `year = 2011`.
* The 2019 LAD dataset supplies geometry for England and Wales local authorities used by the 2011-era map and `uk_master_2011_*` tables.
* The 2024 LAD dataset supplies geometry for England local authorities used by the 2021-era England map.

Although the 2019 endpoint is branded as UK in ONS, the current import flow relies on the 2011 GB dataset to spatialize Scottish local authorities.

### Scottish LAD code remapping (2011 geometry -> current DB codes)

Four Scottish councils were renumbered in 2019. The 2011 GB BFC geometry service still uses the older 2011 LAD codes, while the seeded `LocalAuthority` rows in this project use the newer codes from a 2019-era lookup source.

To avoid re-seeding Scotland with legacy codes, `import_bfc_boundaries` applies a targeted code remap for these rows when importing the 2011 GB LAD dataset:

* `S12000015` -> `S12000047` (Fife)
* `S12000024` -> `S12000048` (Perth and Kinross)
* `S12000044` -> `S12000050` (North Lanarkshire)
* `S12000046` -> `S12000049` (Glasgow City)

Practical effect:

* The geometry source remains authoritative for 2011 boundaries.
* Tile properties and tooltip LA codes stay aligned with currently used Scottish LA codes.
* A preflight status such as `28/32` for `LAD 2011 GB BFC` indicates this remap path has not yet been applied in that environment.

## Conditional Import Behaviour

`import_bfc_boundaries` runs a preflight completeness check for each configured dataset using table + year:

* `total_rows`: rows present for that `year`
* `spatialized_rows`: rows with non-null `geom`
* `is_complete`: `total_rows > 0` and `total_rows == spatialized_rows`

Default behaviour (without `--force`):

* Complete datasets are skipped.
* Incomplete datasets are imported.
* A summary line is printed with run/skip counts.

Force behaviour (with `--force`):

* All configured datasets are reprocessed.
* Existing geometry can be overwritten.

## Technical Note: Why we use Streaming over ogr2ogr

While `ogr2ogr` is a standard tool for spatial data migration, this project utilizes a custom Python streaming implementation via `requests` and `GeoPandas`. This approach was chosen to handle the **ArcGIS resultRecordCount** limits more gracefully and to avoid external binary dependencies in the web container.

The **2024 Local Authority** endpoint, in particular, is sensitive to large requests; therefore, we implement a strict `chunk_size` (e.g., 100 records) to prevent timeout errors and 500-responses from the ArcGIS server. This streaming method ensures that we only move the necessary identifier and geometry fields into the database, keeping memory usage predictable during the enrichment process.

## Architecture: pg_tileserv & CDN

To achieve fast rendering on the frontend:

1. **pg_tileserv**: A dedicated Go-based container connects to the database and serves the SQL views as **MVT (Mapbox Vector Tiles)**.
2. **Resolution Switching**: The frontend automatically requests different views based on zoom level:
    * `z0-z4`: Uses `public.uk_master_<era>_z0_4` (high simplification).
    * `z5-z7`: Uses `public.uk_master_<era>_z5_7` (medium simplification).
    * `z8+`: Uses `public.uk_master_<era>_z8_10` (full detail BFC).
    * `<era>` is either `2011` or `2021`. Both eras are valid for All UK and England-only views. The `uk_master_2021_*` tables are mixed vintage: England uses 2021 LSOAs + 2025 IMD while Wales, Scotland and N. Ireland remain on their 2011-era boundaries and latest available IMD (see table below).
3. **CDN**: Tiles are cached at the edge via a CDN to ensure sub-second map interactivity.

### Frontend script cache-busting

To reduce stale frontend behavior after map-layer changes, `site/index.html` uses versioned local script URLs:

* `config.js?v=__ASSET_VERSION__`
* `map-logic.js?v=__ASSET_VERSION__`

During deployment, `.github/workflows/deploy_containerapps.yml` injects `__ASSET_VERSION__` from the current git commit hash (first 12 chars via `build_info.json`). This gives each release unique JS asset URLs, so browser/CDN caches naturally refresh on deploy.

## Current Dataset Mapping (Map Behaviour)

This section summarizes what the map currently renders by view. Use this as the quick reference for boundary year, IMD year, and local authority metadata in tile properties.

| View | Nation | Boundary Type/Year (`year`) | IMD Dataset/Year (`imd_year`) | LA/LAD metadata year (`la_year`) | Match note |
| :--- | :--- | :--- | :--- | :--- | :--- |
| All UK (`uk_master_2021_*`) | England | LSOA 2021 | IMD 2025 | 2024 | Lookup-linked (2021 LSOAs reference 2024 LADs in source lookup file) |
| All UK (`uk_master_2021_*`) | Wales | LSOA 2011 | WIMD 2019 | 2019 | No 2021 LSOA boundaries or post-2019 WIMD published for Wales |
| All UK (`uk_master_2021_*`) | Scotland | DataZone 2011 | SIMD 2020 | 2011 | No post-2011 DataZone boundaries or post-2020 SIMD published for Scotland |
| All UK (`uk_master_2021_*`) | Northern Ireland | SOA 2001 | NIMDM 2017 | `NULL` | Not applicable in current layer (`la_*` fields are `NULL`) |
| All UK (`uk_master_2011_*`) | England | LSOA 2011 | IMD 2019 | 2019 | Lookup-linked (2011 LSOAs reference 2019 LADs in source lookup file) |
| All UK (`uk_master_2011_*`) | Wales | LSOA 2011 | WIMD 2019 | 2019 | Lookup-linked (2011 LSOAs reference 2019 LADs in source lookup file) |
| All UK (`uk_master_2011_*`) | Scotland | DataZone 2011 | SIMD 2020 | 2011 | Lookup-linked (2011 DataZones reference 2011 LAs) |
| All UK (`uk_master_2011_*`) | Northern Ireland | SOA 2001 | NIMDM 2017 | `NULL` | Not applicable in current layer (`la_*` fields are `NULL`) |
| England-only (era = 2021) | England | LSOA 2021 | IMD 2025 | 2024 | Lookup-linked (2021 LSOAs reference 2024 LADs in source lookup file) |
| England-only (era = 2011) | England | LSOA 2011 | IMD 2019 | 2019 | Lookup-linked (2011 LSOAs reference 2019 LADs in source lookup file) |

For the standalone `public.la_tiles` overlay source, the year mapping is currently:

* England/Wales: `2019` and `2024`
* Scotland: `2011`

### Mixed-vintage note for `uk_master_2021_*`

The `uk_master_2021_*` tables contain data from different boundary vintages depending on nation. England uses 2021 LSOAs and 2025 IMD data; Wales, Scotland and N. Ireland remain on their 2011-era boundaries and their most recent available IMD datasets. This reflects the actual availability of published data — Wales has not adopted 2021 LSOA boundaries and has not published a WIMD since 2019; Scotland and N. Ireland are similarly frozen on older vintages. There is no purely "all-2021" UK-wide dataset.

Consuming applications can therefore:

- Pass `era=2021` to show the latest available data for each nation (England on 2021 LSOAs + 2025 IMD; Wales on 2011 LSOAs + 2019 WIMD).
- Pass `era=2011` to show a consistent historical-cohort view where England also uses 2011 LSOAs + 2019 IMD, matching Wales and other nations.

The era toggle is meaningful for All UK views, not only England-only views.

### Important alignment caveat

`la_*` fields are currently joined by the pre-seeded lookup relationships (LSOA/DataZone -> LocalAuthority), not by spatial overlay/intersection at runtime. This means they represent the mapped administrative relationship in the source datasets, not a geometric "best fit" recomputation inside tile SQL.

### Northern Ireland note

Northern Ireland does not use the same Local Authority District model as England/Wales/Scotland in this dataset. Tooltips should treat `la_*` fields as not applicable for NI and can show a message such as: "Northern Ireland uses Local Government Districts, not LAD fields in this layer."

## Tile Properties Exposed

The post-processing SQL materializes tile-serving tables and explicitly controls the attributes exposed by pg_tileserv.

### UK Master Tables (`public.uk_master_*`)

The following properties are exposed at all zoom levels:

* `code`: Area code (`lsoa_code`, `data_zone_code`, or `soa_code`)
* `area_name`: Human-readable name (`lsoa_name`, `data_zone_name`, or `soa_name`)
* `la_code`: Local authority code for England/Wales/Scotland (`NULL` for Northern Ireland)
* `la_name`: Local authority name for England/Wales/Scotland (`NULL` for Northern Ireland)
* `la_year`: Local authority reference year for England/Wales/Scotland (`NULL` for Northern Ireland)
* `nhser_code`: NHS England Region code (`NULL` outside England)
* `nhser_name`: NHS England Region name (`NULL` outside England)
* `icb_code`: Integrated Care Board code (`NULL` outside England)
* `icb_name`: Integrated Care Board name (`NULL` outside England)
* `lhb_code`: Local Health Board code (`NULL` outside Wales)
* `lhb_name`: Local Health Board name (`NULL` outside Wales)
* `imd_decile`: Decile used for choropleth colouring
* `imd_year`: IMD publication year for that nation in the selected era
* `nation`: `england`, `wales`, `scotland`, or `northern_ireland`
* `year`: Boundary year

### LSOA-only Tables (`public.lsoa_tiles_*`)

The following properties are exposed at all zoom levels:

* `lsoa_code`
* `area_name` (from `lsoa_name`)
* `imd_decile`
* `imd_rank`
* `year`

### Health Boundary Tables

Health boundaries are exposed through dedicated views with consistent key names:

* `public.nhser_tiles_2021`
* `public.icb_tiles_2023`
* `public.lhb_tiles_2022`

Each exposes:

* `code` (boundary code)
* `area_name` (human-readable name)
* `nation` (`england` or `wales`)
* `year`
* `geom`

### Why this matters

Because pg_tileserv serves directly from these materialized tables, adding a column in the post-processing SQL makes it available immediately in tile properties after rebuilding the tables.

### Verifying exposed properties

Confirm what is actually served by querying the pg_tileserv metadata endpoints directly:

```bash
curl http://localhost:7800/public.uk_master_2021_z8_10.json | jq '.properties[] | .name'
curl http://localhost:7800/public.lsoa_tiles_2021_z8_10.json | jq '.properties[] | .name'
curl http://localhost:7800/public.nhser_tiles_2021.json | jq '.properties[] | .name'
curl http://localhost:7800/public.icb_tiles_2023.json | jq '.properties[] | .name'
curl http://localhost:7800/public.lhb_tiles_2022.json | jq '.properties[] | .name'
```

This is the authoritative source of truth for what the frontend receives. If a property appears in the SQL `SELECT` but not in these metadata responses, the tile tables have not been rebuilt yet.

### Frontend property lookup robustness

MapLibre GL JS decodes MVT properties and surfaces them as a plain JavaScript object on `feature.properties`. Property key casing is preserved from the PostGIS column name, so consistent snake_case aliases in the SQL (e.g. `area_name`, `imd_decile`) are important.

`map-logic.js` uses a `getPropCaseInsensitive()` helper that tries an ordered list of candidate keys and falls back to a case-insensitive scan of the property object. This guards against silent lookup failures if aliases change. When adding new tile properties, add the canonical key as the first candidate in the relevant `getPropCaseInsensitive()` call in `site/map-logic.js`.

On first hover the map logs the following to the browser console to assist debugging:

* Tile base URL
* Exact property keys received from the tile
* A sample properties object

## How to Run

After the base IMD data has been seeded, run the geometry enrichment:

```bash
python manage.py seed --mode import_bfc_boundaries
```

Validation semantics:

* `import_bfc_boundaries` runs post-processing and then `test_geometries` in strict mode.
* Strict mode fails the command if required boundary tier tables are missing or empty.

To update or overwrite existing geometries, use the `--force` flag.

If you only changed exposed tile properties (for example adding `area_name`), you can rebuild just the post-processed tile tables without re-downloading boundaries:

```bash
python manage.py seed --mode process_geometries
```

For scoped rebuilds, use `--layers`:

```bash
python manage.py seed --mode process_geometries --layers local-authorities
python manage.py seed --mode process_geometries --layers health-geographies
```

Validation semantics for `process_geometries`:

* Full rebuild (`process_geometries` with no `--layers`, or `--layers all`) runs `test_geometries` in strict mode.
* Scoped rebuild (`process_geometries --layers <subset>`) runs `test_geometries` in report-only mode for boundary-tier completeness, so missing/empty unrelated tiers are logged but do not abort the command.

## References

* PostGIS Reference: <https://postgis.net/docs/>
* ONS Geoportal: <https://geoportal.statistics.gov.uk/>
* pg_tileserv: <https://github.com/CrunchyData/pg_tileserv>
