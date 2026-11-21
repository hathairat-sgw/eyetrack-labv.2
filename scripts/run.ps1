param([switch]$NoOpen,[switch]$Mock,[switch]$Smoke)
$ErrorActionPreference = "Stop"
$taskRoot = Split-Path $PSScriptRoot -Parent
if (!(Get-Command node -ErrorAction SilentlyContinue)) { throw "Install Node.js 22, reopen VS Code, then run Setup-Windows.cmd." }
$taskArgs = @((Join-Path $PSScriptRoot 'run.mjs'))
if ($NoOpen) { $taskArgs += '--no-open' }
if ($Mock) { $taskArgs += '--mock' }
if ($Smoke) { $taskArgs += '--smoke' }
Push-Location $taskRoot
try { & node @taskArgs; if ($LASTEXITCODE) { throw "EyeTrack startup failed. See the service error above; run Setup-Windows.cmd if dependencies are missing." } } finally { Pop-Location }
