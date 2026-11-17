$ErrorActionPreference = "Stop"
Set-Location (Split-Path $PSScriptRoot -Parent)
$taskPython = & py -3.10 -c "import sys; print(sys.executable)"
if ($LASTEXITCODE -or !$taskPython) { throw "Install Python 3.10 x64 with Python Launcher first" }
& "$PSScriptRoot/setup.ps1" -Python $taskPython
if ($LASTEXITCODE) { throw "Base setup failed" }
& "$PSScriptRoot/setup-hardware.ps1" -Python310 $taskPython
Write-Host "Installation finished. Open eyetrack-lab.code-workspace and press F5."
