# Build TrailPrint3D extension and place the zip in the repo root.
$ErrorActionPreference = "Stop"

$repoRoot = $PSScriptRoot
$sourceDir = Join-Path $repoRoot "TrailPrint3D"

blender --command extension build `
    --source-dir "$sourceDir" `
    --output-dir "$repoRoot"

if ($LASTEXITCODE -ne 0) { Write-Error "Build failed"; exit 1 }

Write-Host "`nBuild output:" -ForegroundColor Green
Get-ChildItem "$repoRoot\TrailPrint3D-*.zip" | Sort-Object LastWriteTime -Descending | Select-Object -First 1
