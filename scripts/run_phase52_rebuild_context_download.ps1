$ErrorActionPreference = 'Stop'

$Root = Split-Path -Parent $PSScriptRoot
$OutDir = Join-Path $Root 'data\macro\context\dukascopy_2020'
$TempDir = Join-Path $OutDir '_download'
New-Item -ItemType Directory -Force -Path $TempDir | Out-Null

Write-Host ('=' * 70)
Write-Host 'PHASE 5.2 REBUILD — PRE-2021 CONTEXT DOWNLOAD'
Write-Host ('=' * 70)
Write-Host 'Source      : Dukascopy public historical feed'
Write-Host 'XAUUSD      : 2020-09-01 through 2021-01-05, M1'
Write-Host 'DXY         : 2020-09-01 through 2021-01-05, D1'
Write-Host 'Purpose     : feature warm-up context only'
Write-Host 'Research    : 2021-01-01 onward remains unchanged'
Write-Host ''

if (-not (Get-Command npx -ErrorAction SilentlyContinue)) {
    throw 'npx was not found. Install Node.js/npm first; no Python package installation is required by this script.'
}

Push-Location $TempDir
try {
    Write-Host '[1/2] Downloading XAUUSD M1 context...'
    npx --yes dukascopy-node -i xauusd -from 2020-09-01 -to 2021-01-05 -t m1 -f csv
    if ($LASTEXITCODE -ne 0) { throw "XAUUSD download failed with exit code $LASTEXITCODE" }

    Write-Host '[2/2] Downloading DXY D1 context...'
    npx --yes dukascopy-node -i dollaridxusd -from 2020-09-01 -to 2021-01-05 -t d1 -f csv
    if ($LASTEXITCODE -ne 0) { throw "DXY download failed with exit code $LASTEXITCODE" }
} finally {
    Pop-Location
}

# dukascopy-node writes CSV files under a nested .\download directory.
# Resolve that actual output location explicitly instead of assuming the files
# are written directly into $TempDir.
$DownloadDir = Join-Path $TempDir 'download'
$xau = Get-ChildItem $DownloadDir -Filter 'xauusd-*.csv' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1
$dxy = Get-ChildItem $DownloadDir -Filter 'dollaridxusd-*.csv' -File | Sort-Object LastWriteTime -Descending | Select-Object -First 1

if (-not $xau) { throw "Downloaded XAUUSD CSV was not found under $DownloadDir" }
if (-not $dxy) { throw "Downloaded DXY CSV was not found under $DownloadDir" }

$XauOut = Join-Path $OutDir 'XAUUSD_Dukascopy_M1_2020_context.csv'
$DxyOut = Join-Path $OutDir 'DXY_Dukascopy_D1_2020_context.csv'

Copy-Item $xau.FullName $XauOut -Force
Copy-Item $dxy.FullName $DxyOut -Force

Write-Host ''
Write-Host 'DOWNLOAD COMPLETE — NOT YET SCIENTIFICALLY ACCEPTED'
Write-Host "XAUUSD : $XauOut"
Write-Host "DXY    : $DxyOut"
Write-Host ''
Write-Host 'Next step: run the context continuity/coverage audit before using these files.'
