# init-db/01-download-and-restore.sh
#!/bin/bash
set -e

RELEASE_VERSION="${DB_DUMP_VERSION}"
GITHUB_REPO="rcpch/rcpch-census-platform"
BASE_URL="https://github.com/${GITHUB_REPO}/releases/download/${RELEASE_VERSION}"
DUMP_FILE="rcpch-census-${RELEASE_VERSION}.dump"

echo "=== Starting database initialization ==="
echo "Release version: ${RELEASE_VERSION}"
echo "Target user: ${POSTGRES_USER}"
echo "Target database: ${POSTGRES_DB}"

# Wait for PostgreSQL to be fully ready
echo "Waiting for PostgreSQL to be ready..."
until pg_isready -U "$POSTGRES_USER" -d "$POSTGRES_DB" -q; do
  sleep 1
done
echo "PostgreSQL is ready"

# Check if database is already populated
if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_tables WHERE tablename='deprivation_scores_lsoa'" 2>/dev/null | grep -q 1; then
  echo "Database already initialized, skipping restore"
  exit 0
fi

# Ensure the target role exists and has necessary privileges
echo "Ensuring database role '${POSTGRES_USER}' exists..."
psql -v ON_ERROR_STOP=1 --username "postgres" --dbname "$POSTGRES_DB" <<-EOSQL
  -- Ensure role exists (use lowercase or quoted to preserve case)
  DO \$\$
  BEGIN
    -- Use the exact username provided, quoted to preserve case
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = '${POSTGRES_USER}') THEN
      CREATE ROLE "${POSTGRES_USER}" WITH LOGIN PASSWORD '${POSTGRES_PASSWORD}';
      RAISE NOTICE 'Created role: ${POSTGRES_USER}';
    ELSE
      RAISE NOTICE 'Role already exists: ${POSTGRES_USER}';
    END IF;
  END
  \$\$;

  -- Ensure role has necessary privileges (quote the role name)
  ALTER ROLE "${POSTGRES_USER}" WITH CREATEDB CREATEROLE;
  GRANT ALL PRIVILEGES ON DATABASE "${POSTGRES_DB}" TO "${POSTGRES_USER}";
EOSQL

echo "Downloading database dump ${RELEASE_VERSION}..."

# Check if dump is split
PART_AA="${DUMP_FILE}.part-aa"
if wget --spider "${BASE_URL}/${PART_AA}" 2>/dev/null; then
  echo "Detected split dump, downloading and reassembling..."
  
  # Download all parts
  for part in {a..z}; do
    PART_FILE="${DUMP_FILE}.part-a${part}"
    if wget -q "${BASE_URL}/${PART_FILE}" 2>/dev/null; then
      echo "Downloaded ${PART_FILE}"
    else
      break
    fi
  done
  
  # Reassemble
  cat ${DUMP_FILE}.part-* > ${DUMP_FILE}
  rm ${DUMP_FILE}.part-*
  echo "Reassembled dump file"
else
  # Single file download
  echo "Downloading single dump file..."
  wget -q "${BASE_URL}/${DUMP_FILE}"
fi

echo "Restoring database (this may take 5-10 minutes)..."
echo "Using pg_restore with --no-owner and --role=${POSTGRES_USER}"

# Restore with explicit role assignment
# --no-owner: Don't restore ownership
# --no-acl: Don't restore access privileges
# --role: Set ownership to this role for all objects
# -v: Verbose output for debugging
pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-owner \
  --no-acl \
  --role="$POSTGRES_USER" \
  -v \
  ${DUMP_FILE} 2>&1 | grep -v "^$" || true

# Grant all privileges on restored objects to the role
echo "Setting permissions on restored objects..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  -- Grant privileges on all tables
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${POSTGRES_USER};
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO ${POSTGRES_USER};
  GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO ${POSTGRES_USER};
  
  -- Set default privileges for future objects
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO ${POSTGRES_USER};
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO ${POSTGRES_USER};
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO ${POSTGRES_USER};
EOSQL

echo "Database restored successfully"
echo "Cleaning up dump file..."
rm ${DUMP_FILE}

echo "=== Database initialization complete ==="