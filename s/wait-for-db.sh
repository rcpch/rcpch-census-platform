#!/bin/bash
set -euo pipefail

# Wait for Postgres to be available and optionally check if populated
# Uses environment variables if set, otherwise defaults
: ${POSTGRES_DB_HOST:=db}
: ${POSTGRES_DB_PORT:=5432}
: ${POSTGRES_USER:=rcpchCensusUser}
: ${POSTGRES_DB:=rcpchCensusdb}
: ${WAIT_FOR_POPULATION:=false}  # Set to 'true' in production

DB_HOST="$POSTGRES_DB_HOST"
DB_PORT="$POSTGRES_DB_PORT"
DB_USER="$POSTGRES_USER"
DB_NAME="${POSTGRES_DB:-rcpchCensusdb}"

echo "Waiting for database $DB_HOST:$DB_PORT as $DB_USER..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  printf '.'
  sleep 1
done
echo ""
echo "Database is accepting connections"

# Only check for population if explicitly requested (production)
if [ "$WAIT_FOR_POPULATION" = "true" ]; then
  echo "Checking if database is populated..."
  until PGPASSWORD="$POSTGRES_PASSWORD" psql -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" -tAc "SELECT 1 FROM pg_tables WHERE tablename='deprivation_scores_lsoa'" 2>/dev/null | grep -q 1; do
    echo "Database not yet populated, waiting for restore to complete..."
    sleep 10
  done
  echo "Database is ready and fully populated!"
else
  echo "Database is ready (skipping population check for local development)"
fi