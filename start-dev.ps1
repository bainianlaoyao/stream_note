param(
    [switch]$NoInstall,
    [switch]$NoBackendInstall,
    [switch]$NoFrontendInstall,
    [switch]$NoReload,
    [int]$BackendPort = 8000,
    [string]$BackendHost = "127.0.0.1",
    [int]$FrontendPort = 5173,
    [string]$FrontendHost = "127.0.0.1",
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$backendScript = Join-Path $repoRoot "start-backend.ps1"
$frontendScript = Join-Path $repoRoot "start-frontend.ps1"

if (-not (Test-Path $backendScript)) {
    throw "Backend launcher not found: $backendScript"
}

if (-not (Test-Path $frontendScript)) {
    throw "Frontend launcher not found: $frontendScript"
}

$skipBackendInstall = $NoInstall -or $NoBackendInstall
$skipFrontendInstall = $NoInstall -or $NoFrontendInstall

$backendArgs = @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$backendScript`"",
    "-Port", $BackendPort,
    "-BindHost", $BackendHost
)

if ($skipBackendInstall) {
    $backendArgs += "-NoInstall"
}

if ($NoReload) {
    $backendArgs += "-NoReload"
}

$frontendArgs = @(
    "-NoExit",
    "-ExecutionPolicy", "Bypass",
    "-File", "`"$frontendScript`"",
    "-Port", $FrontendPort,
    "-BindHost", $FrontendHost
)

if ($skipFrontendInstall) {
    $frontendArgs += "-NoInstall"
}

if ($DryRun) {
    Write-Host "Backend command:"
    Write-Host "powershell $($backendArgs -join ' ')"
    Write-Host ""
    Write-Host "Frontend command:"
    Write-Host "powershell $($frontendArgs -join ' ')"
    exit 0
}

Write-Host "Launching backend window..."
Start-Process -FilePath "powershell" -ArgumentList $backendArgs -WorkingDirectory $repoRoot

Write-Host "Launching frontend window..."
Start-Process -FilePath "powershell" -ArgumentList $frontendArgs -WorkingDirectory $repoRoot

Write-Host ""
Write-Host "Dev servers are starting:"
Write-Host "- Backend:  http://$BackendHost`:$BackendPort"
Write-Host "- Frontend: http://$FrontendHost`:$FrontendPort"
Write-Host ""
Write-Host "Two PowerShell windows were opened. Close them to stop the servers."
