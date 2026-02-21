[CmdletBinding()]
param(
    [switch]$SkipInstall,
    [switch]$RegenerateKeystore,
    [switch]$DryRun,
    [string]$ApiBaseUrl,
    [string]$MobileApiBaseUrl
)

$ErrorActionPreference = "Stop"

$repoRoot = Split-Path -Parent $MyInvocation.MyCommand.Path

$config = [ordered]@{
    FrontendProjectDir      = Join-Path $repoRoot "stream-note-web"
    AndroidProjectDir       = Join-Path $repoRoot "stream-note-web\android"
    ArtifactDir             = Join-Path $repoRoot "artifacts\android"

    # Server API used by mobile app package
    ApiBaseUrl              = "http://121.43.58.58/api/v1"
    MobileApiBaseUrl        = "http://121.43.58.58/api/v1"

    # Local Android toolchain path
    JavaHome                = "C:\Android\jdk-21"
    AndroidSdkRoot          = "C:\Android\Sdk"
    AndroidBuildToolsVersion = "36.0.0"

    # Signing config file (external override)
    SigningConfigFile       = Join-Path $repoRoot "build-android-signing.ps1"
}

if (-not [string]::IsNullOrWhiteSpace($ApiBaseUrl)) {
    $config.ApiBaseUrl = $ApiBaseUrl.Trim()
}
if (-not [string]::IsNullOrWhiteSpace($MobileApiBaseUrl)) {
    $config.MobileApiBaseUrl = $MobileApiBaseUrl.Trim()
}

# Defaults also kept in script for quick fallback.
$androidSigning = @{
    KeystorePath      = Join-Path $config.ArtifactDir "stream-note-release.keystore"
    KeystoreAlias     = "streamnote_release"
    KeystorePassword  = "StreamNote@2026"
    KeyPassword       = "StreamNote@2026"
    DistinguishedName = "CN=Stream Note, OU=Mobile, O=Stream Note, L=Hangzhou, ST=Zhejiang, C=CN"
}

if (Test-Path $config.SigningConfigFile) {
    . $config.SigningConfigFile
    if ($null -ne $AndroidSigningConfig) {
        foreach ($key in $AndroidSigningConfig.Keys) {
            $androidSigning[$key] = $AndroidSigningConfig[$key]
        }
    }
}

function Write-Step([string]$message) {
    Write-Host ""
    Write-Host "==> $message" -ForegroundColor Cyan
}

function Ensure-Directory([string]$path) {
    if ($DryRun) {
        Write-Host "[DryRun] Ensure dir: $path"
        return
    }

    if (-not (Test-Path $path)) {
        New-Item -ItemType Directory -Path $path -Force | Out-Null
    }
}

function Ensure-Command([string]$name) {
    $command = Get-Command $name -ErrorAction SilentlyContinue
    if (-not $command) {
        throw "Command not found: $name"
    }
    return $command.Source
}

function Invoke-External {
    param(
        [Parameter(Mandatory = $true)][string]$Executable,
        [Parameter(Mandatory = $true)][string[]]$Arguments,
        [Parameter(Mandatory = $true)][string]$WorkingDirectory
    )

    $joined = $Arguments -join " "
    Write-Host "$Executable $joined"

    if ($DryRun) {
        return
    }

    Push-Location $WorkingDirectory
    try {
        & $Executable @Arguments
        if ($LASTEXITCODE -ne 0) {
            throw "Command failed ($LASTEXITCODE): $Executable $joined"
        }
    }
    finally {
        Pop-Location
    }
}

function Get-AndroidVersionInfo {
    param(
        [Parameter(Mandatory = $true)][string]$BuildGradlePath
    )

    if (-not (Test-Path $BuildGradlePath)) {
        throw "Android build.gradle not found: $BuildGradlePath"
    }

    $content = Get-Content -Raw -Path $BuildGradlePath
    $versionCodeMatch = [regex]::Match($content, '(?m)^\s*versionCode\s+(\d+)\s*$')
    $versionNameMatch = [regex]::Match($content, '(?m)^\s*versionName\s+"([^"]+)"\s*$')

    if (-not $versionCodeMatch.Success) {
        throw "Cannot parse versionCode from $BuildGradlePath"
    }
    if (-not $versionNameMatch.Success) {
        throw "Cannot parse versionName from $BuildGradlePath"
    }

    return @{
        VersionCode = [int]$versionCodeMatch.Groups[1].Value
        VersionName = $versionNameMatch.Groups[1].Value
        RawContent  = $content
    }
}

function Get-NextVersionName {
    param(
        [Parameter(Mandatory = $true)][string]$CurrentVersionName,
        [Parameter(Mandatory = $true)][int]$NextVersionCode
    )

    if ($CurrentVersionName -match '^\d+(\.\d+)*$') {
        $parts = $CurrentVersionName.Split('.')
        $lastIndex = $parts.Length - 1
        $parts[$lastIndex] = ([int]$parts[$lastIndex] + 1).ToString()
        return ($parts -join '.')
    }

    return "$CurrentVersionName.$NextVersionCode"
}

function Update-AndroidVersionInfo {
    param(
        [Parameter(Mandatory = $true)][string]$BuildGradlePath,
        [Parameter(Mandatory = $true)][int]$NewVersionCode,
        [Parameter(Mandatory = $true)][string]$NewVersionName
    )

    $versionInfo = Get-AndroidVersionInfo -BuildGradlePath $BuildGradlePath
    $updatedContent = [regex]::Replace(
        $versionInfo.RawContent,
        '(?m)^(\s*versionCode\s+)\d+(\s*)$',
        {
            param($match)
            return "$($match.Groups[1].Value)$NewVersionCode$($match.Groups[2].Value)"
        }
    )
    $updatedContent = [regex]::Replace(
        $updatedContent,
        '(?m)^(\s*versionName\s+)"[^"]+"(\s*)$',
        {
            param($match)
            return "$($match.Groups[1].Value)`"$NewVersionName`"$($match.Groups[2].Value)"
        }
    )

    if ($DryRun) {
        Write-Host "[DryRun] Update versionCode: $($versionInfo.VersionCode) -> $NewVersionCode"
        Write-Host "[DryRun] Update versionName: $($versionInfo.VersionName) -> $NewVersionName"
        return @{
            PreviousVersionCode = $versionInfo.VersionCode
            PreviousVersionName = $versionInfo.VersionName
            VersionCode         = $NewVersionCode
            VersionName         = $NewVersionName
        }
    }

    Set-Content -Path $BuildGradlePath -Value $updatedContent -Encoding UTF8
    return @{
        PreviousVersionCode = $versionInfo.VersionCode
        PreviousVersionName = $versionInfo.VersionName
        VersionCode         = $NewVersionCode
        VersionName         = $NewVersionName
    }
}

function Get-VersionToken {
    param(
        [Parameter(Mandatory = $true)][string]$VersionName,
        [Parameter(Mandatory = $true)][int]$VersionCode
    )

    $safeVersionName = $VersionName -replace '[^0-9A-Za-z._-]', '-'
    return "v$safeVersionName-vc$VersionCode"
}

Write-Step "Validate environment"
$npmCmd = Ensure-Command "npm"
$npxCmd = Ensure-Command "npx"

if (-not (Test-Path $config.JavaHome)) {
    throw "JavaHome not found: $($config.JavaHome)"
}
if (-not (Test-Path $config.AndroidSdkRoot)) {
    throw "AndroidSdkRoot not found: $($config.AndroidSdkRoot)"
}
if (-not (Test-Path $config.FrontendProjectDir)) {
    throw "Frontend project dir not found: $($config.FrontendProjectDir)"
}
if (-not (Test-Path $config.AndroidProjectDir)) {
    throw "Android project dir not found: $($config.AndroidProjectDir)"
}

$zipalign = Join-Path $config.AndroidSdkRoot "build-tools\$($config.AndroidBuildToolsVersion)\zipalign.exe"
$apksigner = Join-Path $config.AndroidSdkRoot "build-tools\$($config.AndroidBuildToolsVersion)\apksigner.bat"
$keytool = Join-Path $config.JavaHome "bin\keytool.exe"
$gradlew = Join-Path $config.AndroidProjectDir "gradlew.bat"

if (-not (Test-Path $zipalign)) {
    throw "zipalign not found: $zipalign"
}
if (-not (Test-Path $apksigner)) {
    throw "apksigner not found: $apksigner"
}
if (-not (Test-Path $keytool)) {
    throw "keytool not found: $keytool"
}
if (-not (Test-Path $gradlew)) {
    throw "gradlew not found: $gradlew"
}

Write-Step "Prepare output directories"
Ensure-Directory $config.ArtifactDir

$appBuildGradlePath = Join-Path $config.AndroidProjectDir "app\build.gradle"
Write-Step "Bump Android version (versionCode/versionName)"
$currentVersionInfo = Get-AndroidVersionInfo -BuildGradlePath $appBuildGradlePath
$nextVersionCode = $currentVersionInfo.VersionCode + 1
$nextVersionName = Get-NextVersionName -CurrentVersionName $currentVersionInfo.VersionName -NextVersionCode $nextVersionCode
$versionUpdateResult = Update-AndroidVersionInfo `
    -BuildGradlePath $appBuildGradlePath `
    -NewVersionCode $nextVersionCode `
    -NewVersionName $nextVersionName
$versionToken = Get-VersionToken -VersionName $versionUpdateResult.VersionName -VersionCode $versionUpdateResult.VersionCode
Write-Host "Version bump: code $($versionUpdateResult.PreviousVersionCode) -> $($versionUpdateResult.VersionCode), name $($versionUpdateResult.PreviousVersionName) -> $($versionUpdateResult.VersionName)"

Write-Step "Write android local.properties"
$localPropertiesPath = Join-Path $config.AndroidProjectDir "local.properties"
$escapedSdkPath = $config.AndroidSdkRoot.Replace("\", "\\").Replace(":", "\:")
if ($DryRun) {
    Write-Host "[DryRun] local.properties => sdk.dir=$escapedSdkPath"
}
else {
    Set-Content -Path $localPropertiesPath -Value "sdk.dir=$escapedSdkPath" -Encoding ASCII
}

Write-Step "Prepare release keystore"
if ($RegenerateKeystore -and (Test-Path $androidSigning.KeystorePath) -and (-not $DryRun)) {
    Remove-Item -Force $androidSigning.KeystorePath
}

if (-not (Test-Path $androidSigning.KeystorePath)) {
    Ensure-Directory (Split-Path -Parent $androidSigning.KeystorePath)
    Invoke-External -Executable $keytool -Arguments @(
        "-genkeypair",
        "-v",
        "-keystore", $androidSigning.KeystorePath,
        "-storepass", $androidSigning.KeystorePassword,
        "-keypass", $androidSigning.KeyPassword,
        "-alias", $androidSigning.KeystoreAlias,
        "-keyalg", "RSA",
        "-keysize", "2048",
        "-validity", "36500",
        "-dname", $androidSigning.DistinguishedName
    ) -WorkingDirectory $repoRoot
}

Write-Step "Build frontend and sync Android assets"
if ((-not $SkipInstall) -and (-not (Test-Path (Join-Path $config.FrontendProjectDir "node_modules")))) {
    Invoke-External -Executable $npmCmd -Arguments @("install") -WorkingDirectory $config.FrontendProjectDir
}

$prevJavaHome = $env:JAVA_HOME
$prevAndroidHome = $env:ANDROID_HOME
$prevAndroidSdkRoot = $env:ANDROID_SDK_ROOT
$prevApiBase = $env:VITE_API_BASE_URL
$prevMobileApiBase = $env:VITE_MOBILE_API_BASE_URL
$prevPath = $env:Path

$env:JAVA_HOME = $config.JavaHome
$env:ANDROID_HOME = $config.AndroidSdkRoot
$env:ANDROID_SDK_ROOT = $config.AndroidSdkRoot
$env:VITE_API_BASE_URL = $config.ApiBaseUrl
$env:VITE_MOBILE_API_BASE_URL = $config.MobileApiBaseUrl
$env:Path = "$($config.JavaHome)\bin;$($config.AndroidSdkRoot)\platform-tools;$($config.AndroidSdkRoot)\cmdline-tools\latest\bin;$($config.AndroidSdkRoot)\build-tools\$($config.AndroidBuildToolsVersion);$prevPath"

try {
    Invoke-External -Executable $npmCmd -Arguments @("run", "build") -WorkingDirectory $config.FrontendProjectDir
    Invoke-External -Executable $npxCmd -Arguments @("cap", "sync", "android") -WorkingDirectory $config.FrontendProjectDir

    Write-Step "Build Android release"
    Invoke-External -Executable $gradlew -Arguments @("assembleRelease", "bundleRelease", "--no-daemon") -WorkingDirectory $config.AndroidProjectDir

    Write-Step "Sign release APK"
    $unsignedApk = Join-Path $config.AndroidProjectDir "app\build\outputs\apk\release\app-release-unsigned.apk"
    $releaseAab = Join-Path $config.AndroidProjectDir "app\build\outputs\bundle\release\app-release.aab"
    $alignedApk = Join-Path $config.ArtifactDir "stream-note-$versionToken-release-aligned-unsigned.apk"
    $signedApk = Join-Path $config.ArtifactDir "stream-note-$versionToken-release-signed.apk"
    $signedIdsig = "$signedApk.idsig"
    $versionedAab = Join-Path $config.ArtifactDir "stream-note-$versionToken-release.aab"
    $latestSignedApk = Join-Path $config.ArtifactDir "stream-note-release-signed.apk"
    $latestAab = Join-Path $config.ArtifactDir "stream-note-release.aab"

    if (-not (Test-Path $unsignedApk)) {
        throw "Unsigned APK not found: $unsignedApk"
    }
    if (-not (Test-Path $releaseAab)) {
        throw "Release AAB not found: $releaseAab"
    }

    Invoke-External -Executable $zipalign -Arguments @("-p", "-f", "4", $unsignedApk, $alignedApk) -WorkingDirectory $repoRoot
    Invoke-External -Executable $apksigner -Arguments @(
        "sign",
        "--ks", $androidSigning.KeystorePath,
        "--ks-key-alias", $androidSigning.KeystoreAlias,
        "--ks-pass", "pass:$($androidSigning.KeystorePassword)",
        "--key-pass", "pass:$($androidSigning.KeyPassword)",
        "--out", $signedApk,
        $alignedApk
    ) -WorkingDirectory $repoRoot
    Invoke-External -Executable $apksigner -Arguments @("verify", "--verbose", "--print-certs", $signedApk) -WorkingDirectory $repoRoot

    if (-not $DryRun) {
        Copy-Item -Force $releaseAab $versionedAab
        Copy-Item -Force $releaseAab $latestAab
        Copy-Item -Force $signedApk $latestSignedApk
        $idsigTarget = Join-Path $config.ArtifactDir "stream-note-$versionToken-release-signed.apk.idsig"
        $latestIdsigTarget = Join-Path $config.ArtifactDir "stream-note-release-signed.apk.idsig"
        if ((Test-Path $signedIdsig) -and ($signedIdsig -ne $idsigTarget)) {
            Copy-Item -Force $signedIdsig $idsigTarget
            Copy-Item -Force $signedIdsig $latestIdsigTarget
        }

        $signingInfoPath = Join-Path $config.ArtifactDir "android-release-signing-$versionToken.txt"
        $latestSigningInfoPath = Join-Path $config.ArtifactDir "android-release-signing.txt"
        @(
            "VersionCode=$($versionUpdateResult.VersionCode)",
            "VersionName=$($versionUpdateResult.VersionName)",
            "KeystorePath=$($androidSigning.KeystorePath)",
            "KeystoreAlias=$($androidSigning.KeystoreAlias)",
            "KeystorePassword=$($androidSigning.KeystorePassword)",
            "KeyPassword=$($androidSigning.KeyPassword)",
            "ApiBaseUrl=$($config.ApiBaseUrl)",
            "MobileApiBaseUrl=$($config.MobileApiBaseUrl)"
        ) | Set-Content -Path $signingInfoPath -Encoding UTF8
        Copy-Item -Force $signingInfoPath $latestSigningInfoPath
    }

    Write-Step "Android release completed"
    Write-Host "Version: $($versionUpdateResult.VersionName) (code $($versionUpdateResult.VersionCode))"
    Write-Host "Signed APK: $signedApk"
    Write-Host "Release AAB: $versionedAab"
    Write-Host "Signing info: $(Join-Path $config.ArtifactDir "android-release-signing-$versionToken.txt")"
    Write-Host "Latest alias APK: $(Join-Path $config.ArtifactDir 'stream-note-release-signed.apk')"
}
finally {
    $env:Path = $prevPath

    if ($null -eq $prevJavaHome) {
        Remove-Item Env:JAVA_HOME -ErrorAction SilentlyContinue
    }
    else {
        $env:JAVA_HOME = $prevJavaHome
    }

    if ($null -eq $prevAndroidHome) {
        Remove-Item Env:ANDROID_HOME -ErrorAction SilentlyContinue
    }
    else {
        $env:ANDROID_HOME = $prevAndroidHome
    }

    if ($null -eq $prevAndroidSdkRoot) {
        Remove-Item Env:ANDROID_SDK_ROOT -ErrorAction SilentlyContinue
    }
    else {
        $env:ANDROID_SDK_ROOT = $prevAndroidSdkRoot
    }

    if ($null -eq $prevApiBase) {
        Remove-Item Env:VITE_API_BASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:VITE_API_BASE_URL = $prevApiBase
    }

    if ($null -eq $prevMobileApiBase) {
        Remove-Item Env:VITE_MOBILE_API_BASE_URL -ErrorAction SilentlyContinue
    }
    else {
        $env:VITE_MOBILE_API_BASE_URL = $prevMobileApiBase
    }
}
