#!/bin/bash
set -euo pipefail

# Wait for Postgres to be available using pg_isready
# Uses environment variables if set, otherwise defaults
: ${POSTGRES_DB_HOST:=db}
: ${RCPCH_CENSUS_ENGINE_POSTGRES_DB_PORT:=5432}
: ${POSTGRES_DB_USER:=rcpchCensususer}
: ${POSTGRES_DB_NAME:=rcpchCensusdb}

DB_HOST="$POSTGRES_DB_HOST"
DB_PORT="$RCPCH_CENSUS_ENGINE_POSTGRES_DB_PORT"
DB_USER="$POSTGRES_DB_USER"
DB_NAME="${POSTGRES_DB_NAME:-rcpchCensusdb}"

echo "Waiting for database $DB_HOST:$DB_PORT as $DB_USER..."
until pg_isready -h "$DB_HOST" -p "$DB_PORT" -U "$DB_USER" -d "$DB_NAME" >/dev/null 2>&1; do
  printf '.'
  sleep 1
done
echo "\nDatabase is available"
