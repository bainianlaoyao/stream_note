param(
    [switch]$NoInstall,
    [switch]$NoReload,
    [int]$Port = 8000,
    [string]$BindHost = "127.0.0.1"
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$apiDir = Join-Path $repoRoot "stream-note-api"

if (-not (Test-Path $apiDir)) {
    throw "Backend directory not found: $apiDir"
}

$uvCmd = Get-Command uv -ErrorAction SilentlyContinue
if (-not $uvCmd) {
    throw "uv not found. Install uv first: https://docs.astral.sh/uv/getting-started/installation/"
}

Set-Location $apiDir

if (-not (Test-Path ".env") -and (Test-Path ".env.example")) {
    Copy-Item ".env.example" ".env"
    Write-Host "Created stream-note-api/.env from .env.example"
}

# Disable uv cache to avoid cache file permission issues on locked Windows setups.
$env:UV_NO_CACHE = "1"

$venvPython = Join-Path $apiDir ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment with uv..."
    & $uvCmd.Source venv .venv
}

if (-not $NoInstall) {
    Write-Host "Syncing backend dependencies with uv..."
    & $uvCmd.Source sync --python $venvPython
}
else {
    $savedPreference = $ErrorActionPreference
    $importExitCode = 0
    try {
        $ErrorActionPreference = "Continue"
        & $uvCmd.Source run --python $venvPython python -c "import uvicorn" *> $null
        $importExitCode = $LASTEXITCODE
    }
    finally {
        $ErrorActionPreference = $savedPreference
    }

    if ($importExitCode -ne 0) {
        throw "Dependencies are missing in .venv. Run script once without -NoInstall."
    }
}

$runArgs = @(
    "run",
    "--python", $venvPython,
    "python",
    "-m",
    "uvicorn",
    "app.main:app",
    "--host", $BindHost,
    "--port", $Port
)

if (-not $NoReload) {
    $runArgs += "--reload"
}

Write-Host "Starting backend at http://$BindHost`:$Port ..."
& $uvCmd.Source @runArgs
