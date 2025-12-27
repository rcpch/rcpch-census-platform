# Azure & CDN Setup for UK Deprivation Map

This document outlines the production architecture for deploying the Django REST Framework (DRF) API and the `pg_tileserv` vector tile server to Azure, using **Azure Front Door** and **API Management** for high-performance spatial data delivery.

## 1. Database: Azure Database for PostgreSQL (Flexible Server)

Both services must connect to the same database instance.

* **Create Server**: Select the **Flexible Server** option in the Azure Portal.
* **Enable PostGIS**: Navigate to **Server Parameters**, search for `azure.extensions`, and add `POSTGIS`.
* **Spatial Optimization**: After running your Python build scripts, you must physically reorder the data rows to match the spatial index. This reduces disk I/O for tile requests:
  
    ```sql
    CLUSTER public.uk_master_2021_z5_7 USING idx_uk_master_2021_z5_7_geom;
    ANALYZE public.uk_master_2021_z5_7;
    ```

## 2. Service A: Django API (Azure App Service)

The Django application handles authentication, metadata, and the **Table Materialization Logic**.

* **Service**: Azure App Service (Linux).
* **Build Strategy**: Your Python scripts should create **Physical Tables** with **GIST Indexes** rather than Views to prevent 500 Internal Server Errors in production.
* **Seed Command**:
  
    ```bash
    python manage.py run_spatial_script --mode production
    ```

## 3. Service B: Tile Server (Azure Container Apps)

`pg_tileserv` is deployed as a lightweight container. 

* **Service**: Azure Container Apps (ACA).
* **Performance**: Because we use indexed tables, `pg_tileserv` can remain on a low-consumption tier (0.5 vCPU).
* **Environment Variables**:
  * `DATABASE_URL`: Your PostgreSQL connection string.
  * `HTTP_PORT`: `7800`

## 4. Gateway: Azure API Management (APIM)

In production, APIM sits between your CDN and your services to handle security and protocol translation. Apply the following **Inbound Policy** to handle CORS and internal caching:

```xml
<policies>
    <inbound>
        <base />
        <cors allow-credentials="false">
            <allowed-origins>
                <origin>[https://your-username.github.io](https://your-username.github.io)</origin>
            </allowed-origins>
            <allowed-methods>
                <method>GET</method>
                <method>OPTIONS</method>
            </allowed-methods>
            <allowed-headers>
                <header>*</header>
            </allowed-headers>
        </cors>
        <cache-lookup vary-by-developer="false" vary-by-developer-groups="false" downstream-caching-type="public" must-revalidate="true" caching-type="internal">
            <vary-by-query-parameter>x</vary-by-query-parameter>
            <vary-by-query-parameter>y</vary-by-query-parameter>
            <vary-by-query-parameter>z</vary-by-query-parameter>
        </cache-lookup>
    </inbound>
    <outbound>
        <base />
        <cache-store duration="86400" />
    </outbound>
</policies>
```

## 5. Global Entry: Azure Front Door (CDN)

Azure Front Door provides global caching and SSL termination.

Routing & Caching Configuration
Origin Group: Point to your APIM Gateway Endpoint.

Path Patterns:

/api/* (Django)

/tiles/* (pg_tileserv)

Query String Behavior: Set to "Include all query strings". This is mandatory so that the CDN treats every unique tile coordinate (x, y, z) as a unique cache entry.

Compression: Enable Brotli and Gzip. Vector tiles (.pbf) are highly compressible.

## 6. Deployment Workflow & Cache Purging

Whenever the underlying spatial tables are updated/rebuilt by your Python script, the CDN and APIM caches must be invalidated.

```bash
# Purge logic for Azure Front Door
az network front-door endpoint purge --content-paths "/tiles/*" \
    --profile-name MyFrontDoorProfile --resource-group MyResourceGroup
  ```
