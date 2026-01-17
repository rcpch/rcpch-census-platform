# Database Seeding Guide

## Overview

The RCPCH Census Platform uses an Azure Database for PostgreSQL Flexible Server as a managed database service. This database needs to be seeded separately from application deployments using database dumps published as GitHub releases.

## Prerequisites

### One-Time Setup Requirements

Before you can seed the database, ensure the following are configured:

1. **Azure Database for PostgreSQL Flexible Server** deployed
2. **PostGIS extensions installed** (requires `azure_pg_admin` role):
   ```sql
   -- Connect as an admin user (e.g., rcpchCensusAdmin)
   CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
   CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;
   ```

3. **Database user permissions** (one-time grant):
   ```sql
   -- Grant azure_pg_admin role to the restore user
   GRANT azure_pg_admin TO census_restore_user;
   
   -- Grant the app role to restore user (for ownership transfer)
   GRANT "rcpch-census-platform" TO census_restore_user;
   ```

4. **Azure Container App** deployed with the restore script included
5. **GitHub releases** with published database dumps (see [Database Dump Creation and Publication Guide](./DATABASE_DUMP_PUBLICATION.md))

### Required Admin Users

You need credentials for one of these admin users to perform the one-time setup:

- `rcpchCensusAdmin` (recommended - purpose-built admin account)
- `michaelbadm@rcpch.ac.uk`
- `simon.chapman@rcpch.ac.uk`
- `rcpch-census-platform-v2`

All have the `azure_pg_admin` role required for extension installation and permission grants.

## Architecture

### Database Connection Flow

```
Azure Container App
├── nginx container
├── web container (Django) ──────┐
└── tiles container (pg_tileserv) ┼─→ Azure Database for PostgreSQL
                                   │   (seeded via restore script)
                                   └────────────────────────────────→
```

The managed database persists independently of application deployments and only needs seeding when:
- Initially setting up a new environment
- Updating to a new data release version
- Restoring from a known-good state

## Seeding Methods

### Method 1: Azure CLI with Container App Exec (Recommended)

This method uses Azure CLI to execute the restore script inside your running container app.

#### Step 1: Install Azure CLI

If not already installed:

```bash
# macOS
brew install azure-cli

# Ubuntu/Debian  
sudo apt-get install azure-cli

# Windows
# Download from https://aka.ms/installazurecliwindows
```

#### Step 2: Authenticate with Azure

```bash
az login
```

#### Step 3: Run the Restore Command

Copy and paste this command, replacing the placeholder values:

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
    CENSUS_RESTORE_USER_PASSWORD='your-password-here' \
    /app/s/restore-db latest
  "
```

**Parameter Explanation**:
- `--name`: Your Azure Container App name
- `--resource-group`: Your Azure resource group
- `--container`: Container to execute in (usually `web`)
- `CONFIRM_RESTORE=true`: Required safety flag to proceed with restore
- `POSTGRES_DB_HOST`: Your Azure PostgreSQL server hostname
- `POSTGRES_DB`: Database name
- `CENSUS_RESTORE_USER`: Database user with `azure_pg_admin` role
- `CENSUS_RESTORE_USER_PASSWORD`: Password for restore user
- `/app/s/restore-db latest`: Script path and version (`latest` or specific tag like `v1.2.0`)

#### What the Script Does

The `restore-db` script will:

1. **Download** the specified database dump version from GitHub releases
2. **Reassemble** split dump files automatically (if the dump exceeds 2GB)
3. **Prepare** the database by dropping and recreating the schema
4. **Install** PostGIS extensions (requires `azure_pg_admin` role)
5. **Restore** all tables, indexes, and constraints
6. **Transfer** ownership to the application role (`rcpch-census-platform`)
7. **Grant** read permissions to the tileserver user
8. **Verify** restoration with table counts
9. **Clean up** temporary files

#### Expected Output

```
==========================================
RCPCH Census – Manual Database Restore
==========================================
Targeting version: v1.2.0
✓ Downloaded rcpch-census-v1.2.0.dump.part-aa
✓ Downloaded rcpch-census-v1.2.0.dump.part-ab
...
✓ Reassembly successful. Size: 4.2G
Step 1: Cleaning Schema & Installing Extensions...
Step 2: Restoring Data...
Step 3: Transferring ownership to rcpch-census-platform...
Step 4: Configuring tileserver access...
Step 5: Verifying restoration...
✓ Restored 45 tables
==========================================
            RESTORE SUCCESSFUL            
==========================================
```

#### Expected Warnings (Safe to Ignore)

You will see warnings about these extensions - **this is normal and expected**:

```
ERROR: extension "fuzzystrmatch" is not allow-listed for users in Azure Database for PostgreSQL
ERROR: required extension "fuzzystrmatch" is not installed
ERROR: extension "postgis_tiger_geocoder" does not exist
```

These extensions are:
- Not available in Azure PostgreSQL's allowlist
- Not required for UK census data (they're for US address geocoding)
- Safely excluded from the restore process

### Method 2: Azure Portal Console (Alternative)

If you prefer a GUI approach:

1. Navigate to Azure Portal → Container Apps
2. Select your container app
3. Go to **Console** → Select **web** container
4. Run the command directly:

```bash
CONFIRM_RESTORE=true \
POSTGRES_DB_HOST='your-server.postgres.database.azure.com' \
POSTGRES_DB='rcpch_census_db' \
CENSUS_RESTORE_USER='census_restore_user' \
CENSUS_RESTORE_USER_PASSWORD='your-password' \
/app/s/restore-db latest
```

## Version Selection

### Using "latest"

```bash
/app/s/restore-db latest
```

Automatically fetches and restores the most recent GitHub release. Recommended for:

- Initial setup
- Getting the most current data
- Development/testing environments

### Using a Specific Version

```bash
/app/s/restore-db v1.2.0
```

Restores a specific tagged release. Recommended for:

- Production environments requiring version pinning
- Rollback scenarios
- Reproducible deployments

### Finding Available Versions

```bash
# List all releases
gh release list --repo rcpch/rcpch-census-platform

# View specific release details
gh release view v1.2.0 --repo rcpch/rcpch-census-platform
```

## Common Workflows

### Initial Environment Setup

```bash
# 1. Deploy Azure Database for PostgreSQL
# 2. Run as admin to install extensions
psql -h your-server.postgres.database.azure.com -U rcpchCensusAdmin -d rcpch_census_db
> CREATE EXTENSION IF NOT EXISTS postgis WITH SCHEMA public;
> CREATE EXTENSION IF NOT EXISTS postgis_topology WITH SCHEMA topology;
> GRANT azure_pg_admin TO census_restore_user;
> GRANT "rcpch-census-platform" TO census_restore_user;
> \q

# 3. Seed the database
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

# 4. Deploy application (it will connect to pre-seeded database)
```

### Updating to New Data Release

```bash
# After a new dump version is published to GitHub releases
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
    /app/s/restore-db v1.3.0
  "
```

### Rollback to Previous Version

```bash
# Restore to a known-good version
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
    /app/s/restore-db v1.1.0
  "
```

## Troubleshooting

### Connection Errors

**Symptom**: `could not connect to server`

**Solutions**:

- Verify firewall rules allow connections from Container App
- Check PostgreSQL server is running
- Confirm hostname and credentials are correct
- Test connection: `psql -h hostname -U username -d database`

### Permission Errors

**Symptom**: `must be owner of extension` or `only members of "azure_pg_admin" are allowed`

**Solutions**:

- Ensure `census_restore_user` has been granted `azure_pg_admin` role
- Run the one-time setup commands as an admin user
- Verify with: `SELECT * FROM pg_roles WHERE rolname = 'census_restore_user';`

### Extension Errors

**Symptom**: `extension "postgis" does not exist`

**Solutions**:

- Install extensions manually as admin user (see Prerequisites)
- Ensure `azure_pg_admin` role is granted
- Check Azure allows PostGIS for your server tier

### Download Failures

**Symptom**: Failed to download dump parts from GitHub

**Solutions**:

- Check GitHub release exists: `gh release view v1.2.0`
- Verify container has internet access
- Check GitHub API rate limits
- Try a different version or `latest`

### Restore Hangs

**Symptom**: Restore process stops responding

**Solutions**:

- Large dumps can take 10-20 minutes - be patient
- Check Azure Container App logs for errors
- Verify database has sufficient storage space
- Monitor PostgreSQL server metrics in Azure Portal

### Verification Failures

**Symptom**: Fewer tables than expected after restore

**Solutions**:

- Review restore logs for errors
- Check for FATAL or PANIC messages (critical errors)
- Warnings about tiger/fuzzystrmatch extensions are normal
- Re-run restore with a different version to compare

## Security Best Practices

1. **Never commit credentials**: Use environment variables, never hardcode passwords
2. **Rotate passwords**: Change `CENSUS_RESTORE_USER_PASSWORD` regularly
3. **Limit firewall rules**: Only allow necessary IP ranges
4. **Use SSL**: Enable SSL connections to the database
5. **Audit access**: Monitor who runs restore operations
6. **Mask secrets**: The script masks passwords in logs automatically

## Performance Considerations

- **Restore time**: 5-20 minutes depending on dump size and network speed
- **Database sizing**: Ensure adequate storage (current dumps are ~5GB, allow 2x for overhead)
- **Compute tier**: Burstable tier sufficient for restore operations
- **Concurrent connections**: Restore requires exclusive access - don't run during high traffic
- **Indexes**: Restored with data automatically, no manual rebuild needed

## Related Documentation

- [Database Dump Creation and Publication Guide](./DATABASE_DUMP_PUBLICATION.md) - How to create and release dumps
- [Deployment Guide](./DEPLOYMENT.md) - Full application deployment workflow
- [Azure Container Apps Documentation](https://learn.microsoft.com/en-us/azure/container-apps/)
- [Azure Database for PostgreSQL Documentation](https://learn.microsoft.com/en-us/azure/postgresql/)

## Support

For issues or questions:

1. Check the restore script logs for detailed error messages
2. Review Azure Database for PostgreSQL logs in Azure Portal
3. Consult PostgreSQL and PostGIS documentation
4. Open an issue in the GitHub repository with logs attached
