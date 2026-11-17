$ErrorActionPreference = 'Stop'
Set-Location (Split-Path $PSScriptRoot -Parent)
& node scripts/run.mjs @args
exit $LASTEXITCODE
