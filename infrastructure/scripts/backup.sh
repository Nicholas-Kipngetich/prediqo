#!/usr/bin/env bash
# Production PostgreSQL backup for a self-hosted Linux VPS.
set -euo pipefail

COMPOSE_FILE="${COMPOSE_FILE:-infrastructure/deployment/docker-compose.prod.yml}"
BACKUP_DIR="${BACKUP_DIR:-./backups}"
DB_NAME="${POSTGRES_DB:-prediqo}"
DB_USER="${POSTGRES_USER:-prediqo}"
STAMP="$(date +%Y%m%d_%H%M%S)"

mkdir -p "$BACKUP_DIR"
TARGET="$BACKUP_DIR/prediqo_${STAMP}.sql.gz"

docker compose -f "$COMPOSE_FILE" exec -T postgres \
  pg_dump -U "$DB_USER" "$DB_NAME" | gzip > "$TARGET"

echo "Backup written to $TARGET"
