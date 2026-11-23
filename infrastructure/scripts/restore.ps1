# Windows/local restore helper for the SQLite dev database.
# For PostgreSQL use restore.sh on the VPS.

param(
    [Parameter(Mandatory = $true)]
    [string]$BackupFile,
    [string]$Target = "backend/prediqo-dev.db"
)

$ErrorActionPreference = "Stop"
if (-not (Test-Path $BackupFile)) {
    throw "Backup file not found: $BackupFile"
}

Write-Warning "This replaces $Target."
$confirm = Read-Host "Type RESTORE to continue"
if ($confirm -ne "RESTORE") {
    Write-Output "Cancelled."
    exit
}

Copy-Item -Path $BackupFile -Destination $Target -Force
Write-Output "Restored $BackupFile to $Target"
