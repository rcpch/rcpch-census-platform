# init-db/01-download-and-restore.sh
#!/bin/bash
set -e

RELEASE_VERSION="${DB_DUMP_VERSION}"
GITHUB_REPO="rcpch/rcpch-census-platform"
BASE_URL="https://github.com/${GITHUB_REPO}/releases/download/${RELEASE_VERSION}"
DUMP_FILE="rcpch-census-${RELEASE_VERSION}.dump"

echo "=== Starting database initialization ==="
echo "Release version: ${RELEASE_VERSION}"

# Check if database is already populated
if psql -U "$POSTGRES_USER" -d "$POSTGRES_DB" -tAc "SELECT 1 FROM pg_tables WHERE tablename='deprivation_scores_lsoa'" | grep -q 1; then
  echo "Database already initialized, skipping restore"
  exit 0
fi

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
pg_restore -U "$POSTGRES_USER" -d "$POSTGRES_DB" --no-owner --no-acl ${DUMP_FILE} || true

echo "Database restored successfully"
rm ${DUMP_FILE}