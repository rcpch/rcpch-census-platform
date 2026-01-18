# init-db/01-download-and-restore.sh
#!/bin/bash
set -e

RELEASE_VERSION="${DB_DUMP_VERSION}"
GITHUB_REPO="rcpch/rcpch-census-platform"
BASE_URL="https://github.com/${GITHUB_REPO}/releases/download/${RELEASE_VERSION}"
DUMP_FILE="rcpch-census-${RELEASE_VERSION}.dump"
WORK_DIR="/tmp"  # Use /tmp for write access

echo "=== Starting database initialization ==="
echo "Release version: ${RELEASE_VERSION}"
echo "Target user: ${POSTGRES_USER}"
echo "Target database: ${POSTGRES_DB}"

# Debug: Show what's in the database
echo "Checking current database state..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt" || echo "No tables yet"

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

# Ensure the user has necessary privileges
echo "Ensuring database role '${POSTGRES_USER}' has necessary privileges..."
psql -v ON_ERROR_STOP=1 --username "$POSTGRES_USER" --dbname "$POSTGRES_DB" <<-EOSQL
  -- User already exists from container initialization
  ALTER ROLE "${POSTGRES_USER}" WITH CREATEDB CREATEROLE;
EOSQL

echo "Downloading database dump ${RELEASE_VERSION}..."

# Change to working directory
cd "$WORK_DIR"

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


# Check dump file exists and is not empty
if [ ! -f "$DUMP_FILE" ]; then
  echo "ERROR: Dump file $DUMP_FILE not found. Aborting restore."
  exit 1
fi
if [ ! -s "$DUMP_FILE" ]; then
  echo "ERROR: Dump file $DUMP_FILE is empty. Aborting restore."
  exit 1
fi

echo "Restoring database (this may take 5-10 minutes)..."
echo "Using pg_restore with --no-owner and --role=${POSTGRES_USER}"

# Restore with explicit role assignment
set +e
pg_restore \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-owner \
  --no-acl \
  --role="$POSTGRES_USER" \
  -v \
  "$DUMP_FILE" 2>&1 | grep -v "^$"
RESTORE_EXIT_CODE=${PIPESTATUS[0]}
set -e
if [ $RESTORE_EXIT_CODE -ne 0 ]; then
  echo "ERROR: pg_restore failed with exit code $RESTORE_EXIT_CODE. The dump file may be corrupt or incompatible."
  exit $RESTORE_EXIT_CODE
fi

# Grant all privileges on restored objects to the role
echo "Setting permissions on restored objects..."
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" <<-EOSQL
  -- Grant privileges on all tables
  GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO "${POSTGRES_USER}";
  GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO "${POSTGRES_USER}";
  GRANT ALL PRIVILEGES ON ALL FUNCTIONS IN SCHEMA public TO "${POSTGRES_USER}";
  
  -- Set default privileges for future objects
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON TABLES TO "${POSTGRES_USER}";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON SEQUENCES TO "${POSTGRES_USER}";
  ALTER DEFAULT PRIVILEGES IN SCHEMA public GRANT ALL ON FUNCTIONS TO "${POSTGRES_USER}";
EOSQL

echo "Database restored successfully"

# Log table and row counts for verification
echo "=== Post-restore verification ==="
echo "Tables in database:"
psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "\dt"

# Log row count for a key table (deprivation_scores_lsoa)
if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -c "SELECT COUNT(*) FROM deprivation_scores_lsoa;" 2>/dev/null; then
  echo "Row count for deprivation_scores_lsoa table logged above."
else
  echo "Could not log row count for deprivation_scores_lsoa (table may not exist)."
fi

echo "Cleaning up dump file..."
rm -f ${WORK_DIR}/${DUMP_FILE}

echo "=== Database initialization complete ==="