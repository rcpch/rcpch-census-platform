# Azure & CDN Setup for UK Deprivation Map

This document outlines the production architecture for deploying the Django REST Framework (DRF) API and the `pg_tileserv` vector tile server to Azure, using **Azure Front Door** as a CDN and load balancer.

## 1. Database: Azure Database for PostgreSQL (Flexible Server)

Both services must connect to the same database instance.

* **Create Server**: Select the **Flexible Server** option in the Azure Portal.
* **Enable PostGIS**: Navigate to **Server Parameters** and search for `azure.extensions`. Add `POSTGIS` to the list.
* **Networking**: 
  * Enable "Allow public access from any Azure service within Azure to this server" OR 
  * Setup a **Virtual Network (VNet)** integration for higher security.
* **Credentials**: Ensure the `DATABASE_URL` used by both services matches your created database name, user, and password.

## 2. Service A: Django API (Azure App Service)

The Django application handles authentication, metadata, and data processing.

* **Service**: Azure App Service (Linux).
* **Runtime Stack**: Python 3.12 (or your specific version).
* **Environment Variables**:
  * `DATABASE_URL`: `postgres://user:pass@your-server.postgres.database.azure.com:5432/yourdb`
  * `ALLOWED_HOSTS`: `api.yourdomain.com`
  * `DEBUG`: `False`
* **Seed Command**: After deployment, use the Azure SSH console or a Deployment Slot script to run the import:

    ```bash
    python manage.py seed --mode import_bfc_boundaries
    ```

## 3. Service B: Tile Server (Azure Container Apps)

`pg_tileserv` is deployed as a lightweight container to serve vector tiles.

* **Service**: Azure Container Apps (ACA).
* **Image**: `pramsey/pg_tileserv:latest`.
* **Networking**: 
  * Enable **Ingress** (External).
  * Target Port: `7800`.
* **Environment Variables**:
  * `DATABASE_URL`: Same as the Django application.
  * `HTTP_PORT`: `7800`
* **CORS Configuration**: Under **Settings > CORS**, add your frontend domain (e.g., `https://map.yourdomain.com`) to allow the browser to fetch tiles from a different origin.

## 4. CDN & Load Balancer: Azure Front Door

Azure Front Door acts as your global entry point, providing SSL termination and caching.

### Routing Configuration

Configure two distinct origins within a single Front Door profile:

| Path Pattern | Origin Group | Destination |
| :--- | :--- | :--- |
| `/api/*` | Django-Origin | Azure App Service (8001/443) |
| `/tiles/*` | Tiles-Origin | Azure Container App (7800/443) |

### Caching Policy (The CDN Part)

For the `/tiles/*` route, create a specialized caching rule:

1. **Query String Behavior**: Set to "Include all query strings" (necessary if you pass parameters like zoom).
2. **Compression**: Enable **Gzip** and **Brotli**. This is critical—vector tiles and GeoJSON are text-heavy and compress significantly.
3. **TTL (Time to Live)**: Set a default TTL of **24 hours**.

## 5. Deployment Workflow & Cache Purging

Whenever you run your `seed` command in production, the CDN cache must be invalidated. 

Update your `purge_cdn_cache` method to use the Azure REST API or Azure CLI to clear Front Door:

```python
# Conceptual Azure Purge logic
az network front-door endpoint purge --content-paths "/tiles/*" "/api/map-data/*" \
    --profile-name MyFrontDoorProfile --resource-group MyResourceGroup