# Windows/local backup helper. Backs up the local SQLite dev database, or
# streams a PostgreSQL dump when Docker is available.

param(
    [string]$ComposeFile = "infrastructure/deployment/docker-compose.prod.yml",
    [string]$BackupDir = "./backups",
    [switch]$UsePostgres
)

$ErrorActionPreference = "Stop"
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null
$stamp = Get-Date -Format "yyyyMMdd_HHmmss"

if ($UsePostgres) {
    $target = Join-Path $BackupDir "prediqo_$stamp.sql"
    docker compose -f $ComposeFile exec -T postgres pg_dump `
        -U $env:POSTGRES_USER prediqo | Set-Content -Path $target
} else {
    $source = "backend/prediqo-dev.db"
    if (-not (Test-Path $source)) {
        throw "Local dev database not found: $source"
    }
    $target = Join-Path $BackupDir "prediqo_dev_$stamp.db"
    Copy-Item -Path $source -Destination $target
}

Write-Output "Backup written to $target"
