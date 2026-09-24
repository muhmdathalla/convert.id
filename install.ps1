# Convert.id — Automated Windows All-in-One Installer
# Usage: iwr -useb https://raw.githubusercontent.com/muhmdathalla/convert.id/main/install.ps1 | iex

$ErrorActionPreference = "Stop"
$ProgressPreference = "SilentlyContinue"

Write-Host ""
Write-Host "   ______                                __     _     __" -ForegroundColor White
Write-Host "  / ____/___  ____ _   _____  _____/ /_   (_)___/ /" -ForegroundColor White
Write-Host " / /   / __ \/ __ \ | / / _ \/ ___/ __/  / / __  / " -ForegroundColor White
Write-Host "/ /___/ /_/ / / / / |/ /  __/ /  / /_   / / /_/ /  " -ForegroundColor White
Write-Host "\____/\____/_/ /_/|___/\___/_/   \__/  /_/\__,_/   " -ForegroundColor White
Write-Host "Convert.id Windows All-in-One Installer" -ForegroundColor DarkGray
Write-Host ""

# 1. Check Python
Write-Host "[1/5] Checking Python runtime..." -ForegroundColor DarkGray
try {
    $pyVersion = & python --version 2>&1
    Write-Host "      Detected $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "Error: Python 3 is required. Please install Python from https://python.org" -ForegroundColor Red
    exit 1
}

# 2. Setup App Home
$InstallDir = "$HOME\.convertid"
$BinDir = "$InstallDir\bin"
$AppDir = "$InstallDir\app"

if (!(Test-Path $InstallDir)) { New-Item -ItemType Directory -Path $InstallDir | Out-Null }
if (!(Test-Path $BinDir)) { New-Item -ItemType Directory -Path $BinDir | Out-Null }

# 3. Clone or Update Repository
Write-Host "[2/5] Fetching Convert.id core system..." -ForegroundColor DarkGray
if (Test-Path "$PSScriptRoot\convert_id") {
    # Local in-tree install
    Write-Host "      Installing from current working copy..." -ForegroundColor DarkGray
    & python -m pip install -e "$PSScriptRoot" --quiet
    Copy-Item -Path "$PSScriptRoot\bin\convert.cmd" -Destination "$BinDir\convert.cmd" -Force
} else {
    if (Test-Path "$AppDir\.git") {
        Write-Host "      Updating repository..." -ForegroundColor DarkGray
        git -C "$AppDir" pull --quiet
    } else {
        Write-Host "      Cloning https://github.com/muhmdathalla/convert.id.git..." -ForegroundColor DarkGray
        git clone https://github.com/muhmdathalla/convert.id.git "$AppDir" --quiet
    }
    & python -m pip install -e "$AppDir" --quiet
    Copy-Item -Path "$AppDir\bin\convert.cmd" -Destination "$BinDir\convert.cmd" -Force
}

# 4. Create alias script convert.cmd
$CmdContent = @"
@echo off
python -m convert_id.cli %*
"@
Set-Content -Path "$BinDir\convert.cmd" -Value $CmdContent -Force
Set-Content -Path "$BinDir\convert-id.cmd" -Value $CmdContent -Force

# 5. Check and Download FFmpeg portable if not present
Write-Host "[3/5] Checking multimedia engine (FFmpeg)..." -ForegroundColor DarkGray
$ffmpegExists = Get-Command "ffmpeg" -ErrorAction SilentlyContinue
if (!$ffmpegExists -and !(Test-Path "$BinDir\ffmpeg.exe")) {
    Write-Host "      Downloading portable FFmpeg essentials..." -ForegroundColor DarkGray
    try {
        $zipUrl = "https://www.gyan.dev/ffmpeg/builds/ffmpeg-release-essentials.zip"
        $zipDest = "$InstallDir\ffmpeg.zip"
        if (Get-Command "curl.exe" -ErrorAction SilentlyContinue) {
            & curl.exe -L -o "$zipDest" "$zipUrl" --progress-bar
        } else {
            (New-Object System.Net.WebClient).DownloadFile($zipUrl, $zipDest)
        }
        Write-Host "      Extracting FFmpeg binaries..." -ForegroundColor DarkGray
        Expand-Archive -Path $zipDest -DestinationPath "$InstallDir\ffmpeg_temp" -Force
        $ffExe = Get-ChildItem -Path "$InstallDir\ffmpeg_temp" -Recurse -Filter "ffmpeg.exe" | Select-Object -First 1
        $fpExe = Get-ChildItem -Path "$InstallDir\ffmpeg_temp" -Recurse -Filter "ffprobe.exe" | Select-Object -First 1
        if ($ffExe) { Move-Item -Path $ffExe.FullName -Destination "$BinDir\ffmpeg.exe" -Force }
        if ($fpExe) { Move-Item -Path $fpExe.FullName -Destination "$BinDir\ffprobe.exe" -Force }
        Remove-Item -Path $zipDest -Force -ErrorAction SilentlyContinue
        Remove-Item -Path "$InstallDir\ffmpeg_temp" -Recurse -Force -ErrorAction SilentlyContinue
        Write-Host "      Portable FFmpeg installed successfully." -ForegroundColor Green
    } catch {
        Write-Host "      Note: FFmpeg auto-download skipped. You can run 'convert doctor --fix' later." -ForegroundColor Yellow
    }
} else {
    Write-Host "      FFmpeg is already available." -ForegroundColor Green
}

# 6. Add to PATH & PowerShell Profile
Write-Host "[4/5] Configuring environment PATH & PowerShell profile..." -ForegroundColor DarkGray
$UserPath = [Environment]::GetEnvironmentVariable("Path", [EnvironmentVariableTarget]::User)
if ($UserPath -notlike "*$BinDir*") {
    [Environment]::SetEnvironmentVariable("Path", "$UserPath;$BinDir", [EnvironmentVariableTarget]::User)
    $env:Path += ";$BinDir"
    Write-Host "      Added $BinDir to User PATH." -ForegroundColor Green
} else {
    Write-Host "      User PATH is already configured." -ForegroundColor Green
}

# Configure PowerShell Profile to override built-in Windows convert.exe (FAT32 converter)
try {
    if (!(Test-Path $PROFILE)) {
        New-Item -Type File -Path $PROFILE -Force | Out-Null
    }
    $ProfileContent = Get-Content $PROFILE -Raw -ErrorAction SilentlyContinue
    $AliasFunc = "`nfunction convert { python -m convert_id.cli @args }`nfunction convert-id { python -m convert_id.cli @args }`n"
    if ($ProfileContent -notlike "*function convert {*") {
        Add-Content -Path $PROFILE -Value $AliasFunc
        Write-Host "      Configured PowerShell alias to override Windows System32 convert.exe." -ForegroundColor Green
    }
} catch {
    # Ignore profile write permission issues
}

# 7. Verification
Write-Host "[5/5] Verifying installation..." -ForegroundColor DarkGray
& python -m convert_id.cli --version

Write-Host ""
Write-Host "========================================================================" -ForegroundColor DarkGray
Write-Host " CONVERT.ID INSTALLED SUCCESSFULLY!" -ForegroundColor White
Write-Host "========================================================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host " Try running:" -ForegroundColor DarkGray
Write-Host "   convert image.jfif png              " -ForegroundColor White -NoNewline; Write-Host "# Convert any image" -ForegroundColor DarkGray
Write-Host "   convert video.mp4 --target-size 24MB" -ForegroundColor White -NoNewline; Write-Host "# Fit exact budget" -ForegroundColor DarkGray
Write-Host "   convert web                         " -ForegroundColor White -NoNewline; Write-Host "# Open Monochromatic Web Workbench" -ForegroundColor DarkGray
Write-Host "   convert doctor                      " -ForegroundColor White -NoNewline; Write-Host "# Run system diagnostics" -ForegroundColor DarkGray
Write-Host ""
