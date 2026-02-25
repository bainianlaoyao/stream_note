[CmdletBinding()]
param(
    [Parameter(Mandatory = $false)][string]$ServerHost = "121.43.58.58",
    [Parameter(Mandatory = $false)][string]$ServerUser = "root",
    [Parameter(Mandatory = $false)][string]$ServerPort = "22",
    [Parameter(Mandatory = $false)][string]$RemoteBackendDir = "/opt/stream-note/backend",
    [Parameter(Mandatory = $false)][string]$RemoteFrontendDir = "/var/www/stream-note",
    [Parameter(Mandatory = $false)][string]$RemoteSecretsDir = "/opt/stream-note/secrets",
    [Parameter(Mandatory = $false)][string]$SshKeyPath = "",
    [Parameter(Mandatory = $false)][string]$BackendPort = "8000",
    [switch]$SkipBuild,
    [switch]$SkipBackend,
    [switch]$SkipFrontend,
    [switch]$RestartServices,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"
$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================
# Helper Functions
# ============================================================

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Invoke-SshCommand {
    param(
        [Parameter(Mandatory = $true)][string]$Command
    )

    $sshArgs = @("-p", $ServerPort)
    if ($SshKeyPath) {
        $sshArgs += @("-i", $SshKeyPath)
    }
    $sshArgs += @("$ServerUser@$ServerHost", $Command)

    Write-Host "SSH: $Command"
    if ($DryRun) {
        Write-Host "[DryRun] Would execute via SSH"
        return
    }

    & ssh @sshArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SSH command failed with exit code $LASTEXITCODE"
    }
}

function Invoke-ScpUpload {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target
    )

    $scpArgs = @("-P", $ServerPort, "-r")
    if ($SshKeyPath) {
        $scpArgs += @("-i", $SshKeyPath)
    }
    $scpArgs += @($Source, "$ServerUser@$ServerHost`:$Target")

    Write-Host "SCP: $Source -> $ServerUser@$ServerHost`:$Target"
    if ($DryRun) {
        Write-Host "[DryRun] Would upload via SCP"
        return
    }

    & scp @scpArgs
    if ($LASTEXITCODE -ne 0) {
        throw "SCP upload failed with exit code $LASTEXITCODE"
    }
}

function Invoke-RsyncUpload {
    param(
        [Parameter(Mandatory = $true)][string]$Source,
        [Parameter(Mandatory = $true)][string]$Target,
        [string[]]$Exclude = @()
    )

    $rsyncArgs = @("-avz", "--progress", "-e", "ssh -p $ServerPort")
    if ($SshKeyPath) {
        $rsyncArgs[-1] += " -i $SshKeyPath"
    }
    foreach ($ex in $Exclude) {
        $rsyncArgs += @("--exclude", $ex)
    }
    $rsyncArgs += @($Source, "$ServerUser@$ServerHost`:$Target")

    Write-Host "RSYNC: $Source -> $ServerUser@$ServerHost`:$Target"
    if ($DryRun) {
        Write-Host "[DryRun] Would upload via rsync"
        return
    }

    & rsync @rsyncArgs
    if ($LASTEXITCODE -ne 0) {
        throw "rsync upload failed with exit code $LASTEXITCODE"
    }
}

# ============================================================
# Main Deployment
# ============================================================

$localBackendDir = Join-Path $repoRoot "deploy\backend"
$localFrontendDir = Join-Path $repoRoot "deploy\web"
$localSecretsDir = Join-Path $repoRoot "deploy\secrets"

Write-Host "================================================" -ForegroundColor Green
Write-Host "  Stream Note Remote Deployment" -ForegroundColor Green
Write-Host "================================================" -ForegroundColor Green
Write-Host "Server: $ServerUser@$ServerHost`:$ServerPort"
Write-Host "Remote Backend: $RemoteBackendDir"
Write-Host "Remote Frontend: $RemoteFrontendDir"
Write-Host "Remote Secrets: $RemoteSecretsDir"
Write-Host ""

# Build locally first (default behavior)
if (-not $SkipBuild) {
    Write-Step "Building locally first..."
    $buildArgs = @(
        "-ExecutionPolicy", "Bypass",
        "-File", (Join-Path $repoRoot "build-deploy.ps1"),
        "-SkipBackendRun",
        "-SkipFrontendRun",
        "-SkipAndroid",
        "-SkipIOS"
    )
    if ($DryRun) {
        $buildArgs += "-DryRun"
    }

    & powershell @buildArgs
    if ($LASTEXITCODE -ne 0) {
        throw "Local build failed"
    }
}

# Check local deploy directories exist
if (-not (Test-Path $localBackendDir)) {
    throw "Local backend deploy directory not found: $localBackendDir. The script builds automatically, or use -SkipBuild to skip."
}
if (-not (Test-Path $localFrontendDir)) {
    throw "Local frontend deploy directory not found: $localFrontendDir. The script builds automatically, or use -SkipBuild to skip."
}

# Create remote directories
Write-Step "Creating remote directories..."
Invoke-SshCommand -Command "mkdir -p $RemoteBackendDir $RemoteFrontendDir $RemoteSecretsDir"

# Deploy Backend
if (-not $SkipBackend) {
    Write-Step "Uploading backend..."
    
    # Check if rsync is available
    $rsyncAvailable = Get-Command "rsync" -ErrorAction SilentlyContinue
    if ($rsyncAvailable) {
        Invoke-RsyncUpload `
            -Source "$localBackendDir/" `
            -Target $RemoteBackendDir `
            -Exclude @(".venv", "__pycache__", ".pytest_cache", "*.pyc", "*.db", "*.db-wal", "*.db-shm")
    } else {
        Write-Host "rsync not found, using scp (slower)..."
        Invoke-ScpUpload -Source "$localBackendDir/*" -Target $RemoteBackendDir
    }

    # Upload JWT secret if exists
    $localJwtSecret = Join-Path $localSecretsDir "jwt_secret.txt"
    if (Test-Path $localJwtSecret) {
        Write-Step "Uploading JWT secret..."
        Invoke-ScpUpload -Source $localJwtSecret -Target "$RemoteSecretsDir/jwt_secret.txt"
    }
}

# Deploy Frontend
if (-not $SkipFrontend) {
    Write-Step "Uploading frontend..."
    
    $rsyncAvailable = Get-Command "rsync" -ErrorAction SilentlyContinue
    if ($rsyncAvailable) {
        Invoke-RsyncUpload -Source "$localFrontendDir/" -Target $RemoteFrontendDir
    } else {
        Invoke-ScpUpload -Source "$localFrontendDir/*" -Target $RemoteFrontendDir
    }
}

# Setup and restart services
if ($RestartServices) {
    Write-Step "Setting up remote environment and restarting services..."

    # Create systemd service file for backend
    $backendService = @"
[Unit]
Description=Stream Note Backend API
After=network.target

[Service]
Type=simple
User=root
WorkingDirectory=$RemoteBackendDir
Environment="PATH=$RemoteBackendDir/.venv/bin:/usr/local/bin:/usr/bin:/bin"
EnvironmentFile=$RemoteBackendDir/.env
ExecStart=$RemoteBackendDir/.venv/bin/python -m uvicorn app.main:app --host 0.0.0.0 --port $BackendPort
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
"@

    Write-Host "Creating systemd service..."
    Invoke-SshCommand -Command "echo '$backendService' > /etc/systemd/system/stream-note-backend.service"

    # Create virtual environment and install dependencies
    Write-Host "Setting up Python virtual environment..."
    Invoke-SshCommand -Command "cd $RemoteBackendDir && /root/.local/bin/python3.12 -m venv .venv && .venv/bin/pip install --upgrade pip"
    Invoke-SshCommand -Command "cd $RemoteBackendDir && .venv/bin/pip install -r requirements.txt"

    # Read JWT secret and update .env
    $jwtUpdateCommand = (
        'if [ -f ' + $RemoteSecretsDir + '/jwt_secret.txt ]; then ' +
        'jwt=$(cat ' + $RemoteSecretsDir + '/jwt_secret.txt); ' +
        'sed -i s~^JWT_SECRET_KEY=.\*~JWT_SECRET_KEY=$jwt~ ' +
        $RemoteBackendDir + '/.env; ' +
        'fi'
    )
    Invoke-SshCommand -Command $jwtUpdateCommand

    # Enable and restart services
    Write-Host "Enabling and restarting backend service..."
    Invoke-SshCommand -Command "systemctl daemon-reload"
    Invoke-SshCommand -Command "systemctl enable stream-note-backend"
    Invoke-SshCommand -Command "systemctl restart stream-note-backend"

    # Check status
    Write-Host "Checking service status..."
    Invoke-SshCommand -Command "systemctl status stream-note-backend --no-pager"
}

Write-Step "Deployment Complete!"
Write-Host ""
Write-Host "Frontend URL: http://$ServerHost"
Write-Host "Backend URL:  http://$ServerHost`:$BackendPort/api/v1"
Write-Host ""
Write-Host "To check backend logs:"
Write-Host "  ssh $ServerUser@$ServerHost 'journalctl -u stream-note-backend -f'"
Write-Host ""
Write-Host "To restart backend:"
Write-Host "  ssh $ServerUser@$ServerHost 'systemctl restart stream-note-backend'"
