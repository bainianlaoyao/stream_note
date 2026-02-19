param(
    [switch]$NoInstall,
    [int]$Port = 5173,
    [string]$BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$webDir = Join-Path $repoRoot "stream-note-web"

if (-not (Test-Path $webDir)) {
    throw "Frontend directory not found: $webDir"
}

Set-Location $webDir

if (-not (Test-Path "node_modules")) {
    if ($NoInstall) {
        throw "node_modules is missing. Remove -NoInstall or run npm install first."
    }

    Write-Host "Installing frontend dependencies..."
    npm install
}

$devArgs = @(
    "run",
    "dev",
    "--",
    "--host", $BindHost,
    "--port", $Port
)

Write-Host "Starting frontend at http://$BindHost`:$Port ..."
npm @devArgs
