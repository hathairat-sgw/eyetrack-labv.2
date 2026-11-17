param([switch]$Hardware)
$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
Set-Location (Split-Path $PSScriptRoot -Parent)
$envFolder = if ($Hardware) { ".venv-hardware" } else { ".venv" }
$interpreter = Join-Path $envFolder "Scripts\python.exe"
if (!(Test-Path $interpreter)) { throw "Run scripts\setup.ps1 or scripts\setup-hardware.ps1 first" }
& $interpreter -m uvicorn backend.main:app --host 127.0.0.1 --port 8000

