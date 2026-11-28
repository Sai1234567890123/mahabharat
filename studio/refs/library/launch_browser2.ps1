# Launches an isolated secondary Chrome instance on debugging port 9223
# for Gemini Pro Account #2 (launched via launch_gemini_agent2.ps1),
# preventing tab collisions with Primary Chrome on port 9222.

param(
    [int]$Port = 9223,
    [string]$StartUrl = "https://www.fab.com"
)

$ProfileDir = "$env:USERPROFILE\.gemini\chrome-profile-2"
if (-not (Test-Path $ProfileDir)) {
    New-Item -ItemType Directory -Path $ProfileDir -Force | Out-Null
}

$ChromePaths = @(
    "$env:ProgramFiles\Google\Chrome\Application\chrome.exe",
    "${env:ProgramFiles(x86)}\Google\Chrome\Application\chrome.exe",
    "$env:LocalAppData\Google\Chrome\Application\chrome.exe"
)
$ChromeExe = $ChromePaths | Where-Object { Test-Path $_ } | Select-Object -First 1

if (-not $ChromeExe) {
    Write-Error "Chrome executable not found in standard locations."
    exit 1
}

Write-Host "Starting isolated Chrome #2 on port $Port (profile: $ProfileDir)..." -ForegroundColor Cyan
Start-Process -FilePath $ChromeExe -ArgumentList @(
    "--remote-debugging-port=$Port",
    "--user-data-dir=`"$ProfileDir`"",
    "--no-first-run",
    $StartUrl
)
Write-Host "Chrome #2 launched. Sign in once if needed, then run Agent #2." -ForegroundColor Green
