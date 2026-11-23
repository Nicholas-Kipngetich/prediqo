#!/usr/bin/env bash
# Restore a gzipped PostgreSQL backup into the production compose stack.
# Usage: ./restore.sh ./backups/prediqo_20260101_120000.sql.gz
set -euo pipefail

if [ "$#" -ne 1 ]; then
  echo "Usage: $0 <backup.sql.gz>" >&2
  exit 1
fi

BACKUP_FILE="$1"
if [ ! -f "$BACKUP_FILE" ]; then
  echo "Backup file not found: $BACKUP_FILE" >&2
  exit 1
fi

COMPOSE_FILE="${COMPOSE_FILE:-infrastructure/deployment/docker-compose.prod.yml}"
DB_NAME="${POSTGRES_DB:-prediqo}"
DB_USER="${POSTGRES_USER:-prediqo}"

echo "WARNING: this replaces the current database contents."
read -r -p "Type RESTORE to continue: " CONFIRM
if [ "$CONFIRM" != "RESTORE" ]; then
  echo "Cancelled."
  exit 1
fi

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$DB_USER" -d "$DB_NAME" -c "DROP SCHEMA public CASCADE; CREATE SCHEMA public;"
gunzip -c "$BACKUP_FILE" | docker compose -f "$COMPOSE_FILE" exec -T postgres \
  psql -U "$DB_USER" -d "$DB_NAME"

echo "Restore complete. Run alembic upgrade head if migrations are ahead of the backup."
