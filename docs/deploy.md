
# Deployment & Serving Tiles: UK Deprivation Map

This document describes the workflow for database seeding, application deployment, and serving vector tiles for the UK Deprivation Map project.

## 1. Database Seeding & Dumping

1. **Seed the database locally**: Run the database and Django app in development mode. Populate the database as needed.
2. **Dump the database**: Use `pg_dump` to export the seeded database to the `postgis_dump_files` folder at the project root (this folder is gitignored).
3. **Publish the dump**: Use the convenience script in the `s/` folder to upload the dump file as a GitHub Release asset.

## 2. Application Deployment (Azure Container Apps)

Deployment is managed as a sidecar container arrangement:

- On push to the `shapes` branch (and in future, merge to `live`), a GitHub Actions workflow builds and pushes the Django app image to `ghcr.io`.
- The Azure deployment template pulls:
  - The Django app image from GHCR
  - The database dump from GitHub Releases
  - The `pg_tileserv` and `postgis` images from open source
- The containers are deployed together to Azure Container Apps:
  - Django app (port 8000)
  - PostGIS database (port 5432, internal)
  - pg_tileserv (port 7800)

## 3. Serving Vector Tiles to the Static Client

The static client (in the `site/` folder, deployed via GitHub Pages) needs to access both the Django API and the vector tile server.

- **Django API**: Exposed on port 8000 via Azure ingress.
- **pg_tileserv**: By default, serves on port 7800. To make this accessible externally:
  - Expose port 7800 in your Azure Container Apps ingress configuration, or
  - Use Azure Front Door or API Management to route `/tiles/*` to the tileserv container.
- **CORS**: Ensure CORS headers are set to allow requests from your GitHub Pages domain.

**Example:**

If your Azure Container App is at `https://myapp.azurecontainerapps.io`, and you expose both ports:

- Django API: `https://myapp.azurecontainerapps.io/api/`
- Tiles: `https://myapp.azurecontainerapps.io:7800/tiles/{z}/{x}/{y}.pbf`

Or, if using a single ingress and path-based routing:

- Django API: `https://myapp.azurecontainerapps.io/api/`
- Tiles: `https://myapp.azurecontainerapps.io/tiles/{z}/{x}/{y}.pbf`

Update your `site/map-logic.js` to point to the correct tiles URL.

## 4. Notes on Production

- In production, you may use Azure Front Door or API Management for SSL, caching, and routing.
- Remember to invalidate CDN caches after updating spatial tables or redeploying.

## 5. Cache Purging Example

```bash
# Purge logic for Azure Front Door
az network front-door endpoint purge --content-paths "/tiles/*" \
    --profile-name MyFrontDoorProfile --resource-group MyResourceGroup
```
