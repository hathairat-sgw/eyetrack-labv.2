param([string]$Python = "python")
$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$env:PYTHONUTF8 = "1"
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw "Install Node.js 22 and reopen VS Code" }
if (!(Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw "npm is missing; repair Node.js installation" }
& $Python -m venv .venv
if ($LASTEXITCODE) { throw "Cannot create Python environment" }
& ".\.venv\Scripts\python.exe" -m pip install -r backend\requirements.txt
if ($LASTEXITCODE) { throw "Python dependency installation failed" }
Push-Location frontend
try { npm.cmd ci; if ($LASTEXITCODE) { throw "npm install failed" } } finally { Pop-Location }

