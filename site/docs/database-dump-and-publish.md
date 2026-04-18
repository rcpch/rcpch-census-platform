# Database Dump Creation and Publication

Because the database for this project is large (>5GB), the recommended workflow is to seed and dump the database locally after making changes, then publish the dump as a GitHub release. This ensures reliable, versioned, and reproducible deployments.

## Why Local Dumping?

- Cloud-based dumps/uploads of large databases are slow and error-prone
- Local seeding and dumping allows for rapid iteration and testing
- The dump is tested before publication, ensuring it can be restored cleanly
- Versioned releases provide rollback capability and deployment reproducibility

## Workflow Overview

1. **Seed and update the database locally** using your Django app and scripts
2. **Build a compressed dump** using the provided convenience script
3. **Test the dump** to ensure it restores cleanly
4. **Publish the dump** as a GitHub release with automatic versioning and split support for large files
5. **Deploy to Azure**: Seed the managed database by running the restore script via Azure CLI

## Step-by-Step Instructions

### 1. Build the Database Dump

Run the following command from the project root:

```bash
./s/build-dump
```

For a release-grade rebuild from scratch, prefer:

```bash
./s/build-dump --fresh --yes
```

To intentionally reuse an already-seeded local build container:

```bash
./s/build-dump --existing --yes
```

This script will:

- Start a local PostGIS container for building the dump
- Build and run the Django seeder image to migrate and seed the database
- Create a compressed dump file in `postgis_dump_files/rcpch-census-{version}.dump`
- Test the dump by restoring it in a fresh container
- Clean up containers
- Prompt before overwriting any existing dump

`./s/build-dump` also supports:

- `--fresh`: always removes any existing build container and reseeds from scratch
- `--existing`: reuses the existing build container and skips reseeding
- `--yes`: auto-confirms prompts where safe

**Note**: This process can take 10-20 minutes depending on your system and the size of the dataset.

### 2. Release the Dump to GitHub

After building and testing the dump locally, publish it using environment variables to specify the dump file path and version tag:

```bash
DUMP_FILE=./postgis_dump_files/rcpch-census.dump \
RELEASE_VERSION=v1.1.0 \
./s/release-dump
```

Replace `rcpch-census.dump` with the actual filename in `postgis_dump_files/` and `v1.1.0` with the version you are releasing (follow semantic versioning — see [Version Numbering Guidelines](#version-numbering-guidelines) below).

This script will:

- Copy and rename the dump to `rcpch-census-{version}.dump`
- Automatically split into <1.9GB chunks if the dump exceeds that (GitHub upload limit)
- Create the GitHub release if it does not already exist
- Upload all files to the release, overwriting any existing assets with the same name

**Example split file naming**:
- `rcpch-census-v1.2.0.dump.part-aa`
- `rcpch-census-v1.2.0.dump.part-ab`
- `rcpch-census-v1.2.0.dump.part-ac`
- etc.

### 3. Seeding the Azure Managed Database

After releasing a new dump version, you need to manually seed (or re-seed) the Azure managed database. See the [Database Seeding Guide](./managed-database-seeding.md) for detailed instructions.

**Quick reference**:
```bash
# Open Azure Container App console and run
CONFIRM_RESTORE=true \
POSTGRES_DB_HOST='your-host.postgres.database.azure.com' \
POSTGRES_DB='your-db-name' \
CENSUS_RESTORE_USER='census_restore_user' \
CENSUS_RESTORE_USER_PASSWORD='your-password' \
/app/s/restore-db v1.2.0
```

### 4. Downloading and Using a Published Dump

If you need to download and restore a dump manually (e.g., for local development):

#### For single-file dumps:

```bash
VERSION="v1.2.0"  # Replace with desired version
wget "https://github.com/rcpch/rcpch-census-platform/releases/download/${VERSION}/rcpch-census-${VERSION}.dump"
```

#### For split dumps (reassembly required):

```bash
VERSION="v1.2.0"  # Replace with desired version

# Download all parts
for char in {a..z}; do
  wget -q "https://github.com/rcpch/rcpch-census-platform/releases/download/${VERSION}/rcpch-census-${VERSION}.dump.part-a${char}" 2>/dev/null || break
done

# Reassemble
cat rcpch-census-${VERSION}.dump.part-* > rcpch-census-${VERSION}.dump

# Clean up parts
rm rcpch-census-${VERSION}.dump.part-*

# Verify
ls -lh rcpch-census-${VERSION}.dump
```

#### Restore to local Docker:
```bash
docker run -d --name postgres-restore \
  -e POSTGRES_PASSWORD=postgres \
  postgis/postgis:16-3.4

# Wait for PostgreSQL to be ready
sleep 5

# Restore
docker exec -i postgres-restore \
  pg_restore -U postgres -d postgres --clean --if-exists --no-owner --no-privileges \
  < rcpch-census-${VERSION}.dump
```

## Version Numbering Guidelines

Follow semantic versioning:

- **Major version** (e.g., v2.0.0): Breaking schema changes or complete dataset overhaul
- **Minor version** (e.g., v1.2.0): New data added, new tables, or backward-compatible changes
- **Patch version** (e.g., v1.2.1): Bug fixes, data corrections, or minor updates

## File Management

- **Storage**: Dump files are stored in `postgis_dump_files/` (gitignored)
- **Cleanup**: Local dumps can be safely deleted after releasing to GitHub
- **Retention**: GitHub releases should be kept indefinitely for rollback capability
- **Size limits**: Individual files must be <2GB for GitHub; the script handles splitting automatically

## Notes

- The dump file is gitignored and should never be committed to the repository
- Always use the provided scripts (`s/build-dump` and `s/release-dump`) for consistency
- The dump is tested locally before release to ensure it restores cleanly
- After updating the database and redeploying, consider invalidating CDN caches if applicable
- Each release is immutable - if you need to make changes, create a new version

## Troubleshooting

### Build Issues

**Problem**: Dump creation fails

- Check Docker is running and has sufficient resources (10GB+ Docker memory recommended)
- Ensure no port conflicts on 5432
- Review logs for migration or seeding errors
- Verify PostGIS extension is available in the container

`s/build-dump` now runs preflight checks before reseeding and will fail early if resources are below threshold.

Default thresholds:
- `BUILD_DUMP_MIN_DISK_GB=30`
- `BUILD_DUMP_MIN_DOCKER_MEM_GB=10`
- `BUILD_DUMP_ENFORCE_RESOURCES=true`

Override example (if you intentionally want lower thresholds):

```bash
BUILD_DUMP_MIN_DISK_GB=20 \
BUILD_DUMP_MIN_DOCKER_MEM_GB=8 \
./s/build-dump --fresh --yes
```

**Problem**: Dump test restoration fails

- Review the test logs for specific errors
- Common issues: missing extensions, permission problems
- The dump may be corrupt if the build was interrupted

### Release Issues

**Problem**: `gh` authentication fails

- Run `gh auth login` and follow prompts
- Ensure you have write access to the repository
- Check your GitHub token has `repo` scope

**Problem**: Upload fails for large files

- The script should auto-split files >1.8GB
- If manual splitting needed, use: `split -b 1800M dump.file dump.part-`
- Verify your internet connection for large uploads

**Problem**: Release already exists

- Choose a different version number
- Delete the existing release if it was created in error
- Use `gh release list` to see existing releases

### Restore Issues

See the [Database Seeding Guide](./managed-database-seeding.md) troubleshooting section for restore-related issues.

## Related Files and Scripts

- `s/build-dump` - Creates and tests the database dump locally
- `s/release-dump` - Publishes the dump to GitHub releases
- `s/restore-db` - Restores a dump to Azure managed database
- `.github/workflows/deploy_containerapps.yml` - Azure deployment workflow
- `postgis_dump_files/` - Local storage for dump files (gitignored)

## Further Reading

- [Database Seeding Guide](./managed-database-seeding.md) - How to seed Azure managed databases
- [PostgreSQL pg_dump Documentation](https://www.postgresql.org/docs/current/app-pgdump.html)
- [GitHub Releases Documentation](https://docs.github.com/en/repositories/releasing-projects-on-github)

---

For more details and advanced options, see the comments in `s/build-dump` and `s/release-dump`.
