# Installs the free studio tools on sai's Windows PC. Nothing here is paid.
# Run in PowerShell:  powershell -ExecutionPolicy Bypass -File studio\setup\install_pc.ps1
# Already on the PC (not touched): Blender 5.2, Unreal Engine 5.8.
$ErrorActionPreference = "Stop"

Write-Host "== Krita (painting key frames, colour script, matte paintings, texture repaint)"
winget install --id KDE.Krita -e --accept-source-agreements --accept-package-agreements

Write-Host "== FFmpeg (cutting, sound mux, previews)"
winget install --id Gyan.FFmpeg -e --accept-source-agreements --accept-package-agreements

Write-Host "== Java 21 runtime (needed by the SheepIt render farm client)"
winget install --id EclipseAdoptium.Temurin.21.JRE -e --accept-source-agreements --accept-package-agreements

$tools = Join-Path $env:USERPROFILE "studio-tools"
New-Item -ItemType Directory -Force -Path $tools | Out-Null

Write-Host "== Rhubarb Lip Sync 1.14.0 (mouth shapes from sai's recorded lines)"
$zip = Join-Path $tools "rhubarb.zip"
Invoke-WebRequest -Uri "https://github.com/DanielSWolf/rhubarb-lip-sync/releases/download/v1.14.0/Rhubarb-Lip-Sync-1.14.0-Windows.zip" -OutFile $zip
Expand-Archive -Force $zip -DestinationPath $tools
Remove-Item $zip

Write-Host "== SheepIt client (free render farm): opens the download page. Sign up free, save the client into $tools."
Start-Process "https://www.sheepit-renderfarm.com/getstarted"

Write-Host "Done. Tools are in $tools"
Write-Host "SheepIt needs a free account and 8 GB RAM with 2 GB free; run it only when Unreal and Blender are closed."
