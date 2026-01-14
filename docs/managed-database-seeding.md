# Managed Database Seeding

## Overview

Since moving from a sidecar PostgreSQL container to a managed Azure Database for PostgreSQL service, the database needs to be seeded separately from the application deployment. This document explains how to seed your managed database from GitHub releases.

## Background

Previously, the database ran as a sidecar container alongside the application, and the `init-db/01-download-and-restore.sh` script would automatically download and restore the database dump on container startup. 

Now with a managed database service:

- The database persists independently of application deployments
- The database only needs to be seeded once (or when you want to update the data)
- Seeding is done via GitHub Actions workflow or a local script

## Prerequisites

### Azure Resources Required

1. **Azure Database for PostgreSQL** (Flexible Server recommended)
   - PostGIS extension enabled
   - Firewall rules configured to allow connections
   
2. **Azure Key Vault** with the following secrets:
   - `postgres-db-host`: Database server hostname
   - `postgres-db-port`: Database port (usually 5432)
   - `postgres-db-name`: Database name
   - `postgres-db-user`: Database username
   - `postgres-db-password`: Database password

3. **GitHub Secrets** configured:
   - `KEY_VAULT_NAME`: Name of your Azure Key Vault
   - Azure OIDC authentication secrets (AZURE_CLIENT_ID, AZURE_TENANT_ID, AZURE_SUBSCRIPTION_ID)

## Seeding Methods

### Method 1: GitHub Actions Workflow (Recommended)

This is the easiest method for production environments.

#### How to Run

1. Go to your repository on GitHub
2. Navigate to **Actions** → **Seed Managed Azure Database**
3. Click **Run workflow**
4. Choose options:
   - **db_dump_version**: Enter a specific version tag (e.g., `v1.1.0`) or leave as `latest`
   - **force_reseed**: Check this to drop and re-seed an already populated database
5. Click **Run workflow**

#### What It Does

The workflow will:
1. Authenticate with Azure using OIDC
2. Fetch database connection details from Azure Key Vault
3. Download the specified database dump from GitHub releases
4. Handle split dumps automatically (reassembles if needed)
5. Check if database is already populated
6. Restore the dump to your managed database
7. Set appropriate permissions
8. Verify the restoration

#### Monitoring

- View real-time logs in the GitHub Actions interface
- Check the summary at the end for verification details
- Row counts and table listings will be displayed

### Method 2: Local Script

Use this method for local testing or when you need manual control.

#### Prerequisites

Install required tools:
```bash
# macOS
brew install postgresql azure-cli gh wget

# Ubuntu/Debian
sudo apt-get install postgresql-client azure-cli gh wget

# Verify installations
psql --version
az --version
gh --version
```

#### How to Run

1. Authenticate with Azure:
   ```bash
   az login
   ```

2. Authenticate with GitHub (if using Key Vault option):
   ```bash
   gh auth login
   ```

3. Run the seeding script:
   ```bash
   ./s/seed-managed-db
   ```

4. Follow the interactive prompts:
   - Choose connection method (Key Vault or manual entry)
   - Select database dump version (latest or specific)
   - Confirm any actions (like dropping existing data)

#### What It Does

The script will:
1. Verify all required tools are installed
2. Test database connectivity
3. Check if database is already populated
4. Download the dump from GitHub releases (handles split files)
5. Restore the dump
6. Set permissions
7. Verify the restoration
8. Clean up temporary files

## Database Dump Versions

Database dumps are stored as GitHub releases in this repository. Each release contains:

- **Single file**: `rcpch-census-{version}.dump` (if under 2GB)
- **Split files**: `rcpch-census-{version}.dump.part-aa`, `.part-ab`, etc. (if over 2GB)

### Finding Available Versions

```bash
# List recent releases
gh release list

# View specific release
gh release view v1.1.0
```

### Version Selection Strategy

- **Latest**: Use for initial setup or to get the most recent data
- **Specific version**: Use when you need a particular dataset version or for reproducibility

## Workflow Integration

### Initial Database Setup

When setting up a new environment:

1. Deploy the Azure Database for PostgreSQL service
2. Configure PostGIS extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Store connection details in Azure Key Vault
4. Run the seed workflow with `latest` version
5. Deploy your application (it will connect to the pre-seeded database)

### Updating Data

When you need to update the database with new data:

1. Create a new database dump locally using `./s/build-dump`
2. Release it to GitHub using `./s/release-dump`
3. Run the seed workflow with `force_reseed: true` and the new version

### Application Deployment

Your application deployment workflow (`.github/workflows/deploy_containerapps.yml`) should:
1. **Not** include database seeding
2. Simply connect to the managed database using connection strings from Key Vault
3. Run Django migrations if schema changes are needed:
   ```bash
   python manage.py migrate
   ```

## Architecture Differences

### Before (Sidecar Database)

```
Container App
├── nginx container
├── db container (PostGIS)
│   └── init-db script downloads & restores dump on startup
├── web container (Django)
└── tiles container (pg_tileserv)
```

### After (Managed Database)

```
Container App
├── nginx container
├── web container (Django) ──────┐
└── tiles container (pg_tileserv) ┼─→ Azure Database for PostgreSQL
                                   │   (seeded separately via workflow)
                                   └───────────────────────────────────→
```

## Troubleshooting

### Connection Issues

**Problem**: Cannot connect to managed database

**Solutions**:
- Check firewall rules in Azure (allow GitHub Actions IP ranges or your local IP)
- Verify PostGIS extension is enabled
- Confirm connection details in Key Vault are correct
- For GitHub Actions, ensure OIDC federation is configured correctly

### Split File Issues

**Problem**: Download fails for split dumps

**Solutions**:
- Check internet connection
- Verify the release exists and contains all parts
- Both the workflow and script handle split files automatically

### Permission Errors

**Problem**: `pg_restore` fails with permission errors

**Solutions**:
- Ensure the database user has sufficient privileges
- The workflow/script uses `--no-owner` and `--role` flags to handle this
- May need to grant CREATE privileges on the database

### Already Populated

**Problem**: Database already has data

**Solutions**:
- Use `force_reseed: true` in the GitHub Actions workflow
- Confirm when prompted in the local script
- This will drop and recreate the schema

### Large File Timeouts

**Problem**: Restoration takes too long

**Solutions**:
- This is normal for large datasets (5-10 minutes or more)
- GitHub Actions has a generous timeout
- For local runs, ensure stable internet connection
- Consider running locally if GitHub Actions times out

## Security Considerations

1. **Credentials**: Never commit database credentials to the repository
2. **Key Vault**: Store all sensitive connection details in Azure Key Vault
3. **Firewall**: Restrict database access to known IP ranges when possible
4. **SSL**: Enable SSL connections to the managed database
5. **Secrets**: Use `::add-mask::` in workflows to prevent password leakage in logs

## Cost Considerations

- **Managed Database**: Runs 24/7, costs more than sidecar but provides better performance and reliability
- **Seeding**: Only needs to be done once or when data updates are required
- **Storage**: Database backup storage is included with Azure Database for PostgreSQL
- **Compute**: Consider using Burstable tier for dev/test environments

## Migration Checklist

If migrating from sidecar to managed database:

- [ ] Create Azure Database for PostgreSQL
- [ ] Enable PostGIS extension
- [ ] Configure firewall rules
- [ ] Store connection details in Key Vault
- [ ] Test connection from local machine
- [ ] Run seed workflow to populate database
- [ ] Verify data integrity (row counts, geometries)
- [ ] Update application connection strings to point to managed database
- [ ] Remove `db` container from `containerapp.template.yml`
- [ ] Update `deploy_containerapps.yml` to remove database deployment steps
- [ ] Update application environment variables (POSTGRES_DB_HOST, etc.)
- [ ] Deploy application
- [ ] Test application functionality
- [ ] Monitor performance and costs

## Related Scripts

- `s/build-dump`: Creates a database dump locally
- `s/release-dump`: Publishes dump to GitHub releases
- `s/seed-managed-db`: Seeds managed database (local)
- `.github/workflows/seed_managed_db.yml`: Seeds managed database (GitHub Actions)

## Support

For issues or questions:
1. Check the GitHub Actions logs for detailed error messages
2. Review Azure Database for PostgreSQL logs
3. Consult the PostgreSQL and PostGIS documentation
4. Open an issue in this repository
