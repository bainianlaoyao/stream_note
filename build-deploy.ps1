[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$SkipAndroid,
    [switch]$SkipIOS,
    [switch]$SkipBackendRun,
    [switch]$SkipFrontendRun,
    [switch]$SyncBackendSource,
    [switch]$DryRun
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

# ============================================================
# Deploy Config (edit this block to match your server settings)
# ============================================================
$config = [ordered]@{
    FrontendProjectDir = Join-Path $repoRoot "stream-note-web"
    BackendProjectDir  = Join-Path $repoRoot "stream-note-api"

    # Runtime directories on server
    BackendDeployDir   = Join-Path $repoRoot "deploy\backend"
    FrontendDeployDir  = Join-Path $repoRoot "deploy\web"
    ArtifactDir        = Join-Path $repoRoot "artifacts"
    LogDir             = Join-Path $repoRoot "deploy\logs"

    # Runtime bind host/port
    BackendBindHost    = "0.0.0.0"
    BackendPort        = 8000
    FrontendBindHost   = "0.0.0.0"
    FrontendPort       = 8080

    # Public backend address used by frontend build
    BackendPublicHost  = "121.43.58.58"
    BackendPublicPort  = 8000

    # Public frontend origin (used in backend CORS)
    FrontendPublicOrigin = "http://121.43.58.58"

    # Extra CORS origins for mobile shell
    AdditionalCorsOrigins = @(
        "http://localhost",
        "https://localhost",
        "http://127.0.0.1",
        "https://127.0.0.1",
        "capacitor://localhost",
        "ionic://localhost"
    )

    # iOS packaging config (only used on macOS)
    IOSExportMethod = "development" # development | ad-hoc | app-store | enterprise
    IOSTeamID       = ""
}

function Write-Step([string]$Message) {
    Write-Host ""
    Write-Host "==> $Message" -ForegroundColor Cyan
}

function Ensure-Directory([string]$Path) {
    if ($DryRun) {
        Write-Host "[DryRun] Ensure dir: $Path"
        return
    }

    if (-not (Test-Path $Path)) {
        New-Item -ItemType Directory -Path $Path -Force | Out-Null
    }
}

function Ensure-Command([string]$Name) {
    $command = Get-Command $Name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Command not found: $Name"
    }
    return $command.Source
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    $prettyArgs = $Arguments -join " "
    Write-Host "$Executable $prettyArgs"

    if ($DryRun) {
        return
    }

    Push-Location $WorkingDirectory
    try {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed ($LASTEXITCODE): $Executable $prettyArgs"
        }
    }
    finally {
        Pop-Location
    }
}

function Sync-Directory {
    param(
        [Parameter(Mandatory = $true)][string]$SourceDir,
        [Parameter(Mandatory = $true)][string]$TargetDir,
        [string[]]$ExcludeDirs = @(),
        [string[]]$ExcludeFiles = @()
    )

    if (-not (Test-Path $SourceDir)) {
        throw "Source directory not found: $SourceDir"
    }

    Ensure-Directory $TargetDir

    $args = @($SourceDir, $TargetDir, "/MIR", "/NFL", "/NDL", "/NJH", "/NJS", "/NP")
    foreach ($dir in $ExcludeDirs) {
        $args += @("/XD", $dir)
    }
    foreach ($file in $ExcludeFiles) {
        $args += @("/XF", $file)
    }

    Write-Host "robocopy $($args -join ' ')"
    if ($DryRun) {
        return
    }

    & robocopy @args | Out-Null
    $code = $LASTEXITCODE
    if ($code -gt 7) {
        throw "robocopy failed with exit code $code"
    }
}

function Upsert-EnvValue {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string]$Key,
        [Parameter(Mandatory = $true)][string]$Value
    )

    if ($DryRun) {
        Write-Host "[DryRun] Set env: $Key=$Value in $FilePath"
        return
    }

    $lines = @()
    if (Test-Path $FilePath) {
        $lines = Get-Content -Path $FilePath
    }

    $updated = $false
    for ($i = 0; $i -lt $lines.Count; $i++) {
        if ($lines[$i] -match "^\s*$Key=") {
            $lines[$i] = "$Key=$Value"
            $updated = $true
            break
        }
    }

    if (-not $updated) {
        $lines += "$Key=$Value"
    }

    Set-Content -Path $FilePath -Value $lines -Encoding UTF8
}

function Resolve-IsMacOS {
    if ($PSVersionTable.PSVersion.Major -ge 6) {
        return $IsMacOS
    }
    return ($env:OS -ne "Windows_NT" -and (uname) -eq "Darwin")
}

function Start-BackgroundProcess {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory,
        [Parameter(Mandatory = $true)][string]$StdOutFile,
        [Parameter(Mandatory = $true)][string]$StdErrFile
    )

    $prettyArgs = $Arguments -join " "
    Write-Host "Start-Process $FilePath $prettyArgs"

    if ($DryRun) {
        return $null
    }

    $proc = Start-Process `
        -FilePath $FilePath `
        -ArgumentList $Arguments `
        -WorkingDirectory $WorkingDirectory `
        -RedirectStandardOutput $StdOutFile `
        -RedirectStandardError $StdErrFile `
        -PassThru

    return $proc
}

# ------------------------------------------------------------
# Derived values
# ------------------------------------------------------------
$backendBaseUrl = "http://$($config.BackendPublicHost):$($config.BackendPublicPort)"
$frontendApiBaseUrl = "$backendBaseUrl/api/v1"
$corsOrigins = @(
    $config.FrontendPublicOrigin,
    "http://localhost:$($config.FrontendPort)",
    "http://127.0.0.1:$($config.FrontendPort)"
) + $config.AdditionalCorsOrigins
$corsValue = ($corsOrigins | Select-Object -Unique) -join ","

$frontendDir = $config.FrontendProjectDir
$backendSourceDir = $config.BackendProjectDir
$backendDeployDir = $config.BackendDeployDir
$frontendDeployDir = $config.FrontendDeployDir
$artifactDir = $config.ArtifactDir
$logDir = $config.LogDir

$androidProjectDir = Join-Path $frontendDir "android"
$iosProjectRoot = Join-Path $frontendDir "ios\App"

Write-Step "Validate required commands"
$uvCmd = Ensure-Command "uv"
$npmCmd = Ensure-Command "npm"
$npxCmd = Ensure-Command "npx"

Write-Step "Prepare output directories"
Ensure-Directory $artifactDir
Ensure-Directory $logDir
Ensure-Directory $backendDeployDir
Ensure-Directory $frontendDeployDir

if (-not (Test-Path $frontendDir)) {
    throw "Frontend project directory not found: $frontendDir"
}
if (-not (Test-Path $backendSourceDir)) {
    throw "Backend project directory not found: $backendSourceDir"
}

Write-Step "Prepare backend deploy directory"
$backendSourceFull = [System.IO.Path]::GetFullPath($backendSourceDir)
$backendDeployFull = [System.IO.Path]::GetFullPath($backendDeployDir)
$needSyncBackend = $SyncBackendSource -or ($backendSourceFull -ne $backendDeployFull)
if ($needSyncBackend) {
    Sync-Directory -SourceDir $backendSourceDir -TargetDir $backendDeployDir -ExcludeDirs @(".venv", "__pycache__", ".pytest_cache", ".ruff_cache")
}

$backendEnvFile = Join-Path $backendDeployDir ".env"
$backendEnvExample = Join-Path $backendDeployDir ".env.example"
if (-not (Test-Path $backendEnvFile) -and (Test-Path $backendEnvExample)) {
    if ($DryRun) {
        Write-Host "[DryRun] Copy $backendEnvExample -> $backendEnvFile"
    }
    else {
        Copy-Item $backendEnvExample $backendEnvFile
    }
}
Upsert-EnvValue -FilePath $backendEnvFile -Key "CORS_ALLOW_ORIGINS" -Value $corsValue

Write-Step "Build frontend dist (API base URL from script config)"
if ((-not $SkipInstall) -and (-not (Test-Path (Join-Path $frontendDir "node_modules")))) {
    Invoke-External -Executable $npmCmd -Arguments @("install") -WorkingDirectory $frontendDir
}

$previousApiEnv = $env:VITE_API_BASE_URL
$env:VITE_API_BASE_URL = $frontendApiBaseUrl
try {
    Invoke-External -Executable $npmCmd -Arguments @("run", "build") -WorkingDirectory $frontendDir
    Invoke-External -Executable $npmCmd -Arguments @("run", "cap:sync") -WorkingDirectory $frontendDir
}
finally {
    if ($null -eq $previousApiEnv) {
        Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:VITE_API_BASE_URL = $previousApiEnv
    }
}

$distDir = Join-Path $frontendDir "dist"
if (-not (Test-Path $distDir)) {
    throw "Frontend dist directory not found: $distDir"
}

Write-Step "Deploy frontend static files"
Sync-Directory -SourceDir $distDir -TargetDir $frontendDeployDir

if (-not $SkipAndroid) {
    Write-Step "Build Android install files (APK + AAB)"
    if (-not (Test-Path $androidProjectDir)) {
        throw "Android project not found: $androidProjectDir. Run: npm run cap:add:android"
    }

    $gradlew = Join-Path $androidProjectDir "gradlew.bat"
    if (-not (Test-Path $gradlew)) {
        throw "Gradle wrapper not found: $gradlew"
    }

    Invoke-External -Executable $gradlew -Arguments @("assembleRelease", "bundleRelease") -WorkingDirectory $androidProjectDir

    $apkSource = Join-Path $androidProjectDir "app\build\outputs\apk\release\app-release.apk"
    $aabSource = Join-Path $androidProjectDir "app\build\outputs\bundle\release\app-release.aab"
    $androidArtifactDir = Join-Path $artifactDir "android"
    Ensure-Directory $androidArtifactDir

    if (-not $DryRun) {
        if (Test-Path $apkSource) {
            Copy-Item $apkSource (Join-Path $androidArtifactDir "stream-note-release.apk") -Force
        }
        else {
            throw "Android APK not found: $apkSource"
        }

        if (Test-Path $aabSource) {
            Copy-Item $aabSource (Join-Path $androidArtifactDir "stream-note-release.aab") -Force
        }
        else {
            throw "Android AAB not found: $aabSource"
        }
    }
}
else {
    Write-Step "Skip Android build"
}

if (-not $SkipIOS) {
    Write-Step "Build iOS install file (IPA)"
    if (-not (Resolve-IsMacOS)) {
        Write-Warning "iOS packaging requires macOS + Xcode. Current OS is not macOS, iOS build skipped."
    }
    else {
        $xcodebuild = Ensure-Command "xcodebuild"
        if ([string]::IsNullOrWhiteSpace($config.IOSTeamID)) {
            throw "config.IOSTeamID is empty. Set Team ID in build-deploy.ps1 before iOS packaging."
        }

        $xcodeproj = Join-Path $iosProjectRoot "App.xcodeproj"
        if (-not (Test-Path $xcodeproj)) {
            throw "iOS project not found: $xcodeproj. Run: npm run cap:add:ios"
        }

        $iosArtifactDir = Join-Path $artifactDir "ios"
        $archivePath = Join-Path $iosArtifactDir "StreamNote.xcarchive"
        $exportPath = Join-Path $iosArtifactDir "export"
        $exportOptions = Join-Path $iosArtifactDir "ExportOptions.plist"

        Ensure-Directory $iosArtifactDir

        $plist = @"
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>method</key>
    <string>$($config.IOSExportMethod)</string>
    <key>signingStyle</key>
    <string>automatic</string>
    <key>teamID</key>
    <string>$($config.IOSTeamID)</string>
    <key>stripSwiftSymbols</key>
    <true/>
    <key>compileBitcode</key>
    <false/>
</dict>
</plist>
"@

        if ($DryRun) {
            Write-Host "[DryRun] Write $exportOptions"
        }
        else {
            Set-Content -Path $exportOptions -Value $plist -Encoding UTF8
        }

        Invoke-External -Executable $xcodebuild -Arguments @(
            "-project", $xcodeproj,
            "-scheme", "App",
            "-configuration", "Release",
            "-archivePath", $archivePath,
            "archive",
            "DEVELOPMENT_TEAM=$($config.IOSTeamID)",
            "-allowProvisioningUpdates"
        ) -WorkingDirectory $iosProjectRoot

        Invoke-External -Executable $xcodebuild -Arguments @(
            "-exportArchive",
            "-archivePath", $archivePath,
            "-exportPath", $exportPath,
            "-exportOptionsPlist", $exportOptions,
            "-allowProvisioningUpdates"
        ) -WorkingDirectory $iosProjectRoot

        if (-not $DryRun) {
            $ipa = Get-ChildItem -Path $exportPath -Filter "*.ipa" -File -ErrorAction SilentlyContinue | Select-Object -First 1
            if ($null -eq $ipa) {
                throw "iOS export completed but IPA file not found in $exportPath"
            }
            Copy-Item $ipa.FullName (Join-Path $iosArtifactDir "stream-note-release.ipa") -Force
        }
    }
}
else {
    Write-Step "Skip iOS build"
}

Write-Step "Prepare backend virtual environment"
$venvPythonWin = Join-Path $backendDeployDir ".venv\Scripts\python.exe"
if ((-not $DryRun) -and (-not (Test-Path $venvPythonWin))) {
    Invoke-External -Executable $uvCmd -Arguments @("venv", ".venv") -WorkingDirectory $backendDeployDir
}

if (-not $SkipInstall) {
    Invoke-External -Executable $uvCmd -Arguments @("sync", "--python", $venvPythonWin) -WorkingDirectory $backendDeployDir
}

$backendStdOut = Join-Path $logDir "backend.out.log"
$backendStdErr = Join-Path $logDir "backend.err.log"
$frontendStdOut = Join-Path $logDir "frontend.out.log"
$frontendStdErr = Join-Path $logDir "frontend.err.log"

$backendProc = $null
$frontendProc = $null

if (-not $SkipBackendRun) {
    Write-Step "Start backend service"
    $backendProc = Start-BackgroundProcess `
        -FilePath $uvCmd `
        -Arguments @(
            "run",
            "--python", $venvPythonWin,
            "python",
            "-m",
            "uvicorn",
            "app.main:app",
            "--host", $config.BackendBindHost,
            "--port", "$($config.BackendPort)"
        ) `
        -WorkingDirectory $backendDeployDir `
        -StdOutFile $backendStdOut `
        -StdErrFile $backendStdErr
}
else {
    Write-Step "Skip backend run"
}

if (-not $SkipFrontendRun) {
    Write-Step "Start frontend static service"
    $frontendProc = Start-BackgroundProcess `
        -FilePath $npxCmd `
        -Arguments @(
            "--yes",
            "serve@14",
            "-s",
            $frontendDeployDir,
            "-l",
            "tcp://$($config.FrontendBindHost):$($config.FrontendPort)"
        ) `
        -WorkingDirectory $frontendDeployDir `
        -StdOutFile $frontendStdOut `
        -StdErrFile $frontendStdErr
}
else {
    Write-Step "Skip frontend run"
}

Write-Step "Done"
Write-Host "Frontend dist: $distDir"
Write-Host "Frontend deployed root: $frontendDeployDir"
Write-Host "Frontend API base URL used in build: $frontendApiBaseUrl"
Write-Host "Backend URL: http://$($config.BackendBindHost):$($config.BackendPort)"
Write-Host "Frontend URL: http://$($config.FrontendBindHost):$($config.FrontendPort)"
Write-Host "CORS_ALLOW_ORIGINS: $corsValue"
Write-Host "Artifacts: $artifactDir"
Write-Host "Logs: $logDir"

if ($backendProc -ne $null) {
    Write-Host "Backend PID: $($backendProc.Id)"
}
if ($frontendProc -ne $null) {
    Write-Host "Frontend PID: $($frontendProc.Id)"
}
