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
| **UK Local Authority** | 2019 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_December_2019_Boundaries_UK_BFC/FeatureServer/0/query) | `LAD19CD` | `local_authority_district_code` |
| **UK Local Authority** | 2024 | [ONS FeatureServer](https://services1.arcgis.com/ESMARspQHYMw9BZ9/arcgis/rest/services/Local_Authority_Districts_May_2024_Boundaries_UK_BFC/FeatureServer/0/query) | `LAD24CD` | `local_authority_district_code` |

## Technical Note: Why we use Streaming over ogr2ogr

While `ogr2ogr` is a standard tool for spatial data migration, this project utilizes a custom Python streaming implementation via `requests` and `GeoPandas`. This approach was chosen to handle the **ArcGIS resultRecordCount** limits more gracefully and to avoid external binary dependencies in the web container. 

The **2024 Local Authority** endpoint, in particular, is sensitive to large requests; therefore, we implement a strict `chunk_size` (e.g., 100 records) to prevent timeout errors and 500-responses from the ArcGIS server. This streaming method ensures that we only move the necessary identifier and geometry fields into the database, keeping memory usage predictable during the enrichment process.

## Architecture: pg_tileserv & CDN

To achieve fast rendering on the frontend:

1. **pg_tileserv**: A dedicated Go-based container connects to the database and serves the SQL views as **MVT (Mapbox Vector Tiles)**.
2. **Resolution Switching**: The frontend automatically requests different views based on zoom level:
    * `z0-z4`: Uses `uk_master_tiles_z0_4` (High simplification).
    * `z5-z7`: Uses `uk_master_tiles_z5_7` (Medium simplification).
    * `z8+`: Uses `uk_master_tiles_z8_10` (Full detail BFC).
3. **CDN**: Tiles are cached at the edge via a CDN to ensure sub-second map interactivity.

## How to Run

After the base IMD data has been seeded, run the geometry enrichment:

```bash
python manage.py seed --mode import_bfc_boundaries
```

To update or overwrite existing geometries, use the `--force` flag.

## References

PostGIS Reference: https://postgis.net/docs/
ONS Geoportal: https://geoportal.statistics.gov.uk/
pg_tileserv: https://github.com/CrunchyData/pg_tileserv