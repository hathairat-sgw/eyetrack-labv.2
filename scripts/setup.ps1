param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
& $Python -m venv .venv
if ($LASTEXITCODE) { throw "Cannot create Python environment" }
& ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if ($LASTEXITCODE) { throw "Python dependency installation failed" }
Push-Location frontend
try { npm.cmd install; if ($LASTEXITCODE) { throw "npm install failed" } } finally { Pop-Location }

