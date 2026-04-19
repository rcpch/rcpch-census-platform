# Deployment & Tile Serving Guide

This document describes the complete workflow for deploying the RCPCH Census Platform to Azure, including database seeding, application deployment, and vector tile serving.

## Architecture Overview

The application uses Azure Container Apps with the following components:

```
Azure Container App
├── nginx container (port 80/443) - Reverse proxy and static files
├── web container (port 8000) - Django API
└── tiles container (port 7800) - pg_tileserv vector tile server
     │
     └─→ Azure Database for PostgreSQL Flexible Server
         (Managed database, seeded separately)
```

## Deployment Workflow

### 1. Database Dump Creation and Publication

Before deploying, ensure you have a published database dump:

1. **Build the dump locally**:
   ```bash
   ./s/build-dump
   ```
   This creates a tested dump in `postgis_dump_files/` (gitignored).

2. **Publish to GitHub Releases**:
   ```bash
   ./s/release-dump
   ```
   This creates a versioned GitHub release with the dump file (automatically split if >1.8GB).

For detailed instructions, see [Database Dump Creation and Publication Guide](./database-dump-and-publish.md).

### 2. Database Seeding (One-Time or Updates)

The Azure managed database must be seeded separately from application deployment:

**Using Azure CLI** (recommended):
```bash
az containerapp exec \
  --name rcpch-census-platform \
  --resource-group rcpch-census-platform-rg \
  --command "/bin/bash" \
  --container web \
  -- -c "
    CONFIRM_RESTORE=true \
    POSTGRES_DB_HOST='your-server.postgres.database.azure.com' \
    POSTGRES_DB='rcpch_census_db' \
    CENSUS_RESTORE_USER='census_restore_user' \
    CENSUS_RESTORE_USER_PASSWORD='your-password' \
    /app/s/restore-db latest
  "
```

**When to seed**:
- Initial environment setup
- After publishing a new database dump version
- When rolling back to a previous data version

For detailed instructions, see [Database Seeding Guide](./managed-database-seeding.md).

### 3. Application Deployment

Application deployment is automated via GitHub Actions:

**Trigger**: Push to `live` branch (or configured branch)

**What happens**:
1. GitHub Actions workflow (`.github/workflows/deploy_containerapps.yml`) triggers
2. Django app image is built and pushed to `ghcr.io`
3. Azure Container Apps deployment is updated with:
   - Latest Django app image from GHCR
   - pg_tileserv image (from Docker Hub)
   - nginx image with configuration
4. Containers are deployed together to Azure Container Apps

**Manual deployment** (if needed):
```bash
# Deploy using Azure CLI
az containerapp update \
  --name rcpch-census-platform \
  --resource-group rcpch-census-platform-rg \
  --image ghcr.io/rcpch/rcpch-census-platform:latest
```

**Important**: Application deployment does NOT seed the database. The app expects the database to already be seeded and accessible.

### 4. Post-Deployment Verification

After deployment, verify each component:

**Django API**:
```bash
curl https://census.rcpch.ac.uk/api/health/
```

**Vector Tiles**:
```bash
curl https://census.rcpch.ac.uk/tiles/public.uk_master_2021_z5_7.json
```

**Database Connection** (from within container):
```bash
az containerapp exec \
  --name rcpch-census-platform \
  --resource-group rcpch-census-platform-rg \
  --container web \
  --command "psql -h \$POSTGRES_DB_HOST -U \$POSTGRES_USER -d \$POSTGRES_DB -c 'SELECT COUNT(*) FROM deprivation_scores_lsoa;'"
```

## Serving Vector Tiles

### Container Configuration

The `pg_tileserv` container serves vector tiles from the PostGIS database:

- **Internal port**: 7800
- **External access**: Routed through nginx reverse proxy
- **Tile endpoint**: `https://census.rcpch.ac.uk/tiles/`

### Nginx Routing

The nginx container handles routing to backend services:

```nginx
# Django API
location /api/ {
    proxy_pass http://localhost:8000;
}

# Vector tiles
location /tiles/ {
    proxy_pass http://localhost:7800;
}

# Static files
location /static/ {
    alias /static/;
}
```

### Tile URL Format

Tiles are served using the PostGIS table function pattern:

```
https://census.rcpch.ac.uk/tiles/{table_name}/{z}/{x}/{y}.pbf
```

**Example tile URLs**:
- UK 2021 data (zoom 5-7): `https://census.rcpch.ac.uk/tiles/public.uk_master_2021_z5_7/{z}/{x}/{y}.pbf`
- UK 2021 data (zoom 8-10): `https://census.rcpch.ac.uk/tiles/public.uk_master_2021_z8_10/{z}/{x}/{y}.pbf`
- Local Authority boundaries: `https://census.rcpch.ac.uk/tiles/public.la_tiles/{z}/{x}/{y}.pbf`

### Tile Metadata

Each layer has a JSON metadata endpoint:

```
https://census.rcpch.ac.uk/tiles/{table_name}.json
```

This provides:
- Available zoom levels
- Bounding box
- Column information
- Geometry type

### Client Configuration

Update your frontend map configuration to use the correct tile URLs:

```javascript
// Example for Mapbox GL JS
map.addSource('deprivation-tiles', {
  type: 'vector',
  tiles: [
    'https://census.rcpch.ac.uk/tiles/public.uk_master_2021_z5_7/{z}/{x}/{y}.pbf'
  ],
  minzoom: 5,
  maxzoom: 7
});
```

### CORS Configuration

CORS is handled by nginx to allow requests from your static site:

```nginx
add_header Access-Control-Allow-Origin "https://rcpch.github.io" always;
add_header Access-Control-Allow-Methods "GET, OPTIONS" always;
add_header Access-Control-Allow-Headers "Content-Type" always;
```

Update this configuration in `nginx/nginx.conf` if deploying to different domains.

## Production Considerations

### Caching Strategy

**Azure Front Door** (if configured):
```bash
# Purge tile cache after database updates
az afd endpoint purge \
  --content-paths "/tiles/*" \
  --profile-name census-frontdoor \
  --endpoint-name census-endpoint \
  --resource-group rcpch-census-platform-rg
```

**Cache headers** (set in nginx):
- Tiles: `Cache-Control: public, max-age=86400` (24 hours)
- API: `Cache-Control: public, max-age=3600` (1 hour)
- Metadata: `Cache-Control: public, max-age=43200` (12 hours)

### Database Connection Pooling

The Django app uses connection pooling for efficient database access:

```python
# settings.py
DATABASES = {
    'default': {
        'ENGINE': 'django.contrib.gis.db.backends.postgis',
        'CONN_MAX_AGE': 600,  # 10 minutes
        'OPTIONS': {
            'connect_timeout': 10,
            'options': '-c statement_timeout=30000'  # 30 seconds
        }
    }
}
```

### Monitoring

Monitor these key metrics:

1. **Container health**: CPU, memory, restart counts
2. **Database performance**: Connection count, query duration
3. **Tile requests**: Response times, cache hit ratio
4. **API endpoints**: Request volume, error rates

**Azure Monitor queries**:
```kusto
// Container restarts
ContainerAppConsoleLogs_CL
| where ContainerName_s == "web" or ContainerName_s == "tiles"
| where Log_s contains "restart"
| summarize count() by ContainerName_s, bin(TimeGenerated, 1h)

// Tile request volume
ContainerAppConsoleLogs_CL
| where ContainerName_s == "nginx"
| where Log_s contains "/tiles/"
| summarize requests=count() by bin(TimeGenerated, 5m)
```

### Scaling Considerations

**Current setup** (single replica):
- Suitable for development and low-to-medium traffic
- Database is managed service (scales independently)

**For high traffic**:
- Increase replicas in Container App configuration
- Enable autoscaling based on HTTP queue length or CPU
- Consider read replicas for the database
- Add CDN caching for frequently accessed tiles

### SSL/TLS

SSL is handled automatically by Azure Container Apps custom domains:

1. Configure custom domain in Azure Portal
2. Add DNS records (CNAME to Container App URL)
3. Enable managed certificate or bring your own
4. Force HTTPS redirect in nginx configuration

## Troubleshooting

### Tiles Not Loading

**Symptom**: Map shows no data or tiles fail to load

**Check**:
1. Verify pg_tileserv is running: `curl http://localhost:7800/index.json`
2. Check nginx routing: Review nginx access logs
3. Test database connection: Ensure tables exist and have geometry columns
4. Verify CORS headers: Check browser console for CORS errors
5. Inspect tile URL format: Ensure correct table names and zoom levels

### Database Connection Issues

**Symptom**: Django or pg_tileserv cannot connect to database

**Check**:
1. Verify environment variables: `POSTGRES_DB_HOST`, `POSTGRES_DB`, etc.
2. Check Azure PostgreSQL firewall rules
3. Test connection from container:
   ```bash
   az containerapp exec --name rcpch-census-platform \
     --resource-group rcpch-census-platform-rg \
     --container web \
     --command "pg_isready -h \$POSTGRES_DB_HOST -p 5432"
   ```
4. Review PostgreSQL logs in Azure Portal

### Deployment Failures

**Symptom**: GitHub Actions deployment fails

**Check**:
1. Review workflow logs in GitHub Actions
2. Verify GHCR authentication (PAT token still valid)
3. Check Azure service principal credentials
4. Ensure Container App resource exists
5. Review Azure Activity Log for deployment errors

### Performance Issues

**Symptom**: Slow tile or API responses

**Check**:
1. Database indexes: Ensure geometry columns are indexed
2. Container resources: Check if hitting CPU/memory limits
3. Database query plans: Use `EXPLAIN ANALYZE` for slow queries
4. Network latency: Test from different locations
5. Cache hit rates: Review CDN/cache statistics

## Environment-Specific Configuration

### Development

- Single replica
- Burstable database tier
- No CDN caching
- Verbose logging enabled

### Staging

- 2 replicas for redundancy
- General Purpose database tier
- Short cache TTLs (testing)
- Moderate logging

### Production

- Auto-scaling (2-5 replicas)
- General Purpose or Memory Optimized database
- Aggressive caching (24h for tiles)
- Error-level logging only
- Azure Front Door for global distribution

## Related Documentation

- [Database Seeding Guide](./DATABASE_SEEDING.md) - How to seed the managed database
- [Database Dump Creation and Publication](./DATABASE_DUMP_PUBLICATION.md) - Creating and releasing dumps
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [pg_tileserv Documentation](https://github.com/CrunchyData/pg_tileserv)

## Deployment Checklist

### Initial Setup
- [ ] Create Azure Database for PostgreSQL Flexible Server
- [ ] Install PostGIS extensions as admin
- [ ] Grant permissions to restore user
- [ ] Deploy Container App infrastructure
- [ ] Configure custom domain and SSL
- [ ] Seed database with initial dump
- [ ] Deploy application containers
- [ ] Verify all endpoints respond correctly
- [ ] Configure monitoring and alerts

### Regular Updates
- [ ] Build new database dump locally
- [ ] Test dump restoration
- [ ] Publish dump to GitHub Releases
- [ ] Seed Azure database with new version
- [ ] Deploy updated application code (if needed)
- [ ] Purge CDN caches
- [ ] Verify tile layers load correctly
- [ ] Monitor for errors

### Rollback Procedure
- [ ] Identify last known-good dump version
- [ ] Seed database with previous version
- [ ] Redeploy previous application version (if needed)
- [ ] Purge CDN caches
- [ ] Verify system stability
- [ ] Document incident and lessons learned

---

For support or questions, consult the related documentation or open an issue in the GitHub repository.
